"""
Turn raw RAG / Chroma hits into human-readable chat answers with clickable links.

Avoids dumping metadata dumps like:
  Source 1: sba_api
  Type: loan_program API path: /api/...
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _strip_meta_noise(text: str) -> str:
    """Remove raw metadata lines that read poorly in chat."""
    if not text:
        return ""
    # Inline meta noise (often concatenated on one line)
    text = re.sub(
        r"\b(?:Type|API path|API route|Parent path|ID|kind|route|child_path|item_id|Retrieved children|Chunks)\s*:\s*\S+",
        " ",
        str(text),
        flags=re.I,
    )
    text = re.sub(r"\bSource\s*:\s*(?:sba_api|SBA API endpoint response)\b", " ", text, flags=re.I)
    lines = []
    for line in text.replace("\r\n", "\n").split("\n"):
        t = line.strip()
        if not t:
            if lines and lines[-1] != "":
                lines.append("")
            continue
        # Drop pure meta labels
        if re.match(
            r"^(Type|API path|Parent path|ID|Source|kind|route|child_path|item_id|Retrieved children|Chunks)\s*:",
            t,
            re.I,
        ):
            continue
        if re.match(r"^Source:\s*SBA API", t, re.I):
            continue
        if t.startswith("# Combined SBA API digest"):
            continue
        if t.startswith("Source: SBA API endpoint"):
            continue
        # Drop leftover "Source N: sba_api" style headers
        if re.match(r"^Source\s+\d+\s*:\s*sba_api\s*$", t, re.I):
            continue
        lines.append(t)
    # Collapse excess blanks
    out = []
    for ln in lines:
        if ln == "" and out and out[-1] == "":
            continue
        out.append(ln)
    return re.sub(r"[ \t]{2,}", " ", "\n".join(out)).strip()


def _title_from_meta(meta: dict, content: str) -> str:
    title = (
        meta.get("title")
        or meta.get("name")
        or meta.get("label")
        or ""
    )
    title = _clean(str(title))
    looks_like_file = bool(
        re.search(r"api_sba_|__combined|__overview|__child_|\.txt$", title, re.I)
    ) or title.lower() in ("sba_api", "document", "content", "")

    # Prefer first markdown heading in content
    m = re.search(r"^#\s+(.+)$", content or "", re.M)
    if m:
        t = _clean(m.group(1))
        if t and t.lower() not in ("sba_api",):
            # Skip "Combined SBA API digest..."
            if not t.lower().startswith("combined sba"):
                return t

    if title and not looks_like_file:
        return title

    route = str(meta.get("route") or meta.get("child_path") or meta.get("path") or "")
    if route.startswith("/api/sba/"):
        return route.rstrip("/").rsplit("/", 1)[-1].replace("-", " ").replace("_", " ").title()
    # Last resort: humanize filename stem
    if title:
        t = re.sub(r"^api_sba_(content_)?", "", title, flags=re.I)
        t = re.sub(r"__(combined|overview|child).*$", "", t, flags=re.I)
        t = t.replace("_", " ").strip().title()
        if t:
            return t
    src = str(meta.get("source") or "")
    if src and src not in ("sba_api", "chroma"):
        return src.replace("_", " ").replace(".txt", "").title()
    return "SBA resource"


def _valid_api_path(p: str) -> bool:
    p = (p or "").strip().rstrip(".,;)")
    if not p.startswith("/api/sba/"):
        return False
    # Reject empty / junk segments (e.g. /api/sba/lifecycle/&)
    parts = [x for x in p.split("/") if x != ""]
    if len(parts) < 3:  # api, sba, ...
        return False
    for seg in parts[2:]:
        if not re.match(r"^[A-Za-z0-9_\-().]+$", seg):
            return False
    return True


def _path_from_meta(meta: dict, content: str) -> str:
    for key in ("child_path", "route", "path", "api_path"):
        p = str(meta.get(key) or "").strip()
        if _valid_api_path(p):
            return p.rstrip(".,;)")
    m = re.search(r"(?:API path|API route|Route|Path)\s*:\s*(/api/sba/\S+)", content or "", re.I)
    if m:
        p = m.group(1).rstrip(".,;)")
        if _valid_api_path(p):
            return p
    return ""


def _url_from_meta(meta: dict, content: str) -> str:
    for key in ("url", "link", "href", "official_url"):
        u = str(meta.get(key) or "").strip()
        if u.startswith("http"):
            return u.rstrip(".,;)")
    m = re.search(r"(?:Official URL|URL)\s*:\s*(https?://\S+)", content or "", re.I)
    if m:
        return m.group(1).rstrip(".,;)")
    m = re.search(r"(https?://(?:www\.)?sba\.gov[^\s\)\]\"']+)", content or "", re.I)
    if m:
        return m.group(1).rstrip(".,;)")
    return ""


def _browse_link(api_path: str, title: str = "") -> str:
    t = title or api_path.rstrip("/").rsplit("/", 1)[-1]
    return f"/browse#r={quote(api_path, safe='')}&t={quote(t)}"


def _md(label: str, href: str) -> str:
    label = (label or "Open").replace("[", "").replace("]", "")
    return f"[{label}]({href})"


# Inline program names → useful links (official + in-app where known)
_PROGRAM_INLINE = [
    (
        re.compile(r"\bSBA\s*7\s*(?:\(\s*a\s*\)|-\s*a|\s+a)\b(?:\s*loans?)?", re.I),
        "SBA 7(a) loans",
        "https://www.sba.gov/funding-programs/loans/7a-loans",
        "/api/sba/content/loans/7a",
    ),
    (
        re.compile(r"\bSBA\s*504\b(?:\s*loans?)?", re.I),
        "SBA 504 loans",
        "https://www.sba.gov/funding-programs/loans/504-loans",
        "/api/sba/content/loans/504",
    ),
    (
        re.compile(r"\bSBA\s*Microloans?\b|\bMicroloan\s+program\b", re.I),
        "SBA Microloans",
        "https://www.sba.gov/funding-programs/loans/microloans",
        "/api/sba/content/loans/microloans",
    ),
    (
        re.compile(r"\bLender\s*Match\b", re.I),
        "Lender Match",
        "https://www.sba.gov/funding-programs/loans/lender-match",
        "/api/sba/content/loans/lender-match",
    ),
    (
        re.compile(r"\bSBA-backed loans?\b|\bSBA-guaranteed loan", re.I),
        "SBA-backed loans",
        "https://www.sba.gov/funding-programs/loans",
        "/api/sba/content/loans",
    ),
]


def _linkify_program_mentions(text: str) -> str:
    """Turn known program phrases into markdown links (first match each)."""
    if not text:
        return text
    out = text
    for pat, label, official, api_path in _PROGRAM_INLINE:
        # Do not re-link text that is already inside markdown [..](..)
        def _sub(m, _official=official):
            # If match is already part of a markdown link, leave it
            start = m.start()
            before = out[max(0, start - 2) : start]
            if before.endswith("](") or before.endswith("["):
                return m.group(0)
            return _md(m.group(0), _official)

        # Skip if already has this official URL linked nearby
        if official in out and pat.search(out):
            # still try once for unlinked mention
            pass
        out, _n = pat.subn(_sub, out, count=1)
    return out


def _dedupe_key(title: str, path: str, url: str, body: str) -> str:
    base = (path or url or title or "").lower()
    if not base:
        base = hashlib.sha1((body or "")[:160].encode("utf-8", errors="ignore")).hexdigest()[:12]
    return base


def normalize_hits(
    documents: List[str],
    metadatas: Optional[List[dict]] = None,
    ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Normalize and dedupe Chroma/RAG rows into structured hits."""
    metadatas = metadatas or [{}] * len(documents)
    ids = ids or [str(i) for i in range(len(documents))]
    hits = []
    seen = set()
    for i, doc in enumerate(documents):
        meta = metadatas[i] if i < len(metadatas) and isinstance(metadatas[i], dict) else {}
        content = str(doc or "")
        title = _title_from_meta(meta, content)
        path = _path_from_meta(meta, content)
        if path and not _valid_api_path(path):
            path = ""
        url = _url_from_meta(meta, content)
        body = _strip_meta_noise(content)
        # Prefer prose: drop leading # title if duplicate of title
        body = re.sub(r"^#\s+.+$", "", body, count=1, flags=re.M).strip()
        body = re.sub(r"^(API|Path|Route|Source)\s*$", "", body, flags=re.I | re.M).strip()
        key = _dedupe_key(title, path, url, body)
        if key in seen:
            continue
        seen.add(key)
        # Skip empty or pure-meta leftovers (keep if we have a real official URL)
        if len(body) < 40 and not url:
            continue
        hits.append(
            {
                "id": ids[i] if i < len(ids) else str(i),
                "title": title,
                "body": body[:900],
                "path": path,
                "url": url,
                "type": str(meta.get("type") or meta.get("kind") or "").replace("_", " "),
                "metadata": meta,
            }
        )
    return hits


