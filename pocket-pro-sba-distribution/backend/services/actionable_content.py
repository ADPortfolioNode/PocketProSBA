"""
Actionable SBA content for chat/RAG answers.

Users must be able to *use* information: open official pages, forms, docs,
Lender Match, local offices, and in-app Resources topics — not only read text.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

logger = logging.getLogger(__name__)

# Curated high-value actions by topic keyword
_CURATED: List[Tuple[re.Pattern, List[Dict[str, str]]]] = [
    (
        re.compile(r"7\s*[\(\-]?\s*a|general\s+loan|working\s+capital", re.I),
        [
            {
                "label": "7(a) loans — official program page",
                "href": "https://www.sba.gov/funding-programs/loans/7a-loans",
                "kind": "official",
            },
            {
                "label": "7(a) docs & requirements (in app)",
                "href": "/browse#r=%2Fapi%2Fsba%2Fcontent%2Fdocuments%2F7a-docs&t=7(a)%20docs",
                "kind": "docs",
            },
            {
                "label": "Explore 7(a) in Resources",
                "href": "/browse#r=%2Fapi%2Fsba%2Fcontent%2Floans%2F7a&t=SBA%207(a)",
                "kind": "app",
            },
        ],
    ),
    (
        re.compile(r"\b504\b|fixed\s+asset|real\s+estate|CDC", re.I),
        [
            {
                "label": "504 loans — official program page",
                "href": "https://www.sba.gov/funding-programs/loans/504-loans",
                "kind": "official",
            },
            {
                "label": "504 documentation (in app)",
                "href": "/browse#r=%2Fapi%2Fsba%2Fcontent%2Fdocuments%2F504-docs&t=504%20docs",
                "kind": "docs",
            },
            {
                "label": "Explore 504 in Resources",
                "href": "/browse#r=%2Fapi%2Fsba%2Fcontent%2Floans%2F504&t=SBA%20504",
                "kind": "app",
            },
        ],
    ),
    (
        re.compile(r"microloan|micro\s*loan", re.I),
        [
            {
                "label": "Microloans — official program page",
                "href": "https://www.sba.gov/funding-programs/loans/microloans",
                "kind": "official",
            },
            {
                "label": "Microloan documentation (in app)",
                "href": "/browse#r=%2Fapi%2Fsba%2Fcontent%2Fdocuments%2Fmicroloan-docs&t=Microloan%20docs",
                "kind": "docs",
            },
        ],
    ),
    (
        re.compile(r"lender\s*match|find\s+a\s+lender|connect.*lender", re.I),
        [
            {
                "label": "Lender Match — get matched to lenders",
                "href": "https://www.sba.gov/funding-programs/loans/lender-match",
                "kind": "tool",
            },
            {
                "label": "Lender Match in Resources",
                "href": "/browse#r=%2Fapi%2Fsba%2Fcontent%2Floans%2Flender-match&t=Lender%20Match",
                "kind": "app",
            },
        ],
    ),
    (
        re.compile(r"form|document|download|paperwork|application", re.I),
        [
            {
                "label": "SBA forms library (official)",
                "href": "https://www.sba.gov/document",
                "kind": "form",
            },
            {
                "label": "Browse SBA documents & forms (in app)",
                "href": "/browse#r=%2Fapi%2Fsba%2Fcontent%2Fdocuments&t=Documents",
                "kind": "docs",
            },
        ],
    ),
    (
        re.compile(r"disaster", re.I),
        [
            {
                "label": "Disaster assistance (official)",
                "href": "https://www.sba.gov/funding-programs/disaster-assistance",
                "kind": "official",
            },
            {
                "label": "Disaster resources (in app)",
                "href": "/browse#r=%2Fapi%2Fsba%2Fcontent%2Fdisaster&t=Disaster",
                "kind": "app",
            },
        ],
    ),
    (
        re.compile(r"8\s*[\(\-]?\s*a|contract|HUBZone|WOSB|SDVOSB", re.I),
        [
            {
                "label": "Federal contracting (official)",
                "href": "https://www.sba.gov/federal-contracting",
                "kind": "official",
            },
            {
                "label": "Contracting programs (in app)",
                "href": "/browse#r=%2Fapi%2Fsba%2Fcontent%2Fcontracting&t=Contracting",
                "kind": "app",
            },
        ],
    ),
    (
        re.compile(r"office|counsel|mentor|SCORE|SBDC|local\s+help", re.I),
        [
            {
                "label": "Find local SBA help (official)",
                "href": "https://www.sba.gov/local-assistance",
                "kind": "tool",
            },
            {
                "label": "Offices & local resources (in app)",
                "href": "/browse#r=%2Fapi%2Fsba%2Fcontent%2Foffices&t=Offices",
                "kind": "app",
            },
        ],
    ),
    (
        re.compile(r"start\s+a\s+business|launch|register", re.I),
        [
            {
                "label": "Start your business (official guide)",
                "href": "https://www.sba.gov/business-guide/launch-your-business",
                "kind": "guide",
            },
            {
                "label": "Start lifecycle (in app)",
                "href": "/browse#r=%2Fapi%2Fsba%2Flifecycle%2Fstart&t=Start",
                "kind": "app",
            },
            {
                "label": "SBA Resources hub",
                "href": "/browse",
                "kind": "app",
            },
        ],
    ),
]

_ALWAYS = [
    {
        "label": "SBA forms library",
        "href": "https://www.sba.gov/document",
        "kind": "form",
    },
    {
        "label": "Browse all SBA Loans (in app)",
        "href": "/browse#r=%2Fapi%2Fsba%2Fcontent%2Floans&t=SBA%20Loans",
        "kind": "app",
    },
    {
        "label": "SBA Resources (in app)",
        "href": "/browse",
        "kind": "app",
    },
    {
        "label": "Lender Match tool",
        "href": "https://www.sba.gov/funding-programs/loans/lender-match",
        "kind": "tool",
    },
]


def _md(label: str, href: str) -> str:
    label = (label or "Open").replace("[", "").replace("]", "")
    return f"[{label}]({href})"


def _browse(api_path: str, title: str = "") -> str:
    t = title or api_path.rstrip("/").rsplit("/", 1)[-1]
    return f"/browse#r={quote(api_path, safe='')}&t={quote(t)}"


def actions_from_item(item: dict) -> List[Dict[str, str]]:
    """Extract usable actions from an SBA API item (form, doc, event, program)."""
    if not isinstance(item, dict):
        return []
    out: List[Dict[str, str]] = []
    title = str(item.get("title") or item.get("name") or "Resource")
    itype = str(item.get("type") or "").lower()

    file_url = str(item.get("fileUrl") or item.get("file_url") or "").strip()
    reg = str(item.get("registrationLink") or item.get("registration_link") or "").strip()
    url = str(item.get("url") or item.get("link") or "").strip()
    path = str(item.get("path") or "").strip()

    if file_url.startswith("http"):
        kind = "form" if "form" in itype or "form" in title.lower() or "document" in itype else "download"
        out.append(
            {
                "label": f"{'Open form / document' if kind == 'form' else 'Open document'}: {title}",
                "href": file_url,
                "kind": kind,
            }
        )
    if reg.startswith("http"):
        out.append({"label": f"Register: {title}", "href": reg, "kind": "register"})
    if url.startswith("http") and url not in {a["href"] for a in out}:
        label = "Official page"
        if "form" in itype or "form" in title.lower():
            label = "Open form page"
        elif "document" in itype:
            label = "Open documentation"
        elif "event" in itype:
            label = "Event details"
        elif "tool" in itype or "lender" in title.lower():
            label = "Open tool"
        out.append({"label": f"{label}: {title}", "href": url, "kind": "official"})
    if path.startswith("/api/sba/"):
        out.append(
            {
                "label": f"Explore in Resources: {title}",
                "href": _browse(path, title),
                "kind": "app",
            }
        )

    # Explicit actions array from API envelope
    for act in item.get("actions") or []:
        if not isinstance(act, dict):
            continue
        href = str(act.get("href") or act.get("path") or act.get("url") or "").strip()
        if href.startswith("/api/sba/"):
            href = _browse(href, act.get("label") or title)
        if not href.startswith("http") and not href.startswith("/"):
            continue
        lab = str(act.get("label") or act.get("id") or "Open")
        out.append({"label": f"{lab}: {title}" if title not in lab else lab, "href": href, "kind": "action"})

    return out


def collect_actions(
    query: str = "",
    hits: Optional[List[dict]] = None,
    api_items: Optional[List[dict]] = None,
    *,
    max_actions: int = 14,
) -> List[Dict[str, str]]:
    """Merge curated + hit-derived + item-derived actions, deduped by href."""
    seen = set()
    actions: List[Dict[str, str]] = []

    def add(a: dict):
        href = (a.get("href") or "").strip()
        if not href or href in seen:
            return
        # skip junk
        if href.endswith("/&") or "%26" in href and "lifecycle" in href:
            return
        seen.add(href)
        actions.append(a)

    text = query or ""
    for hit in hits or []:
        text += " " + str(hit.get("title") or "") + " " + str(hit.get("body") or "")
        # from hit fields
        if hit.get("url"):
            add(
                {
                    "label": f"Official: {hit.get('title') or 'SBA page'}",
                    "href": hit["url"],
                    "kind": "official",
                }
            )
        if hit.get("path") and str(hit["path"]).startswith("/api/sba/"):
            add(
                {
                    "label": f"Open in Resources: {hit.get('title') or 'topic'}",
                    "href": _browse(hit["path"], hit.get("title") or ""),
                    "kind": "app",
                }
            )
        meta = hit.get("metadata") or {}
        for key in ("fileUrl", "file_url", "registrationLink", "url"):
            u = str(meta.get(key) or "").strip()
            if u.startswith("http"):
                kind = "form" if "form" in key.lower() or "document" in str(meta.get("type") or "") else "official"
                add({"label": f"Open related resource ({hit.get('title') or 'SBA'})", "href": u, "kind": kind})

    for item in api_items or []:
        for a in actions_from_item(item):
            add(a)

    for pat, acts in _CURATED:
        if pat.search(text):
            for a in acts:
                add(a)

    # Soft-fetch forms/docs when query is about paperwork or loans
    if re.search(r"form|document|loan|7\s*a|504|apply|application", text, re.I):
        try:
            from backend.services.SBA_Content import SBAContentAPI

            api = SBAContentAPI()
            docs = api.search_documents(query="", page=1, fresh=False) or {}
            for it in (docs.get("items") or [])[:8]:
                for a in actions_from_item(it if isinstance(it, dict) else {}):
                    add(a)
        except Exception as e:
            logger.debug("actionable docs soft-fail: %s", e)

    for a in _ALWAYS:
        add(a)

    # Kind priority: form/tool first
    order = {"form": 0, "download": 1, "tool": 2, "register": 3, "official": 4, "docs": 5, "guide": 6, "app": 7, "action": 8}
    actions.sort(key=lambda a: order.get(a.get("kind") or "", 9))
    return actions[:max_actions]


def format_actions_section(actions: List[Dict[str, str]]) -> str:
    if not actions:
        return ""
    lines = [
        "## Use this information",
        "",
        "Open a link below to **use** forms, tools, or full program pages:",
        "",
    ]
    icons = {
        "form": "📝",
        "download": "📄",
        "tool": "🛠️",
        "register": "📅",
        "official": "🌐",
        "docs": "📚",
        "guide": "📖",
        "app": "📂",
        "action": "➡️",
    }
    for a in actions:
        icon = icons.get(a.get("kind") or "", "🔗")
        lines.append(f"- {icon} {_md(a.get('label') or 'Open', a.get('href') or '#')}")
    return "\n".join(lines)


def attach_actionable_section(
    answer: str,
    query: str = "",
    hits: Optional[List[dict]] = None,
    api_items: Optional[List[dict]] = None,
) -> str:
    """Append ## Use this information if missing; refresh if thin."""
    text = (answer or "").rstrip()
    actions = collect_actions(query=query, hits=hits, api_items=api_items)
    section = format_actions_section(actions)
    if not section:
        return text
    if re.search(r"(?im)^##\s*Use this information\b", text):
        # Already present — keep answer, ensure ## Links still has essentials via caller
        return text
    # Place before trailing ## Links if present so "use" is primary
    m = re.search(r"(?im)^##\s*Links\b", text)
    if m:
        return text[: m.start()].rstrip() + "\n\n" + section + "\n\n" + text[m.start() :]
    return text + "\n\n" + section
