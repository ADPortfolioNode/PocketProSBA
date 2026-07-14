"""
Ingest SBA API endpoint responses into the RAG process.

When parent/child explore routes return payload envelopes, we:
  1. Flatten topic + child items into text documents
  2. Persist under knowledge_base/sba_api_live/ (keyword RAG even without Gemini)
  3. Soft-add chunks to Chroma via RAGManager when available

Never raises to callers — always soft-degrade.
"""

from __future__ import annotations

import hashlib
import logging
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Throttle re-ingest of same route (seconds)
_MIN_REINGEST_SECONDS = 45
_last_ingest: Dict[str, float] = {}
_lock = threading.Lock()


def _kb_live_dir() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[1] / "knowledge_base" / "sba_api_live",  # backend/knowledge_base/sba_api_live
        Path("/app/backend/knowledge_base/sba_api_live"),
        Path("./backend/knowledge_base/sba_api_live"),
    ]
    for c in candidates:
        try:
            c.mkdir(parents=True, exist_ok=True)
            return c
        except Exception:
            continue
    # Last resort: cwd
    p = Path("knowledge_base/sba_api_live")
    p.mkdir(parents=True, exist_ok=True)
    return p


def _safe_slug(route: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", (route or "sba").strip("/"))
    s = re.sub(r"_+", "_", s).strip("_").lower()
    return (s or "sba")[:120]


def _strip_html(text: str) -> str:
    t = re.sub(r"<[^>]+>", " ", text or "")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _item_to_text(item: dict) -> str:
    title = item.get("title") or item.get("name") or "SBA resource"
    lines = [
        f"# {title}",
        f"Type: {item.get('type') or 'content'}",
    ]
    if item.get("path"):
        lines.append(f"API path: {item.get('path')}")
    if item.get("parent_path"):
        lines.append(f"Parent path: {item.get('parent_path')}")
    if item.get("id") is not None:
        lines.append(f"ID: {item.get('id')}")
    desc = _strip_html(
        str(item.get("description") or item.get("summary") or item.get("body") or "")
    )
    if desc:
        lines.append("")
        lines.append(desc)
    if item.get("url") or item.get("link"):
        lines.append("")
        lines.append(f"Official URL: {item.get('url') or item.get('link')}")
    if item.get("fileUrl") or item.get("file_url"):
        lines.append(f"File / form URL: {item.get('fileUrl') or item.get('file_url')}")
    if item.get("registrationLink") or item.get("registration_link"):
        lines.append(
            f"Registration URL: {item.get('registrationLink') or item.get('registration_link')}"
        )
    # Capture API actions so chat can surface them later
    for act in item.get("actions") or []:
        if not isinstance(act, dict):
            continue
        href = act.get("href") or act.get("path") or act.get("url") or ""
        label = act.get("label") or act.get("id") or "Action"
        if href:
            lines.append(f"Action: {label} -> {href}")
    meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
    for key in (
        "max_amount",
        "terms",
        "rates",
        "use_cases",
        "program",
        "agency",
        "location",
        "phone",
        "email",
    ):
        val = item.get(key) if item.get(key) is not None else meta.get(key)
        if val is not None and val != "":
            if isinstance(val, list):
                val = ", ".join(str(v) for v in val)
            lines.append(f"{key.replace('_', ' ').title()}: {val}")
    return "\n".join(lines).strip()


def envelope_to_documents(
    envelope: dict, route: str = "", title: str = ""
) -> List[Tuple[str, Dict[str, Any]]]:
    """Turn an SBA API envelope into (text, metadata) chunks for RAG."""
    if not isinstance(envelope, dict):
        return []

    route = str(route or envelope.get("path") or "").strip()
    topic = envelope.get("topic") if isinstance(envelope.get("topic"), dict) else {}
    topic_title = (
        title
        or topic.get("title")
        or envelope.get("title")
        or envelope.get("name")
        or route
        or "SBA API topic"
    )
    docs: List[Tuple[str, Dict[str, Any]]] = []

    # Topic-level document
    parts = [
        f"# {topic_title}",
        f"Source: SBA API endpoint response",
        f"API route: {route or '(unknown)'}",
    ]
    if topic.get("description") or envelope.get("description") or envelope.get("message"):
        parts.append("")
        parts.append(
            _strip_html(
                str(
                    topic.get("description")
                    or envelope.get("description")
                    or envelope.get("message")
                    or ""
                )
            )
        )
    if topic.get("official_url") or envelope.get("url"):
        parts.append("")
        parts.append(f"Official URL: {topic.get('official_url') or envelope.get('url')}")
    for sec in topic.get("sections") or []:
        if not isinstance(sec, dict):
            continue
        st = sec.get("title") or "Section"
        body = _strip_html(str(sec.get("body") or ""))
        if body:
            parts.append("")
            parts.append(f"## {st}")
            parts.append(body)
    overview_text = "\n".join(parts).strip()
    if len(overview_text) > 40:
        docs.append(
            (
                overview_text,
                {
                    "source": "sba_api",
                    "kind": "topic_overview",
                    "route": route,
                    "title": str(topic_title)[:200],
                    "is_current": bool(envelope.get("is_current", True)),
                },
            )
        )

    # Per-child item documents (the main RAG fuel when drilling children)
    items = envelope.get("items") or envelope.get("results") or []
    if not isinstance(items, list):
        items = []
    for i, raw in enumerate(items):
        if not isinstance(raw, dict):
            continue
        text = _item_to_text(raw)
        if len(text) < 20:
            continue
        child_path = str(raw.get("path") or "")
        docs.append(
            (
                text,
                {
                    "source": "sba_api",
                    "kind": "child_item",
                    "route": route,
                    "child_path": child_path,
                    "item_id": str(raw.get("id") if raw.get("id") is not None else i),
                    "title": str(raw.get("title") or raw.get("name") or "")[:200],
                    "type": str(raw.get("type") or "content")[:80],
                    "url": str(raw.get("url") or raw.get("link") or "")[:500],
                    "is_current": bool(
                        raw.get("is_current")
                        if raw.get("is_current") is not None
                        else envelope.get("is_current", True)
                    ),
                },
            )
        )

    # Combined dump (single file friendly for keyword scan)
    if docs:
        combined = (
            f"# Combined SBA API digest for {route or topic_title}\n"
            f"Retrieved children: {len(items)}\n"
            f"Chunks: {len(docs)}\n\n"
            + "\n\n---\n\n".join(t for t, _ in docs)
        )
        docs.insert(
            0,
            (
                combined[:50000],
                {
                    "source": "sba_api",
                    "kind": "combined",
                    "route": route,
                    "title": str(topic_title)[:200],
                    "child_count": len(items),
                },
            ),
        )
    return docs


def _write_kb_files(
    route: str, docs: List[Tuple[str, Dict[str, Any]]]
) -> Dict[str, Any]:
    """Persist combined + overview under knowledge_base/sba_api_live/."""
    live = _kb_live_dir()
    slug = _safe_slug(route or "sba")
    written = []
    # Prefer combined + first overview
    by_kind = {}
    for text, meta in docs:
        kind = (meta or {}).get("kind") or "chunk"
        by_kind.setdefault(kind, []).append((text, meta))

    if by_kind.get("combined"):
        path = live / f"{slug}__combined.txt"
        path.write_text(by_kind["combined"][0][0], encoding="utf-8")
        written.append(str(path))

    if by_kind.get("topic_overview"):
        path = live / f"{slug}__overview.txt"
        path.write_text(by_kind["topic_overview"][0][0], encoding="utf-8")
        written.append(str(path))

    # Individual children (cap to keep disk light)
    children = by_kind.get("child_item") or []
    for text, meta in children[:40]:
        cid = _safe_slug(str(meta.get("item_id") or meta.get("title") or "item"))
        path = live / f"{slug}__child_{cid}.txt"
        path.write_text(text, encoding="utf-8")
        written.append(str(path))

    # Manifest for debugging / chat sources
    manifest = live / f"{slug}__manifest.txt"
    lines = [
        f"route={route}",
        f"chunks={len(docs)}",
        f"files={len(written)}",
        f"updated={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
    ]
    for w in written:
        lines.append(w)
    manifest.write_text("\n".join(lines), encoding="utf-8")
    written.append(str(manifest))
    return {"dir": str(live), "files": written, "count": len(written)}


def _ingest_chroma(docs: List[Tuple[str, Dict[str, Any]]], route: str) -> Dict[str, Any]:
    """Soft-add documents to Chroma via RAGManager."""
    try:
        from backend.services.rag import get_rag_manager
    except Exception as e:
        return {"ok": False, "reason": f"import: {e}", "added": 0}

    rag = get_rag_manager()
    if not rag or not rag.is_available():
        return {"ok": False, "reason": "chroma_unavailable", "added": 0}

    added = 0
    errors = 0
    # Skip giant combined for vector store (duplicate content); keep overview + children
    for text, meta in docs:
        if (meta or {}).get("kind") == "combined":
            continue
        # Cap chunk size for chroma
        chunk = text[:8000]
        m = {k: v for k, v in (meta or {}).items() if isinstance(v, (str, int, float, bool))}
        m["ingested_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        # Stable-ish id in metadata for debugging
        m["doc_hash"] = hashlib.sha1(
            f"{route}|{m.get('kind')}|{m.get('item_id')}|{chunk[:120]}".encode("utf-8")
        ).hexdigest()[:16]
        try:
            result = rag.add_document(chunk, m)
            if isinstance(result, dict) and result.get("error"):
                errors += 1
            else:
                added += 1
        except Exception:
            errors += 1
    return {"ok": added > 0, "added": added, "errors": errors}


def ingest_sba_envelope(
    envelope: dict,
    route: str = "",
    title: str = "",
    *,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Ingest one SBA API response into RAG (KB files + optional Chroma).
    Safe to call on every parent/child fetch.
    """
    route = str(route or (envelope or {}).get("path") or "").strip()
    if not route or not isinstance(envelope, dict):
        return {"ok": False, "reason": "empty"}

    # Skip empty error envelopes
    items = envelope.get("items") or envelope.get("results") or []
    if not items and not (envelope.get("topic") or {}).get("description"):
        if envelope.get("error") or envelope.get("degraded") and not items:
            return {"ok": False, "reason": "no_content"}

    now = time.time()
    with _lock:
        last = _last_ingest.get(route, 0)
        if not force and (now - last) < _MIN_REINGEST_SECONDS:
            return {
                "ok": True,
                "skipped": True,
                "reason": "throttled",
                "route": route,
                "age_s": int(now - last),
            }
        _last_ingest[route] = now

    try:
        docs = envelope_to_documents(envelope, route=route, title=title)
        if not docs:
            return {"ok": False, "reason": "no_docs", "route": route}

        kb = _write_kb_files(route, docs)
        chroma = _ingest_chroma(docs, route)
        logger.info(
            "SBA→RAG ingest route=%s docs=%s kb_files=%s chroma_added=%s",
            route,
            len(docs),
            kb.get("count"),
            chroma.get("added"),
        )
        return {
            "ok": True,
            "route": route,
            "docs": len(docs),
            "kb": kb,
            "chroma": chroma,
            "mode": "kb+chroma" if chroma.get("ok") else "kb_only",
        }
    except Exception as e:
        logger.warning("SBA→RAG ingest soft-fail route=%s: %s", route, e)
        return {"ok": False, "reason": str(e), "route": route}


def schedule_sba_rag_ingest(
    envelope: dict, route: str = "", title: str = "", *, force: bool = False
) -> None:
    """Fire-and-forget ingest so API latency is not blocked on Chroma."""

    def _run():
        try:
            ingest_sba_envelope(envelope, route=route, title=title, force=force)
        except Exception as e:
            logger.warning("async SBA→RAG ingest failed: %s", e)

    try:
        t = threading.Thread(target=_run, name=f"sba-rag-{_safe_slug(route)[:40]}", daemon=True)
        t.start()
    except Exception as e:
        logger.warning("could not schedule SBA→RAG ingest: %s", e)
        # Sync fallback (still soft)
        try:
            ingest_sba_envelope(envelope, route=route, title=title, force=force)
        except Exception:
            pass


def ingest_status() -> Dict[str, Any]:
    live = _kb_live_dir()
    files = list(live.glob("*.txt")) if live.exists() else []
    return {
        "live_dir": str(live),
        "file_count": len(files),
        "routes_cached": len(_last_ingest),
        "recent_routes": sorted(_last_ingest.keys())[-20:],
    }