def format_hits_as_answer(query: str, hits: List[Dict[str, Any]]) -> Tuple[str, List[dict]]:
    """
    Build a plain, human-readable chat answer:

      - one short intro sentence
      - each resource as a bold title plus one short paragraph
      - no headings, no per-item action lines, no in-bubble link list

    Links are deliberately NOT repeated inside the bubble: the message's
    sources are returned alongside the text, and the chat's Resources panel
    collects them into the Links tab (links live in the tab until selected).
    The only section appended afterwards is "Use this information", and only
    when there is a real form, tool, or program page to use.
    """
    if not hits:
        return (
            "I couldn't find a clear SBA resource for that yet. "
            "Try the Resources panel for SBA Loans and Programs, "
            "or ask the same question in different words.",
            [],
        )

    q = _clean(query) or "your question"
    lines = [
        f"Here is what I found on {q}:",
        "",
    ]

    sources_out = []

    for hit in hits[:5]:
        title = hit["title"]
        body = hit["body"]
        # Prefer first paragraph, kept short
        para = re.split(r"\n\s*\n", body)[0] if body else ""
        blurb = _clean(para or body)
        if len(blurb) > 320:
            blurb = blurb[:317].rsplit(" ", 1)[0] + "…"

        path = hit.get("path") if _valid_api_path(hit.get("path") or "") else ""
        hit["path"] = path
        lines.append(f"**{title}**")
        if blurb:
            lines.append("")
            lines.append(blurb)
        lines.append("")

        sources_out.append(
            {
                "id": hit.get("id"),
                "name": title,
                "title": title,
                "content": blurb,
                "url": hit.get("url") or "",
                "path": hit.get("path") or "",
                "metadata": {
                    **(hit.get("metadata") or {}),
                    "title": title,
                    "url": hit.get("url") or "",
                    "path": hit.get("path") or "",
                    "route": hit.get("path") or "",
                },
            }
        )

    try:
        from backend.services.actionable_content import attach_actionable_section

        text = attach_actionable_section("\n".join(lines).rstrip(), query=query, hits=hits)
    except Exception:
        text = "\n".join(lines).rstrip()

    return text, sources_out


