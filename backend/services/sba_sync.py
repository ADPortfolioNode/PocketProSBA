"""
Keep stored SBA content current — the industry-standard pattern for a
read-mostly public feed:

1. **Source of truth stays upstream.** The app never invents program
   facts; it re-fetches the official sba.gov content feed/API.
2. **Change detection, not blind rewrites.** Each fetched route is
   hashed; only changed routes are re-ingested. Unchanged routes are
   left alone, failed routes keep their last-good copy, and nothing is
   ever blanked on a failed fetch (stale-while-revalidate / soft-degrade,
   per the app standard).
3. **Replace, don't append.** Re-ingested documents use stable ids, so
   a refreshed route replaces its old vector instead of stacking a
   fresh copy next to a stale one.
4. **Three triggers, one code path:**
   - on-connect: a background refresh at app startup when the last sync
     is older than ``SBA_SYNC_MAX_AGE_HOURS`` (default 24h);
   - daily quiet: a scheduler thread that runs once a day at
     ``SBA_SYNC_HOUR_UTC`` (default 03:00 UTC) — logs only, no user
     disruption;
   - manual: ``python -m backend.services.sba_sync`` (cron-friendly)
     or POST /api/sba/sync (token-gated, see routes/sba.py).
5. **Single writer.** A lock file in the live KB directory means that
   even with several web workers, only one sync runs at a time; the
   others skip quietly.
6. **Static guides are out of scope.** Hand-written reference guides
   (rates, fees, eligibility) are human-reviewed content, not feed
   content. The sync refreshes feed-derived routes only; it never
   rewrites a static guide. Those guides carry their own review date
   and must not be presented as "current" until reviewed (see the
   SOP 50 10 8.1 audit draft).

Environment:
  SBA_DAILY_SYNC_ENABLED  "1" (default) / "0" — in-app daily scheduler
  SBA_SYNC_HOUR_UTC       hour of day in UTC for the daily run (default 3)
  SBA_SYNC_MAX_AGE_HOURS  on-connect refresh threshold (default 24)
  SBA_SYNC_TOKEN          token required for POST /api/sba/sync; when
                          unset, that endpoint refuses (see routes/sba.py)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Core routes only: a small, polite daily set. The full feed is still
# available on demand through Browse/Chat, which soft-ingest per route.
CORE_ROUTES = [
    "/api/sba/content/loans",
    "/api/sba/content/loans/7a",
    "/api/sba/content/loans/504",
    "/api/sba/content/loans/microloans",
    "/api/sba/content/articles",
]

_STATE_FILE = "sync_state.json"
_LOCK_FILE = "sync.lock"
_scheduler_started = False
_scheduler_lock = threading.Lock()


def _live_dir() -> Path:
    """Shared directory for live KB files + sync state (tests override it)."""
    try:
        from backend.services.sba_rag_ingest import _kb_live_dir

        return _kb_live_dir()
    except Exception:
        p = Path("backend/knowledge_base/sba_api_live")
        p.mkdir(parents=True, exist_ok=True)
        return p


def _state_path() -> Path:
    return _live_dir() / _STATE_FILE


def load_state() -> Dict[str, Any]:
    try:
        data = json.loads(_state_path().read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {"version": 1, "routes": {}}


def save_state(state: Dict[str, Any]) -> None:
    path = _state_path()
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def canonical_hash(envelope: Dict[str, Any]) -> str:
    """Stable hash of a fetched payload, independent of key order."""
    payload = {
        "items": envelope.get("items") or envelope.get("results") or [],
        "topic": envelope.get("topic") or {},
        "title": envelope.get("title") or "",
    }
    blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def seconds_until_next_run(now: datetime, hour_utc: int) -> float:
    """Seconds from ``now`` (aware UTC) until the next run at hour_utc."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    target = now.replace(hour=hour_utc, minute=0, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def _default_fetcher(route: str) -> Dict[str, Any]:
    """Fetch one core route fresh from the official feed (no cache)."""
    from backend.services.SBA_Content import SBAContentAPI

    api = SBAContentAPI()
    if route == "/api/sba/content/loans":
        env = api.search_loans(query="", page=1, fresh=True)
    elif route.startswith("/api/sba/content/loans/"):
        env = api.get_loan_program(route.rsplit("/", 1)[-1], force_fresh=True)
    elif route == "/api/sba/content/articles":
        env = api.search_articles(query="", page=1, fresh=True)
    else:
        raise ValueError(f"no fetcher for route {route}")
    if not isinstance(env, dict):
        raise ValueError(f"fetcher for {route} did not return a dict")
    env.setdefault("path", route)
    return env


def _acquire_lock() -> Optional[Path]:
    """Single-writer lock; returns the lock path, or None if held."""
    path = _live_dir() / _LOCK_FILE
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode("utf-8"))
        os.close(fd)
        return path
    except FileExistsError:
        try:
            age = time.time() - path.stat().st_mtime
            if age > 2 * 3600:  # stale lock from a crashed run: clear it
                path.unlink()
                return _acquire_lock()
        except Exception:
            pass
        return None
    except Exception as e:
        logger.warning("sba sync lock unavailable: %s", e)
        return None


def _release_lock(path: Optional[Path]) -> None:
    if path is not None:
        try:
            path.unlink()
        except Exception:
            pass


