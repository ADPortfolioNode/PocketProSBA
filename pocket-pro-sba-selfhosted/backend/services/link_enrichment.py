"""
Ensure assistant/RAG answers always include clickable hyperlinks.

Chat UIs (magazine formatter) turn markdown [label](url) and bare https://
into real <a> tags. Internal /api/sba/* paths become /browse deep-links.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote

# Official SBA anchors we can safely attach when topics are mentioned
_TOPIC_LINKS: List[Tuple[re.Pattern, str, str]] = [
    (re.compile(r"\b7\s*[\(\-]?\s*a\b", re.I), "SBA 7(a) loans (official)", "https://www.sba.gov/funding-programs/loans/7a-loans"),
    (re.compile(r"\b504\b"), "SBA 504 loans (official)", "https://www.sba.gov/funding-programs/loans/504-loans"),
    (re.compile(r"\bmicroloan", re.I), "SBA Microloans (official)", "https://www.sba.gov/funding-programs/loans/microloans"),
    (re.compile(r"\blender\s*match", re.I), "Lender Match (official)", "https://www.sba.gov/funding-programs/loans/lender-match"),
    (re.compile(r"\bdisaster", re.I), "Disaster assistance (official)", "https://www.sba.gov/funding-programs/disaster-assistance"),
    (re.compile(r"\b8\s*[\(\-]?\s*a\b", re.I), "8(a) Business Development (official)", "https://www.sba.gov/federal-contracting/contracting-assistance-programs/8a-business-development-program"),
]

_URL_RE = re.compile(r"https?://[^\s\]\)<>\"']+", re.I)
_OFFICIAL_LINE_RE = re.compile(
    r"(?im)^(?:official\s*url|url|source\s*url|link|file\s*/\s*form\s*url|file\s*url|form\s*url|registration\s*url)\s*:\s*(https?://\S+)"
)
_ACTION_LINE_RE = re.compile(r"(?im)^Action:\s*(.+?)\s*->\s*(\S+)")
_API_ROUTE_RE = re.compile(r"(?im)^(?:api\s*route|route|path)\s*:\s*(/api/sba/\S+)")
_API_INLINE_RE = re.compile(r"(/api/sba/[a-z0-9_./\-]+)", re.I)


def _clean_url(url: str) -> str:
    return (url or "").strip().rstrip(".,;:)")


def browse_href(api_path: str, title: str = "") -> str:
    path = _clean_url(api_path)
    if not path.startswith("/api/"):
        return path
    t = title or path.rstrip("/").rsplit("/", 1)[-1].replace("-", " ").replace("_", " ")
    return f"/browse#r={quote(path, safe='')}&t={quote(t)}"


def programs_href() -> str:
    """Programs catalog still lives at /sba; API resources open on /browse."""
    return "/browse"


def md_link(label: str, href: str) -> str:
    label = (label or "Open link").replace("]", "").replace("[", "")
    href = _clean_url(href)
    return f"[{label}]({href})"


def extract_urls_from_text(text: str) -> List[Tuple[str, str]]:
    """Return list of (label, href) found in free text."""
    found: List[Tuple[str, str]] = []
    seen = set()

    for m in _OFFICIAL_LINE_RE.finditer(text or ""):
        href = _clean_url(m.group(1))
        if href and href not in seen:
            seen.add(href)
            label = "Official SBA page"
            line = m.group(0).lower()
            if "form" in line or "file" in line:
                label = "Open form / document"
            elif "registration" in line:
                label = "Registration link"
            found.append((label, href))

    for m in _ACTION_LINE_RE.finditer(text or ""):
        label = (m.group(1) or "Open").strip()
        href = _clean_url(m.group(2))
        if href.startswith("/api/sba/"):
            href = browse_href(href, label)
        if href and href not in seen:
            seen.add(href)
            found.append((label, href))

    for m in _URL_RE.finditer(text or ""):
        href = _clean_url(m.group(0))
        if href and href not in seen:
            seen.add(href)
            label = "Open official page" if "sba.gov" in href.lower() else "Open link"
            found.append((label, href))

    for m in _API_ROUTE_RE.finditer(text or ""):
        path = _clean_url(m.group(1))
        if path and path not in seen:
            seen.add(path)
            found.append((f"Open in Resources: {path}", browse_href(path)))

    for m in _API_INLINE_RE.finditer(text or ""):
        path = _clean_url(m.group(1))
        if path and path not in seen and path.startswith("/api/sba/"):
            seen.add(path)
            found.append((f"Browse API topic: {path}", browse_href(path)))

    return found


def links_from_sources(sources: Optional[Iterable[Any]]) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    seen = set()
    for s in sources or []:
        if not isinstance(s, dict):
            continue
        meta = s.get("metadata") if isinstance(s.get("metadata"), dict) else {}
        title = (
            s.get("title")
            or meta.get("title")
            or meta.get("source")
            or s.get("source")
            or "SBA resource"
        )
        for key in ("url", "href", "link", "official_url"):
            href = _clean_url(str(s.get(key) or meta.get(key) or ""))
            if href.startswith("http") and href not in seen:
                seen.add(href)
                out.append((f"{title} (official)", href))
        for key in ("route", "path", "child_path", "api_path"):
            path = _clean_url(str(s.get(key) or meta.get(key) or ""))
            if path.startswith("/api/sba/") and path not in seen:
                seen.add(path)
                out.append((f"{title} — open in Resources", browse_href(path, str(title))))
            # live KB file names → try recover route from combined digests path in text
        path_fs = str(s.get("path") or meta.get("path") or "")
        if "sba_api_live" in path_fs.replace("\\", "/"):
            # e.g. api_sba_content_loans_7a__combined.txt
            name = path_fs.replace("\\", "/").rsplit("/", 1)[-1]
            m = re.match(r"api_sba_(.+?)__(?:combined|overview|child).*\.txt$", name)
            if m:
                route = "/api/sba/" + m.group(1).replace("_", "/")
                # fix common double segments: content/loans/7a from content_loans_7a
                route = route.replace("/sba/content/", "/sba/content/")  # no-op clarity
                # Rebuild properly: api_sba_content_loans_7a → /api/sba/content/loans/7a
                slug = m.group(1)
                if slug.startswith("content_"):
                    rest = slug[len("content_") :]
                    parts = rest.split("_")
                    # loans_7a → loans/7a ; content already stripped
                    if len(parts) >= 2 and parts[0] in (
                        "loans",
                        "contracting",
                        "disaster",
                        "articles",
                        "offices",
                        "lenders",
                        "events",
                        "sbir",
                        "blogs",
                        "courses",
                        "documents",
                    ):
                        route = f"/api/sba/content/{parts[0]}/{'/'.join(parts[1:])}" if len(parts) > 1 else f"/api/sba/content/{parts[0]}"
                    else:
                        route = "/api/sba/content/" + rest.replace("_", "/")
                elif slug.startswith("lifecycle_"):
                    route = "/api/sba/lifecycle/" + slug[len("lifecycle_") :].replace("_", "/")
                if route not in seen:
                    seen.add(route)
                    pretty = route.rstrip("/").rsplit("/", 1)[-1].replace("-", " ").replace("_", " ")
                    if pretty.startswith("api sba") or "combined" in str(title).lower() or str(title).endswith(".txt"):
                        pretty = f"SBA topic ({pretty})" if pretty else "SBA topic"
                    out.append((f"Open in Resources: {pretty}", browse_href(route, pretty)))
    return out


def topic_links_for_text(text: str) -> List[Tuple[str, str]]:
    out = []
    seen = set()
    body = text or ""
    for pat, label, href in _TOPIC_LINKS:
        if pat.search(body) and href not in seen:
            seen.add(href)
            out.append((label, href))
    return out


def build_links_section(pairs: List[Tuple[str, str]], *, max_links: int = 12) -> str:
    if not pairs:
        return ""
    lines = ["## Links", ""]
    lines.append("Click any link below to open the resource (official SBA page or in-app browser):")
    lines.append("")
    seen = set()
    n = 0
    for label, href in pairs:
        href = _clean_url(href)
        if not href or href in seen:
            continue
        seen.add(href)
        lines.append(f"- {md_link(label, href)}")
        n += 1
        if n >= max_links:
            break
    # Always include app nav anchors
    if "/sba" not in seen:
        lines.append(f"- {md_link('SBA Programs (in app)', programs_href())}")
    if not any(h.startswith("/browse") for h in seen):
        lines.append(
            f"- {md_link('Browse SBA Loans (in app)', browse_href('/api/sba/content/loans', 'SBA Loans'))}"
        )
    return "\n".join(lines)


def enrich_answer_with_links(
    answer: str,
    sources: Optional[Iterable[Any]] = None,
    *,
    extra: Optional[List[Tuple[str, str]]] = None,
) -> str:
    """
    Append a ## Links section with markdown hyperlinks if missing.
    Safe to call multiple times (won't duplicate if ## Links already present).
    """
    text = (answer or "").rstrip()
    if not text:
        text = "Here are the best available SBA resources for your question."

    if re.search(r"(?im)^##\s*links\b", text) or re.search(r"\[.+\]\(https?://", text):
        # Still merge any missing official URLs found in digests
        existing = set(_URL_RE.findall(text))
        pairs = extract_urls_from_text(text) + links_from_sources(sources) + (extra or []) + topic_links_for_text(text)
        missing = [(l, h) for l, h in pairs if h not in existing and f"]({h})" not in text]
        if not missing:
            return text
        # Append only missing as bullets under existing section
        add = ["", "### More links", ""]
        seen = set()
        for label, href in missing[:8]:
            if href in seen:
                continue
            seen.add(href)
            add.append(f"- {md_link(label, href)}")
        return text + "\n" + "\n".join(add)

    pairs: List[Tuple[str, str]] = []
    pairs.extend(extract_urls_from_text(text))
    pairs.extend(links_from_sources(sources))
    pairs.extend(extra or [])
    pairs.extend(topic_links_for_text(text))

    section = build_links_section(pairs)
    if not section:
        # Absolute minimum navigation
        section = build_links_section(
            [
                ("SBA Loans (official)", "https://www.sba.gov/funding-programs/loans"),
                ("Browse SBA Loans (in app)", browse_href("/api/sba/content/loans", "SBA Loans")),
                ("SBA Programs (in app)", programs_href()),
            ]
        )
    return text + "\n\n" + section