def format_chroma_query_result(message: str, results: dict) -> Optional[Dict[str, Any]]:
    """
    Convert rag_manager.query_documents output into {text, sources}.
    Returns None if no usable documents.
    """
    if not isinstance(results, dict) or results.get("error"):
        return None

    # Nested chroma lists
    documents = results.get("documents")
    metadatas = results.get("metadatas")
    ids = results.get("ids")
    if documents and isinstance(documents[0], list):
        documents = documents[0]
    if metadatas and isinstance(metadatas[0], list):
        metadatas = metadatas[0]
    if ids and isinstance(ids[0], list):
        ids = ids[0]

    # Alternate shapes
    if not documents and isinstance(results.get("results"), list):
        documents = []
        metadatas = []
        ids = []
        for row in results["results"]:
            if not isinstance(row, dict):
                continue
            documents.append(row.get("content") or row.get("text") or "")
            metadatas.append(row.get("metadata") or {})
            ids.append(str(row.get("id") or len(documents)))

    if not documents:
        # Enhanced format with answer field only
        if results.get("answer"):
            try:
                from backend.services.link_enrichment import enrich_answer_with_links

                text = enrich_answer_with_links(str(results.get("answer")), results.get("source_documents") or [])
            except Exception:
                text = str(results.get("answer"))
            return {"text": text, "sources": results.get("source_documents") or []}
        return None

    hits = normalize_hits(list(documents), list(metadatas or []), list(ids or []))
    if not hits:
        return None
    text, sources = format_hits_as_answer(message, hits)
    return {"text": text, "sources": sources}