def run_sync(
    *,
    fetcher: Optional[Callable[[str], Dict[str, Any]]] = None,
    routes: Optional[List[str]] = None,
    force: bool = False,
    ingest: bool = True,
) -> Dict[str, Any]:
    """Fetch core routes, re-ingest only the changed ones.

    Returns a summary; never raises, and never blanks stored content on
    failure — failed routes keep their last-good copy and are recorded.
    """
    fetch = fetcher or _default_fetcher
    wanted = list(routes or CORE_ROUTES)
    state = load_state()
    state.setdefault("routes", {})
    checked = changed = unchanged = failed = 0
    details: Dict[str, str] = {}
    started = datetime.now(timezone.utc).isoformat()

    for route in wanted:
        checked += 1
        try:
            envelope = fetch(route)
        except Exception as e:
            failed += 1
            details[route] = f"failed: {e}"
            logger.warning("sba sync fetch failed route=%s: %s", route, e)
            continue
        if not isinstance(envelope, dict) or envelope.get("error"):
            if not (envelope.get("items") or envelope.get("results") or envelope.get("topic")):
                failed += 1
                details[route] = "failed: empty/error envelope"
                continue
        digest = canonical_hash(envelope)
        prev = state["routes"].get(route, {})
        if not force and prev.get("hash") == digest:
            unchanged += 1
            details[route] = "unchanged"
            prev["last_checked"] = started
            continue
        if ingest:
            try:
                from backend.services.sba_rag_ingest import ingest_sba_envelope

                title = ""
                topic = envelope.get("topic")
                if isinstance(topic, dict):
                    title = topic.get("title") or ""
                ingest_sba_envelope(envelope, route=route, title=title, force=True)
            except Exception as e:
                failed += 1
                details[route] = f"ingest failed: {e}"
                logger.warning("sba sync ingest failed route=%s: %s", route, e)
                continue
        changed += 1
        details[route] = "changed"
        state["routes"][route] = {
            "hash": digest,
            "fetched_at": started,
            "last_checked": started,
            "status": "changed",
        }

    state["last_sync"] = started
    state["last_summary"] = {
        "checked": checked,
        "changed": changed,
        "unchanged": unchanged,
        "failed": failed,
    }
    try:
        save_state(state)
    except Exception as e:
        logger.warning("sba sync state save failed: %s", e)

    summary = {
        "started": started,
        "checked": checked,
        "changed": changed,
        "unchanged": unchanged,
        "failed": failed,
        "routes": details,
    }
    logger.info("sba sync done: %s", summary)
    return summary


def sync_status() -> Dict[str, Any]:
    """Public operational status: ages, counts, next run. No secrets."""
    state = load_state()
    hour = int(os.getenv("SBA_SYNC_HOUR_UTC", "3") or 3)
    now = datetime.now(timezone.utc)
    routes = {}
    for route, info in (state.get("routes") or {}).items():
        routes[route] = {
            "fetched_at": info.get("fetched_at"),
            "last_checked": info.get("last_checked"),
            "status": info.get("status"),
        }
    return {
        "last_sync": state.get("last_sync"),
        "last_summary": state.get("last_summary"),
        "routes": routes,
        "next_daily_run_utc": (
            now + timedelta(seconds=seconds_until_next_run(now, hour))
        ).isoformat(),
        "daily_hour_utc": hour,
        "scheduler_enabled": os.getenv("SBA_DAILY_SYNC_ENABLED", "1") != "0",
    }


def _scheduler_loop() -> None:
    hour = int(os.getenv("SBA_SYNC_HOUR_UTC", "3") or 3)
    max_age = float(os.getenv("SBA_SYNC_MAX_AGE_HOURS", "24") or 24)
    # On-connect refresh: if the last sync is stale, run once now.
    try:
        state = load_state()
        last = state.get("last_sync")
        stale = True
        if last:
            try:
                age = datetime.now(timezone.utc) - datetime.fromisoformat(last)
                stale = age.total_seconds() > max_age * 3600
            except Exception:
                stale = True
        if stale:
            lock = _acquire_lock()
            if lock is not None:
                try:
                    run_sync()
                finally:
                    _release_lock(lock)
    except Exception as e:
        logger.warning("sba on-connect sync soft-fail: %s", e)
    # Daily quiet run, forever (daemon thread; never blocks requests).
    while True:
        try:
            wait = seconds_until_next_run(datetime.now(timezone.utc), hour)
            # Sleep in chunks so a process shutdown is not held up long.
            while wait > 0:
                step = min(wait, 300)
                time.sleep(step)
                wait -= step
            lock = _acquire_lock()
            if lock is not None:
                try:
                    run_sync()
                finally:
                    _release_lock(lock)
        except Exception as e:
            logger.warning("sba daily sync soft-fail: %s", e)
            time.sleep(3600)


def start_scheduler() -> bool:
    """Start the on-connect + daily scheduler once per process."""
    global _scheduler_started
    if os.getenv("SBA_DAILY_SYNC_ENABLED", "1") == "0":
        return False
    with _scheduler_lock:
        if _scheduler_started:
            return False
        _scheduler_started = True
    try:
        t = threading.Thread(target=_scheduler_loop, name="sba-daily-sync", daemon=True)
        t.start()
        logger.info("sba daily sync scheduler started")
        return True
    except Exception as e:
        logger.warning("sba sync scheduler start failed: %s", e)
        return False


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Quiet daily SBA content sync")
    parser.add_argument("--force", action="store_true", help="re-ingest even if unchanged")
    parser.add_argument("--routes", nargs="*", default=None, help="subset of core routes")
    parser.add_argument("--no-ingest", action="store_true", help="check hashes only")
    args = parser.parse_args(argv)
    summary = run_sync(force=args.force, routes=args.routes, ingest=not args.no_ingest)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
