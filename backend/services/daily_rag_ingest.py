"""
Store the Daily operations workflows in RAG so the concierge can answer
questions about them and build on those answers in conversation.

Why this exists: the Daily page's task cards (one card per task, in
frontend/src/components/ServiceDaily.js) are UI copy. The concierge could
not see them, so a question like "how do I book a room?" had no seeded
answer to build on. This module is the bridge, in two parts:

1. A canonical text source, backend/knowledge_base/daily_workflows/
   daily_workflows.txt, mirroring the UI cards task for task. A test
   asserts the UI card titles and the document task titles stay in sync,
   so the two cannot drift silently.
2. Ingest into Chroma (via RAGManager) with a hash guard: unchanged
   content is never re-ingested, so re-running the seed does not stack
   duplicate vectors. When Chroma is down, ingest soft-fails and the
   keyword search below still answers, because the concierge checks it
   before falling back to Chroma.

Generic only: this document carries no client name, brand, address, phone,
or website, and no pricing presented as a real business's confirmed rates.
Demo only: no payments, no real reservations.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_STATE_FILE = "daily_workflows_state.json"

_STOPWORDS = {
    "the", "and", "for", "what", "how", "are", "with", "from", "this", "that",
    "can", "does", "about", "tell", "show", "find", "search", "look", "explain",
    "describe", "please", "want", "need", "help", "get", "into", "your", "you",
    "does", "do", "is", "it", "a", "an", "of", "to", "in", "on", "me", "my",
}

# Tokens that alone identify a Daily task (vs. an SBA loan question).
_DISTINCTIVE = {
    "booking", "book", "room", "rooms", "recording", "repair", "rental",
    "rentals", "retail", "event", "events", "jam", "schedule", "scheduling",
    "deposit", "quote", "intake", "gear", "studio", "rehearsal", "session",
}


def kb_path() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[1] / "knowledge_base" / "daily_workflows" / "daily_workflows.txt",
        Path("./backend/knowledge_base/daily_workflows/daily_workflows.txt"),
        Path("/app/backend/knowledge_base/daily_workflows/daily_workflows.txt"),
    ]
    for c in candidates:
        if c.is_file():
            return c
    return candidates[0]


def _live_dir() -> Path:
    try:
        from backend.services.sba_rag_ingest import _kb_live_dir

        return _kb_live_dir()
    except Exception:
        p = Path("backend/knowledge_base/sba_api_live")
        p.mkdir(parents=True, exist_ok=True)
        return p


def parse_tasks(text: str) -> List[Dict[str, str]]:
    """Split the KB document into one dict per '## Task:' section."""
    tasks: List[Dict[str, str]] = []
    current: Optional[Dict[str, str]] = None
    for line in (text or "").splitlines():
        if line.startswith("## Task:"):
            if current:
                tasks.append(current)
            current = {"title": line[len("## Task:"):].strip(), "body": line.strip()}
            continue
        if current is not None:
            current["body"] += "\n" + line
    if current:
        tasks.append(current)
    for task in tasks:
        # Headings are "## Task: <title> — <service>"; keep the UI card
        # title clean and take the service from the heading suffix.
        service = ""
        m = re.match(r"^(.*) — ([^—]+)$", task["title"])
        if m:
            task["title"] = m.group(1).strip()
            service = m.group(2).strip()
        if not service:
            m = re.search(r"Service:\s*([^\.\n]+)", task["body"])
            if m:
                service = m.group(1).strip()
        task["service"] = service
        task["body"] = task["body"].strip()
    return tasks


def load_tasks() -> List[Dict[str, str]]:
    path = kb_path()
    if not path.is_file():
        return []
    try:
        return parse_tasks(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:
        logger.warning("daily workflows KB read failed: %s", e)
        return []


def _tokens(question: str) -> List[str]:
    q = re.sub(r"[^a-z0-9\s]", " ", (question or "").lower())
    return [t for t in re.findall(r"[a-z0-9]{3,}", q) if t not in _STOPWORDS]


def search_daily_workflows(question: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """Keyword search over Daily tasks only. Returns [] unless the match is strong.

    A task scores on distinctive Daily tokens in its title/body. Growth
    tasks additionally require a growth/expansion token, so a plain SBA
    loan question never surfaces growth scope unasked.
    """
    tokens = _tokens(question)
    if not tokens:
        return []
    token_set = set(tokens)

    def _matches(token: str, words) -> bool:
        # "book" must also match "booking"/"booked" in titles and bodies,
        # or a room-booking question loses to "Book a recording session"
        # on the exact title word alone.
        if token in words:
            return True
        if token == "book":
            return any(w.startswith("book") for w in words)
        return False

    scored = []
    for task in load_tasks():
        body = task["body"].lower()
        words = set(re.findall(r"[a-z0-9]+", body))
        matched = {t for t in tokens if _matches(t, words)}
        # Title matches count double: the task name is the strongest signal.
        title_words = set(re.findall(r"[a-z0-9]+", task["title"].lower()))
        title_matched = {t for t in tokens if _matches(t, title_words)}
        if task.get("service") == "Growth" and not token_set.intersection({"growth", "expansion", "expand"}):
            continue
        if not matched.intersection(_DISTINCTIVE) and len(matched) < 2:
            continue
        if len(matched) < 1:
            continue
        score = len(matched) + 2 * len(title_matched)
        scored.append((score, task))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {"score": score, "title": t["title"], "service": t.get("service", ""), "body": t["body"]}
        for score, t in scored[:max_results]
    ]


def ingest_daily_workflows(*, force: bool = False) -> Dict[str, Any]:
    """Seed Daily tasks into Chroma. Hash-guarded, soft-fail, never raises."""
    tasks = load_tasks()
    if not tasks:
        return {"ok": False, "reason": "no_tasks", "added": 0}
    blob = "\n\n".join(t["body"] for t in tasks).encode("utf-8")
    digest = hashlib.sha256(blob).hexdigest()
    state_path = _live_dir() / _STATE_FILE
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        state = {}
    if not force and state.get("hash") == digest:
        return {"ok": True, "skipped": True, "reason": "unchanged", "tasks": len(tasks), "added": 0}
    try:
        from backend.services.rag import get_rag_manager
    except Exception as e:
        return {"ok": False, "reason": f"import: {e}", "added": 0}
    rag = get_rag_manager()
    if not rag or not rag.is_available():
        return {"ok": False, "reason": "chroma_unavailable", "added": 0}
    added = errors = 0
    for task in tasks:
        meta = {
            "source": "daily_workflows",
            "kind": "daily_task",
            "service": task.get("service", ""),
            "title": task["title"][:200],
            "is_current": True,
            "demo_only": True,
        }
        try:
            result = rag.add_document(task["body"], meta)
            if isinstance(result, dict) and result.get("error"):
                errors += 1
            else:
                added += 1
        except Exception:
            errors += 1
    if added:
        try:
            state_path.write_text(
                json.dumps({"hash": digest, "tasks": len(tasks), "added": added}, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning("daily workflows state save failed: %s", e)
    return {"ok": added > 0, "tasks": len(tasks), "added": added, "errors": errors}


def ingest_status() -> Dict[str, Any]:
    state_path = _live_dir() / _STATE_FILE
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        state = {}
    return {
        "kb_path": str(kb_path()),
        "tasks": len(load_tasks()),
        "ingested_hash": state.get("hash"),
        "ingested_tasks": state.get("tasks"),
    }
