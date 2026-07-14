"""
PocketPro SBA — machine-readable App Standard Template.

CURRENT functionality is the mandatory standard for the whole app.
Import these constants / helpers when adding features so navigation,
RAG, and actionable content stay consistent.

See: docs/APP_STANDARD_TEMPLATE.md
"""

from __future__ import annotations

from typing import Any, Dict, List

# Version of the locked standard (bump when behavior intentionally changes)
STANDARD_VERSION = "2026-07-11.1"
STANDARD_NAME = "PocketPro SBA Parent→Children + Usable Content"

# ---------------------------------------------------------------------------
# Core rules
# ---------------------------------------------------------------------------

CORE_RULE = (
    "PARENT → GET path → render CHILDREN; "
    "child with children is always a LINK (next parent); "
    "leaf → detail + official/form/document actions; "
    "API envelope → soft RAG ingest; "
    "answers → human-readable + clickable + usable."
)

LEAF_TYPES = frozenset(
    {
        "overview",
        "link",
        "notice",
        "source_status",
        "loan_section",
    }
)

LEAF_ID_MARKERS = ("-overview", "-official", "-about", "-how", "-sec-")

# Surfaces that implement the standard (live mounts preferred)
STANDARD_SURFACES = {
    "programs": {
        "url": "/sba",
        "file": "frontend/public/programs.html",
        "pattern": "catalog_then_open_browse",
        "note": "API paths always navigate to /browse#r=…",
    },
    "browse": {
        "url": "/browse",
        "file": "frontend/public/resources.html",
        "pattern": "recursive_openRoute",
        "note": "Canonical SBA resources explorer for all API topics",
    },
    "chat": {
        "url": "/chat",
        "assets": [
            "frontend/build/static/js/chat-magazine.js",
            "frontend/build/static/css/sleek-layout.css",
        ],
        "pattern": "magazine_prose_actionable_links",
    },
    "api_catalog": {"path": "/api/sba/resources"},
    "api_content": {"path_prefix": "/api/sba/content/"},
    "api_lifecycle": {"path_prefix": "/api/sba/lifecycle/"},
    "rag_ingest_status": {"path": "/api/sba/rag-ingest"},
}

# CTA copy (keep UI language consistent)
CTA = {
    "parent": "Open on Resources page →",
    "child_link": "Explore children →",
    "render": "Open on Resources page →",
    "leaf": "Open details →",
    "form": "Open form / document",
    "register": "Register",
    "official": "Official",
    "official_page": "Official page",
    "resources": "Open on Resources page",
}

# Answer section headings
ANSWER_SECTIONS = {
    "summary_prefix": "Here’s a clear summary from live SBA resources about",
    "use_this": "Use this information",
    "links": "Links",
}

FORBIDDEN_ANSWER_PATTERNS = [
    r"Source\s+\d+\s*:\s*sba_api",
    r"Here's what I found regarding your query:\s*\n\s*Source",
]


def item_is_leaf(item: Dict[str, Any]) -> bool:
    """Standard leaf test: no further API children to explore."""
    if not item:
        return True
    path = str(item.get("path") or "")
    if path.startswith("/api/") and (item.get("drillable") or item.get("has_children")):
        return False
    if item.get("resources"):
        return False
    itype = str(item.get("type") or "").lower()
    if itype in LEAF_TYPES:
        return True
    cid = str(item.get("id") or "")
    if any(m in cid for m in LEAF_ID_MARKERS):
        return True
    return not path.startswith("/api/")


def item_is_linkable_parent(item: Dict[str, Any]) -> bool:
    """Child must be a link if it can load more content."""
    return not item_is_leaf(item)


def standard_item_flags(path: str = "", resources: List = None, item_type: str = "") -> Dict[str, bool]:
    """Compute drillable / has_children per template."""
    resources = resources or []
    path = str(path or "")
    itype = str(item_type or "").lower()
    if itype in LEAF_TYPES:
        return {"drillable": False, "has_children": bool(resources)}
    drillable = path.startswith("/api/")
    return {
        "drillable": drillable,
        "has_children": bool(drillable or resources),
    }


def standard_checklist() -> List[str]:
    return [
        "Parent has /api/… path and loads children on click",
        "Children with children are links (not modal-only)",
        "Recursive back/breadcrumb works",
        "Envelope has drillable, has_children, actions",
        "Forms/docs expose fileUrl + Open form/document",
        "Envelope schedules RAG ingest",
        "User-facing text is human-readable (no Source N: sba_api)",
        "Answer includes usable links (official + in-app + forms/tools)",
        "Live HTML/CSS/JS mounted for core UX",
        "Soft-fail never blanks the whole surface",
    ]


def describe_standard() -> Dict[str, Any]:
    return {
        "version": STANDARD_VERSION,
        "name": STANDARD_NAME,
        "core_rule": CORE_RULE,
        "surfaces": STANDARD_SURFACES,
        "cta": CTA,
        "answer_sections": ANSWER_SECTIONS,
        "checklist": standard_checklist(),
        "doc": "docs/APP_STANDARD_TEMPLATE.md",
    }
