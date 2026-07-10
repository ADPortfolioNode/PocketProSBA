"""
SBA public content client — multi-source with graceful fallback.

Research summary (2026):
------------------------
1) Legacy SBA.gov Content Search API (used historically by this app)
   Base: https://www.sba.gov/api/content/search/{type}.json
   Types: articles, blogs, courses, documents, events, offices, lenders, ...
   Status: currently returns HTTP 404 (site rearchitecture). Kept as primary
   attempt so automatic recovery works if SBA restores the JSON API.

2) SBA Content API (developer portal)
   Docs: https://developer.sba.gov/  and apis.io listing baseURL https://api.sba.gov
   Status: public unauthenticated paths currently 404; may require portal keys.

3) SBIR/STTR Public API (documented, no API key)
   Docs: https://www.sbir.gov/api
   Base: https://api.www.sbir.gov/public/api/
   Endpoints:
     GET /awards?agency=NSF&year=2022&rows=100&start=0
     GET /solicitations?rows=100
     GET awards by firm=..., ri=..., format=xml|json
   Status: often rate-limited (HTTP 429) or temporarily unavailable.

4) SBA Open Data (data.sba.gov)
   CKAN-style open data catalog for size standards, FOIA loan extracts, etc.
   Status: public CKAN /api/3 paths not reliably open without portal login.

5) Official sba.gov HTML (public, no key)
   Working pages used as structured fallback sources:
     https://www.sba.gov/funding-programs/loans
     https://www.sba.gov/funding-programs/loans/7a-loans
     https://www.sba.gov/funding-programs/loans/504-loans
     https://www.sba.gov/funding-programs/loans/microloans
     https://www.sba.gov/blog
     https://www.sba.gov/about-sba/sba-locations
   Consumption: HTTP GET + light HTML extract (stdlib html.parser).

Normalized response shape for route handlers:
  {
    "items": [...],
    "total_pages": int,
    "totalPages": int,
    "currentPage": int,
    "source": "legacy_json|sbir|sba_html|static",
    "degraded": bool,   # True when not live primary API
    "message": optional str
  }
"""

from __future__ import annotations

import logging
import os
import re
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlencode

import requests

logger = logging.getLogger(__name__)

# --- Public bases (overridable via env for future portal keys / mirrors) ---
SBA_CONTENT_BASE = os.getenv(
    "SBA_CONTENT_API_BASE",
    "https://www.sba.gov/api/content/search",
).rstrip("/")
SBA_SITE = os.getenv("SBA_SITE_BASE", "https://www.sba.gov").rstrip("/")
SBIR_API_BASE = os.getenv(
    "SBIR_API_BASE",
    "https://api.www.sbir.gov/public/api",
).rstrip("/")
SBA_API_KEY = os.getenv("SBA_API_KEY") or os.getenv("SBA_CONTENT_API_KEY")

DEFAULT_HEADERS = {
    "User-Agent": os.getenv(
        "SBA_HTTP_USER_AGENT",
        "PocketProSBA/1.0 (local assistant; +https://localhost)",
    ),
    "Accept": "application/json, text/html;q=0.9,*/*;q=0.8",
}

# Short TTL so non-RAG rendered SBA info stays current.
# Static/RAG content is never claimed as "current".
_CACHE: Dict[str, Tuple[float, Any]] = {}
_CACHE_TTL = int(os.getenv("SBA_CACHE_TTL_SECONDS", "90"))
_LIVE_SOURCES = frozenset({"legacy_json", "sbir", "sba_html", "sba_html+live"})


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cache_get(key: str) -> Optional[Any]:
    item = _CACHE.get(key)
    if not item:
        return None
    expires, value = item
    if time.time() > expires:
        _CACHE.pop(key, None)
        return None
    return value


def _cache_set(key: str, value: Any, ttl: int = _CACHE_TTL) -> None:
    _CACHE[key] = (time.time() + ttl, value)


def clear_sba_cache() -> None:
    """Drop all in-process SBA caches (used when ?fresh=1)."""
    _CACHE.clear()


class _PageContentParser(HTMLParser):
    """Extract links, headings, meta description, and visible paragraph text."""

    def __init__(self) -> None:
        super().__init__()
        self.links: List[Dict[str, str]] = []
        self.headings: List[str] = []
        self.meta_description = ""
        self.paragraphs: List[str] = []
        self.title = ""
        self._in_a = False
        self._a_href = ""
        self._a_text: List[str] = []
        self._in_heading = False
        self._heading_text: List[str] = []
        self._in_p = False
        self._p_text: List[str] = []
        self._in_title = False
        self._title_text: List[str] = []
        self._skip_depth = 0  # script/style/noscript

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)
        if tag in ("script", "style", "noscript", "svg"):
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "meta":
            name = (attrs_d.get("name") or attrs_d.get("property") or "").lower()
            if name in ("description", "og:description") and attrs_d.get("content"):
                if not self.meta_description:
                    self.meta_description = attrs_d["content"].strip()
        if tag == "title":
            self._in_title = True
            self._title_text = []
        if tag == "a" and attrs_d.get("href"):
            self._in_a = True
            self._a_href = attrs_d.get("href", "")
            self._a_text = []
        if tag in ("h1", "h2", "h3"):
            self._in_heading = True
            self._heading_text = []
        if tag == "p":
            self._in_p = True
            self._p_text = []

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg"):
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return
        if tag == "title" and self._in_title:
            self.title = re.sub(r"\s+", " ", "".join(self._title_text)).strip()
            self._in_title = False
        if tag == "a" and self._in_a:
            text = re.sub(r"\s+", " ", "".join(self._a_text)).strip()
            href = self._a_href.strip()
            if text and href and not href.startswith(("#", "javascript:", "mailto:")):
                self.links.append({"title": text, "href": href})
            self._in_a = False
        if tag in ("h1", "h2", "h3") and self._in_heading:
            text = re.sub(r"\s+", " ", "".join(self._heading_text)).strip()
            if text and len(text) > 2:
                self.headings.append(text)
            self._in_heading = False
        if tag == "p" and self._in_p:
            text = re.sub(r"\s+", " ", "".join(self._p_text)).strip()
            if len(text) >= 40:
                self.paragraphs.append(text)
            self._in_p = False

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._in_title:
            self._title_text.append(data)
        if self._in_a:
            self._a_text.append(data)
        if self._in_heading:
            self._heading_text.append(data)
        if self._in_p:
            self._p_text.append(data)


# Back-compat alias used by older call sites in this module
_LinkHeadingParser = _PageContentParser


_BOILERPLATE_SNIPPETS = (
    "an official website of the united states government",
    "official websites use .gov",
    "secure .gov websites use https",
    "here's how you know",
    "share this page",
    "last updated",
    "javascript",
    "freedom 250",
    "small business pledge",
    "get your free certificate",
    "honor america",
)


def _is_boilerplate(text: str) -> bool:
    low = (text or "").lower()
    if len(low) < 40:
        return True
    return any(b in low for b in _BOILERPLATE_SNIPPETS)


def _strip_promos(text: str) -> str:
    """Remove leading promo sentences that appear on many sba.gov pages."""
    if not text:
        return ""
    # Drop sentences that are pure site-wide campaigns
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    kept = [s for s in sentences if not _is_boilerplate(s)]
    return " ".join(kept).strip() or text.strip()


def _snippet_from_parser(parser: _PageContentParser, max_len: int = 480) -> str:
    """Prefer meta description, then first non-banner paragraphs from the live page."""
    parts: List[str] = []
    if parser.meta_description and not _is_boilerplate(parser.meta_description):
        parts.append(_strip_promos(parser.meta_description.strip()))
    for p in parser.paragraphs:
        cleaned = _strip_promos(p)
        if not cleaned or _is_boilerplate(cleaned):
            continue
        # Prefer paragraphs that mention loans/programs when available
        if cleaned not in parts:
            parts.append(cleaned)
        if len(" ".join(parts)) >= max_len:
            break
    # Prefer loan-ish paragraphs first
    loanish = [p for p in parts if re.search(r"\b(loan|7\(a\)|504|microloan|financ|lender)\b", p, re.I)]
    if loanish:
        parts = loanish + [p for p in parts if p not in loanish]
    if len(" ".join(parts)) < 80:
        for h in parser.headings:
            if not _is_boilerplate(h) and h not in parts:
                parts.append(h)
            if len(" ".join(parts)) >= 120:
                break
    text = " ".join(parts).strip()
    if len(text) > max_len:
        text = text[: max_len - 1].rsplit(" ", 1)[0] + "…"
    return text


def _as_card(
    raw: Any,
    index: int = 0,
    *,
    source: str = "static",
    is_current: bool = False,
    retrieved_at: Optional[str] = None,
    default_type: str = "content",
) -> Optional[Dict[str, Any]]:
    """
    Normalize any SBA record into a UI card the prebuilt explorer can render.

    Prebuilt list row uses: title, summary, created|startDate, id
    Detail views also use: body, description, link, location, registrationLink, fileUrl
    """
    retrieved_at = retrieved_at or _now_iso()
    if raw is None:
        return None
    if not isinstance(raw, dict):
        text = str(raw).strip()
        if not text:
            return None
        raw = {"title": text[:120], "description": text}

    title = str(
        raw.get("title")
        or raw.get("name")
        or raw.get("label")
        or raw.get("award_title")
        or raw.get("firm")
        or ""
    ).strip()
    summary = str(
        raw.get("summary")
        or raw.get("description")
        or raw.get("teaser")
        or raw.get("abstract")
        or raw.get("body")
        or raw.get("message")
        or ""
    ).strip()
    description = str(
        raw.get("description") or raw.get("summary") or raw.get("body") or summary or ""
    ).strip()
    url = str(
        raw.get("url")
        or raw.get("link")
        or raw.get("href")
        or raw.get("registrationLink")
        or raw.get("fileUrl")
        or raw.get("award_link")
        or ""
    ).strip()

    if not title and url:
        title = (
            url.rstrip("/").split("/")[-1].replace("-", " ").replace("_", " ").title()
            or "SBA resource"
        )
    if not title and summary:
        title = summary[:80] + ("…" if len(summary) > 80 else "")
    if not summary and description:
        summary = description
    if not summary and title:
        summary = f"Official SBA resource: {title}" + (f" — {url}" if url else "")
    if not description and summary:
        description = summary
    if not title and not summary and not url:
        return None

    # Stable id (prefer existing; else deterministic hash)
    item_id = raw.get("id")
    if item_id in (None, ""):
        item_id = raw.get("nid") or raw.get("uuid")
    if item_id in (None, ""):
        item_id = abs(hash((title.lower(), url))) % (10**10) or (index + 1)

    body_html = str(raw.get("body") or "").strip()
    if not body_html:
        # Safe plain-text body so detail panes always have content
        safe = (
            description.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br/>")
        )
        body_html = f"<p>{safe}</p>"
        if url:
            body_html += f'<p><a href="{url}" target="_blank" rel="noopener">Open official source</a></p>'

    created = raw.get("created") or raw.get("changed") or raw.get("published") or retrieved_at
    start_date = raw.get("startDate") or raw.get("start_date") or raw.get("date") or created
    end_date = raw.get("endDate") or raw.get("end_date")
    location = raw.get("location") or raw.get("address") or "Online / see official page"
    item_type = str(raw.get("type") or default_type or "content")

    card = dict(raw)
    card.update(
        {
            "id": item_id,
            "nid": raw.get("nid") or item_id,
            "title": title,
            "name": raw.get("name") or title,
            "summary": summary,
            "description": description,
            "body": body_html,
            "url": url,
            "link": raw.get("link") or url,
            "fileUrl": raw.get("fileUrl") or (url if item_type in ("document", "form") else raw.get("fileUrl")),
            "registrationLink": raw.get("registrationLink") or (url if "event" in item_type else raw.get("registrationLink")),
            "created": created,
            "changed": raw.get("changed") or created,
            "startDate": start_date,
            "endDate": end_date,
            "location": location,
            "type": item_type,
            "source": raw.get("source") or source,
            "is_current": bool(raw["is_current"]) if "is_current" in raw else bool(is_current),
            "freshness": raw.get("freshness")
            or ("current" if (raw.get("is_current") if "is_current" in raw else is_current) else "not_current"),
            "retrieved_at": raw.get("retrieved_at") or retrieved_at,
            # List helper used by some clients
            "teaser": summary[:160],
        }
    )
    return card


def _normalize_page(
    items: List[Dict[str, Any]],
    page: int = 1,
    page_size: int = 20,
    source: str = "static",
    degraded: bool = False,
    message: Optional[str] = None,
    is_current: Optional[bool] = None,
    retrieved_at: Optional[str] = None,
) -> Dict[str, Any]:
    """
    is_current=True  → live SBA.gov / public API fetch (suitable for rendered UI as current)
    is_current=False → static fallback or RAG/KB (must not be presented as live SBA)
    """
    page = max(1, int(page or 1))
    page_size = max(1, min(int(page_size or 20), 50))
    retrieved_at = retrieved_at or _now_iso()
    if is_current is None:
        is_current = source in _LIVE_SOURCES and not degraded
        # HTML scrape is still "current" (live page) even if labeled degraded vs JSON API
        if source.startswith("sba_html"):
            is_current = True
        if source in ("static", "static_fallback", "rag", "local_kb_fallback"):
            is_current = False

    # Cardify full list before paging so every page is display-ready
    cards: List[Dict[str, Any]] = []
    for i, raw in enumerate(items or []):
        card = _as_card(
            raw,
            i,
            source=source,
            is_current=bool(is_current),
            retrieved_at=retrieved_at,
        )
        if card:
            cards.append(card)

    total = len(cards)
    total_pages = max(1, (total + page_size - 1) // page_size) if total else 0
    start = (page - 1) * page_size
    chunk = cards[start : start + page_size]

    out: Dict[str, Any] = {
        "items": chunk,
        "results": chunk,  # alias for older clients
        "total_pages": total_pages,
        "totalPages": total_pages,
        "currentPage": page,
        "count": total,
        "source": source,
        "degraded": degraded,
        "is_current": is_current,
        "freshness": "current" if is_current else "not_current",
        "retrieved_at": retrieved_at,
        # Policy flag for clients: non-RAG SBA UI should prefer is_current payloads
        "render_policy": "current_unless_rag",
    }
    if message:
        out["message"] = message
    if total == 0:
        out["message"] = message or "No SBA cards available for this query."
    return out


def _filter_items(items: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    q = (query or "").strip().lower()
    # Empty, *, or wildcard-only → return full catalog (populate cards)
    if not q or q in {"*", "%", "all", "any"}:
        return items
    tokens = [t for t in re.findall(r"[a-z0-9]{2,}", q) if t not in {"the", "and", "for", "sba"}]
    if not tokens:
        return items
    scored = []
    for item in items:
        blob = " ".join(
            str(item.get(k, "")) for k in ("title", "name", "description", "summary", "body", "url", "type")
        ).lower()
        score = sum(1 for t in tokens if t in blob)
        if score:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    # Prefer matches, but never empty the catalog — cards are the product surface
    return [i for _, i in scored] if scored else items


class SBAContentAPI:
    """
    Multi-source client for public SBA-related content.

    Consumption order per content type:
      1. Legacy JSON content search (if restored)
      2. Domain-specific public APIs (SBIR for innovation content)
      3. Official sba.gov HTML extract
      4. Curated static catalog grounded in official SBA program pages
    """

    LOAN_PAGES = {
        "7a": f"{SBA_SITE}/funding-programs/loans/7a-loans",
        "504": f"{SBA_SITE}/funding-programs/loans/504-loans",
        "microloans": f"{SBA_SITE}/funding-programs/loans/microloans",
        "loans_hub": f"{SBA_SITE}/funding-programs/loans",
    }

    def __init__(
        self,
        base_url: str = SBA_CONTENT_BASE,
        session: Optional[requests.Session] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        if SBA_API_KEY:
            self.session.headers["X-Api-Key"] = SBA_API_KEY
            self.session.headers["Authorization"] = f"Bearer {SBA_API_KEY}"

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------
    def _get_json(
        self,
        url: str,
        params: Optional[dict] = None,
        timeout: int = 12,
        force_fresh: bool = False,
    ) -> Any:
        cache_key = f"json:{url}?{urlencode(params or {}, doseq=True)}"
        if not force_fresh:
            cached = _cache_get(cache_key)
            if cached is not None:
                return cached
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            if response.status_code == 429:
                return {"error": "rate_limited", "status_code": 429, "success": False}
            response.raise_for_status()
            data = response.json()
            _cache_set(cache_key, data, ttl=_CACHE_TTL)
            return data
        except requests.RequestException as e:
            return {"error": str(e), "success": False}
        except ValueError as e:
            return {"error": f"invalid_json: {e}", "success": False}

    def _get_html(
        self,
        url: str,
        timeout: int = 15,
        force_fresh: bool = False,
    ) -> Optional[str]:
        cache_key = f"html:{url}"
        if not force_fresh:
            cached = _cache_get(cache_key)
            if cached is not None:
                return cached
        try:
            response = self.session.get(
                url,
                timeout=timeout,
                headers={**DEFAULT_HEADERS, "Accept": "text/html,application/xhtml+xml"},
            )
            response.raise_for_status()
            text = response.text
            # Keep live page HTML fresh (short TTL) so rendered SBA info stays current
            _cache_set(cache_key, text, ttl=_CACHE_TTL)
            return text
        except requests.RequestException as e:
            logger.warning("SBA HTML fetch failed %s: %s", url, e)
            return None

    def _parse_page(self, html: str) -> _PageContentParser:
        parser = _PageContentParser()
        try:
            parser.feed(html)
        except Exception as e:
            logger.warning("HTML parse failed: %s", e)
        return parser

    def _live_loan_program_cards(self, force_fresh: bool = False) -> List[Dict[str, Any]]:
        """
        Build loan program cards from *current* official SBA page text
        (meta description + lead paragraphs), not hard-coded program terms.
        """
        retrieved_at = _now_iso()
        programs = [
            ("7a", "SBA 7(a) loans", self.LOAN_PAGES["7a"]),
            ("504", "SBA 504 loans", self.LOAN_PAGES["504"]),
            ("microloans", "SBA Microloans", self.LOAN_PAGES["microloans"]),
            ("loans_hub", "SBA-backed loans overview", self.LOAN_PAGES["loans_hub"]),
        ]
        items: List[Dict[str, Any]] = []
        for pid, fallback_title, url in programs:
            html = self._get_html(url, force_fresh=force_fresh)
            if not html:
                continue
            parser = self._parse_page(html)
            title = fallback_title
            # Prefer first H1 when it looks like a page title
            for h in parser.headings[:3]:
                if "loan" in h.lower() or "7(a)" in h.lower() or "504" in h or "micro" in h.lower():
                    title = h
                    break
            if parser.title and "sba" in parser.title.lower():
                # e.g. "7(a) loans | U.S. Small Business Administration"
                t = parser.title.split("|")[0].strip()
                if t:
                    title = t
            description = _snippet_from_parser(parser)
            if not description:
                continue
            items.append(
                {
                    "id": pid,
                    "title": title,
                    "name": title,
                    "description": description,
                    "summary": description,
                    "url": url,
                    "type": "loan_program",
                    "source_page": url,
                    "is_current": True,
                    "freshness": "current",
                    "retrieved_at": retrieved_at,
                }
            )
        return items

    def _legacy_search(self, content_type: str, **params) -> Dict[str, Any]:
        url = f"{self.base_url}/{content_type}.json"
        return self._get_json(url, params)

    def _items_from_legacy(self, data: Any, page: int) -> Optional[Dict[str, Any]]:
        if not isinstance(data, dict) or data.get("error") or data.get("success") is False:
            return None
        items = data.get("results") or data.get("items") or data.get("data") or []
        if isinstance(data, list):
            items = data
        if not isinstance(items, list) or not items:
            # empty successful payload is still valid
            if isinstance(items, list):
                return _normalize_page(items, page=page, source="legacy_json", degraded=False)
            return None
        # normalize records
        norm = []
        for raw in items:
            if not isinstance(raw, dict):
                continue
            norm.append(
                {
                    "id": raw.get("id") or raw.get("nid") or raw.get("uuid"),
                    "title": raw.get("title") or raw.get("name") or raw.get("label") or "Untitled",
                    "description": raw.get("summary")
                    or raw.get("description")
                    or raw.get("teaser")
                    or "",
                    "url": raw.get("url") or raw.get("path") or raw.get("link") or "",
                    "type": raw.get("type") or raw.get("bundle") or "content",
                    "raw": raw,
                }
            )
        return _normalize_page(
            norm,
            page=page,
            source="legacy_json",
            degraded=False,
            message=None if norm else "Legacy content API returned no rows",
        )

    # ------------------------------------------------------------------
    # Static / curated catalogs (grounded in official SBA pages)
    # ------------------------------------------------------------------
    def _static_loan_items(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "7a",
                "title": "SBA 7(a) loans",
                "name": "SBA 7(a) loans",
                "description": (
                    "Primary SBA loan program for working capital, equipment, real estate, "
                    "and business acquisition. Max generally $5 million. Terms up to 25 years "
                    "for real estate. Source: sba.gov/funding-programs/loans/7a-loans"
                ),
                "url": self.LOAN_PAGES["7a"],
                "type": "loan_program",
            },
            {
                "id": "504",
                "title": "SBA 504 loans",
                "name": "SBA 504 loans",
                "description": (
                    "Long-term, fixed-rate financing for major fixed assets such as real estate "
                    "and heavy equipment. Typical structure: bank + CDC/SBA + borrower equity. "
                    "Source: sba.gov/funding-programs/loans/504-loans"
                ),
                "url": self.LOAN_PAGES["504"],
                "type": "loan_program",
            },
            {
                "id": "microloans",
                "title": "SBA Microloans",
                "name": "SBA Microloans",
                "description": (
                    "Small loans up to $50,000 delivered through nonprofit intermediary lenders "
                    "for startups and existing small businesses. "
                    "Source: sba.gov/funding-programs/loans/microloans"
                ),
                "url": self.LOAN_PAGES["microloans"],
                "type": "loan_program",
            },
            {
                "id": "express",
                "title": "SBA Express / faster 7(a) options",
                "name": "SBA Express",
                "description": (
                    "Expedited processing options under the 7(a) family for smaller loans with "
                    "faster lender decisions. See 7(a) loan page for current product variants."
                ),
                "url": self.LOAN_PAGES["7a"],
                "type": "loan_program",
            },
            {
                "id": "working-capital",
                "title": "Working capital financing",
                "name": "Working capital",
                "description": (
                    "SBA-backed options can fund inventory, payroll, and day-to-day operations. "
                    "Discussed on the SBA loans hub as a common use case."
                ),
                "url": self.LOAN_PAGES["loans_hub"],
                "type": "use_case",
            },
            {
                "id": "fixed-assets",
                "title": "Fixed asset financing",
                "name": "Fixed assets",
                "description": (
                    "Purchase or improve real estate, machinery, and equipment — often via 504 "
                    "or longer-term 7(a) structures."
                ),
                "url": self.LOAN_PAGES["loans_hub"],
                "type": "use_case",
            },
        ]

    def _static_office_items(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "sba-locations",
                "title": "SBA locations & district offices",
                "description": "Find SBA district offices and contact points across the U.S.",
                "url": f"{SBA_SITE}/about-sba/sba-locations",
                "type": "office_directory",
            },
            {
                "id": "local-assistance",
                "title": "Local assistance finder",
                "description": "Find SBDCs, SCORE, WBCs, VBOCs and other free counseling partners.",
                "url": f"{SBA_SITE}/local-assistance/find",
                "type": "assistance",
            },
            {
                "id": "lender-match",
                "title": "Lender Match",
                "description": "Connect with SBA-approved lenders for financing options.",
                "url": f"{SBA_SITE}/funding-programs/loans/lender-match",
                "type": "lender_tool",
            },
        ]

    def _static_article_like(self) -> List[Dict[str, Any]]:
        # Core business-guide style topics linked to live sba.gov pages
        guides = [
            ("Plan your business", f"{SBA_SITE}/business-guide/plan-your-business"),
            ("Launch your business", f"{SBA_SITE}/business-guide/launch-your-business"),
            ("Manage your business", f"{SBA_SITE}/business-guide/manage-your-business"),
            ("Grow your business", f"{SBA_SITE}/business-guide/grow-your-business"),
            ("Fund your business", f"{SBA_SITE}/business-guide/grow-your-business/fund-your-business"),
            ("SBA loans overview", self.LOAN_PAGES["loans_hub"]),
            ("7(a) loans guide", self.LOAN_PAGES["7a"]),
            ("504 loans guide", self.LOAN_PAGES["504"]),
            ("Microloans guide", self.LOAN_PAGES["microloans"]),
            ("Federal contracting", f"{SBA_SITE}/federal-contracting"),
            ("Disaster assistance", f"{SBA_SITE}/funding-programs/disaster-assistance"),
            ("Counseling & training", f"{SBA_SITE}/local-assistance"),
        ]
        items = []
        for i, (title, url) in enumerate(guides, start=1):
            items.append(
                {
                    "id": f"guide-{i}",
                    "title": title,
                    "description": f"Official SBA resource: {title}",
                    "url": url,
                    "type": "guide",
                }
            )
        return items

    # ------------------------------------------------------------------
    # HTML extractors
    # ------------------------------------------------------------------
    def _extract_from_html_pages(
        self,
        urls: List[str],
        item_type: str,
        query: str = "",
        page: int = 1,
        force_fresh: bool = False,
    ) -> Optional[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        seen = set()
        retrieved_at = _now_iso()
        page_summaries: List[Dict[str, Any]] = []

        for url in urls:
            html = self._get_html(url, force_fresh=force_fresh)
            if not html:
                continue
            parser = self._parse_page(html)
            page_snippet = _snippet_from_parser(parser)

            # One current page-level card from live meta/lead text
            if page_snippet:
                page_title = parser.title.split("|")[0].strip() if parser.title else url.rstrip("/").split("/")[-1]
                for h in parser.headings[:2]:
                    if len(h) > 8 and "navigation" not in h.lower():
                        page_title = h
                        break
                page_summaries.append(
                    {
                        "id": abs(hash(("page", url))) % (10**10),
                        "title": page_title,
                        "description": page_snippet,
                        "summary": page_snippet,
                        "url": url,
                        "type": item_type,
                        "source_page": url,
                        "is_current": True,
                        "freshness": "current",
                        "retrieved_at": retrieved_at,
                    }
                )

            for link in parser.links:
                title = link["title"]
                href = urljoin(SBA_SITE, link["href"])
                if "sba.gov" not in href:
                    continue
                low = title.lower()
                if low in {
                    "home", "menu", "search", "skip to main content",
                    "primary navigation", "footer navigation", "breadcrumb",
                    "login", "sign in", "share", "print",
                }:
                    continue
                if len(title) < 4 or len(title) > 160:
                    continue
                key = (title.lower(), href.rstrip("/"))
                if key in seen:
                    continue
                seen.add(key)
                # Prefer live page snippet when link is the same page section
                desc = page_snippet if page_snippet and href.rstrip("/") == url.rstrip("/") else (
                    f"Current link on sba.gov — open source for full official details."
                )
                items.append(
                    {
                        "id": abs(hash(key)) % (10**10),
                        "title": title,
                        "description": desc,
                        "summary": desc,
                        "url": href,
                        "type": item_type,
                        "source_page": url,
                        "is_current": True,
                        "freshness": "current",
                        "retrieved_at": retrieved_at,
                    }
                )

        # Put full-page current summaries first (best for rendered UI)
        merged = page_summaries + items
        if not merged:
            return None
        merged = _filter_items(merged, query)
        return _normalize_page(
            merged,
            page=page,
            source="sba_html",
            degraded=False,
            is_current=True,
            retrieved_at=retrieved_at,
            message="Live content extracted from official sba.gov pages.",
        )

    # ------------------------------------------------------------------
    # SBIR public API
    # ------------------------------------------------------------------
    def search_sbir_awards(
        self,
        query: str = "",
        agency: Optional[str] = None,
        year: Optional[int] = None,
        firm: Optional[str] = None,
        rows: int = 20,
        start: int = 0,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        Consume SBIR/STTR awards API.
        Docs: https://www.sbir.gov/api
        Example: https://api.www.sbir.gov/public/api/awards?agency=DOE&year=2010&rows=100
        """
        params: Dict[str, Any] = {
            "rows": max(1, min(rows, 100)),
            "start": max(0, start if start else (max(page, 1) - 1) * rows),
        }
        if agency:
            params["agency"] = agency
        if year:
            params["year"] = year
        if firm:
            params["firm"] = firm
        # Free-text: map to firm search when query looks like a company, else no filter
        if query and not firm and not agency:
            params["firm"] = query

        data = self._get_json(f"{SBIR_API_BASE}/awards", params=params, timeout=20)
        if isinstance(data, dict) and data.get("error"):
            # Always populate cards — rate limits must not empty the UI
            return _normalize_page(
                _filter_items(self._static_sbir_items(), query),
                page=page,
                source="static",
                degraded=True,
                is_current=False,
                message=f"SBIR API unavailable ({data.get('error')}); showing official SBIR resource cards.",
            )

        rows_data = data if isinstance(data, list) else data.get("awards") or data.get("results") or []
        items = []
        for raw in rows_data if isinstance(rows_data, list) else []:
            if not isinstance(raw, dict):
                continue
            items.append(
                {
                    "id": raw.get("contract") or raw.get("agency_tracking_number"),
                    "title": raw.get("award_title") or raw.get("title") or "SBIR Award",
                    "description": (raw.get("abstract") or "")[:500],
                    "summary": (raw.get("abstract") or raw.get("award_title") or "SBIR award")[:240],
                    "url": raw.get("award_link") or "https://www.sbir.gov/awards",
                    "type": "sbir_award",
                    "agency": raw.get("agency"),
                    "firm": raw.get("firm"),
                    "phase": raw.get("phase"),
                    "program": raw.get("program"),
                    "award_amount": raw.get("award_amount"),
                    "award_year": raw.get("award_year"),
                    "raw": raw,
                }
            )
        items = _filter_items(items, query) if query and "firm" not in params else items
        if not items:
            return _normalize_page(
                _filter_items(self._static_sbir_items(), query),
                page=page,
                source="static",
                degraded=True,
                is_current=False,
                message="SBIR API returned no awards; showing official SBIR resource cards.",
            )
        return _normalize_page(
            items,
            page=page,
            page_size=params["rows"],
            source="sbir",
            degraded=False,
            is_current=True,
            message=None,
        )

    def get_content_detail(self, content_type: str, item_id: Any) -> Dict[str, Any]:
        """
        Resolve a single card by id for prebuilt SPA detail clicks:
        GET /api/sba-content/{type}/{id}
        """
        content_type = (content_type or "").strip().lower()
        target = str(item_id).strip()
        searchers = {
            "articles": self.search_articles,
            "blogs": self.search_blogs,
            "courses": self.search_courses,
            "documents": self.search_documents,
            "events": self.search_events,
            "offices": self.search_offices,
            "loans": self.search_loans,
            "lenders": self.search_lenders,
            "sbir": lambda **kw: self.search_sbir_awards(query=kw.get("query") or "", page=kw.get("page") or 1),
        }
        search_fn = searchers.get(content_type)
        if not search_fn:
            return {"error": f"Unknown content type: {content_type}", "success": False}

        # Pull a large page of cards and find id match (also match title slug)
        try:
            result = search_fn(query="", page=1)
        except TypeError:
            result = search_fn()
        except Exception as e:
            logger.error("get_content_detail search failed: %s", e)
            result = {"items": []}

        items = []
        if isinstance(result, dict):
            items = result.get("items") or result.get("results") or []
        # Also scan static catalogs when search is paginated
        for item in items:
            if str(item.get("id")) == target or str(item.get("nid")) == target:
                card = _as_card(item, source=result.get("source") or "sba", is_current=bool(result.get("is_current")))
                if card:
                    card["success"] = True
                    return card

        # Wider scan: extra static catalogs
        extras: List[Dict[str, Any]] = []
        if content_type in ("articles", "blogs"):
            extras = self._static_article_like()
        elif content_type == "courses":
            extras = self._static_course_items()
        elif content_type == "documents":
            extras = self._static_document_items()
        elif content_type == "events":
            extras = self._static_event_items()
        elif content_type == "lenders":
            extras = self._static_lender_items()
        elif content_type == "loans":
            extras = self._static_loan_items()
        elif content_type == "offices":
            extras = self._static_office_items()
        elif content_type == "sbir":
            extras = self._static_sbir_items()

        for item in extras:
            if str(item.get("id")) == target:
                card = _as_card(item, source="static", is_current=False)
                if card:
                    card["success"] = True
                    return card

        # Last resort: build a card so the detail pane is never empty
        return _as_card(
            {
                "id": target,
                "title": f"SBA {content_type} resource",
                "summary": f"Details for {content_type} item {target}. Open sba.gov for the latest official information.",
                "description": f"Details for {content_type} item {target}. Open sba.gov for the latest official information.",
                "url": f"{SBA_SITE}/",
                "type": content_type.rstrip("s") if content_type.endswith("s") else content_type,
            },
            source="static",
            is_current=False,
        ) or {"error": "Not found", "success": False}

    # ------------------------------------------------------------------
    # Public search methods used by routes
    # ------------------------------------------------------------------
    def search_articles(self, **params) -> Dict[str, Any]:
        page = int(params.get("page") or 1)
        query = params.get("query") or params.get("q") or ""

        legacy = self._items_from_legacy(self._legacy_search("articles", **params), page)
        if legacy and legacy.get("items") is not None and not legacy.get("degraded"):
            return legacy

        curated = self._static_article_like()
        html = self._extract_from_html_pages(
            [
                f"{SBA_SITE}/business-guide",
                f"{SBA_SITE}/funding-programs/loans",
                f"{SBA_SITE}/federal-contracting",
            ],
            item_type="article",
            query=query,
            page=1,
        )
        extra = html.get("items") if isinstance(html, dict) else None
        items = self._merge_cards(curated, extra or [])
        live = bool(extra)
        return _normalize_page(
            _filter_items(items, query),
            page=page,
            source="sba_html" if live else "static",
            degraded=not live,
            is_current=True if live else False,
            message="Article/guide cards from official SBA business-guide pages.",
        )

    def get_article(self, article_id: int) -> Dict[str, Any]:
        legacy = self._get_json(f"{self.base_url}/articles/{article_id}.json")
        if isinstance(legacy, dict) and not legacy.get("error"):
            card = _as_card(legacy, source="legacy_json", is_current=True)
            if card:
                card["success"] = True
                return card
        detail = self.get_content_detail("articles", article_id)
        if detail and not detail.get("error"):
            return detail
        return {"error": "Article not found", "success": False}

    def search_blogs(self, **params) -> Dict[str, Any]:
        page = int(params.get("page") or 1)
        query = params.get("query") or params.get("q") or ""

        legacy = self._items_from_legacy(self._legacy_search("blogs", **params), page)
        if legacy and legacy.get("items"):
            return legacy

        curated = [
            {
                "id": "blog-hub",
                "title": "SBA blog",
                "description": "Official SBA blog posts and small-business stories.",
                "url": f"{SBA_SITE}/blog",
                "type": "blog",
            },
            {
                "id": "newsroom",
                "title": "SBA newsroom",
                "description": "Press releases and media advisories from the SBA.",
                "url": f"{SBA_SITE}/about-sba/sba-newsroom/press-releases-media-advisories",
                "type": "blog",
            },
            {
                "id": "funding-news",
                "title": "Funding program updates",
                "description": "Current financing program information for small businesses.",
                "url": f"{SBA_SITE}/funding-programs/loans",
                "type": "blog",
            },
        ] + self._static_article_like()[:5]
        html = self._extract_from_html_pages(
            [f"{SBA_SITE}/blog", f"{SBA_SITE}/about-sba/sba-newsroom/press-releases-media-advisories"],
            item_type="blog",
            query=query,
            page=1,
        )
        extra = html.get("items") if isinstance(html, dict) else None
        items = self._merge_cards(curated, extra or [])
        live = bool(extra)
        return _normalize_page(
            _filter_items(items, query),
            page=page,
            source="sba_html" if live else "static",
            degraded=not live,
            is_current=bool(live),
            message="Blog/news cards from official SBA newsroom and blog pages.",
        )

    def get_blog(self, blog_id: int) -> Dict[str, Any]:
        legacy = self._get_json(f"{self.base_url}/blogs/{blog_id}.json")
        if isinstance(legacy, dict) and not legacy.get("error"):
            return legacy
        return {"error": "Blog not found", "success": False}

    def search_contacts(self, **params) -> Any:
        return self._legacy_search("contacts", **params)

    # Shared site chrome / promo titles that pollute multi-page scrapes
    _NOISE_TITLES = frozenset({
        "freedom 250 small business pledge",
        "sign up now to get your free certificate.",
        "sign up now to get your free certificate",
        "explore our business guide",
        "share sensitive information only on official, secure websites",
        "skip to main content",
        "primary navigation",
        "footer navigation",
        "sba",
        "u.s. small business administration",
    })

    def _is_noise_card(self, raw: Dict[str, Any]) -> bool:
        title = str(raw.get("title") or raw.get("name") or "").strip().lower()
        if not title:
            return True
        if title in self._NOISE_TITLES:
            return True
        # Generic repeated promos
        if "freedom 250" in title or title.startswith("sign up now"):
            return True
        return False

    def _merge_cards(
        self,
        primary: List[Dict[str, Any]],
        secondary: List[Dict[str, Any]],
        *,
        limit: int = 40,
    ) -> List[Dict[str, Any]]:
        """Primary cards first (curated), then unique secondary (live scrape) by title/url."""
        out: List[Dict[str, Any]] = []
        seen_titles = set()
        seen_urls = set()
        for raw in list(primary or []) + list(secondary or []):
            if not isinstance(raw, dict):
                continue
            if self._is_noise_card(raw):
                continue
            title = str(raw.get("title") or raw.get("name") or "").strip().lower()
            url = str(raw.get("url") or raw.get("link") or "").rstrip("/").lower()
            if not title and not url:
                continue
            # Dedupe by title OR url so the same promo isn't repeated 20 times
            if title and title in seen_titles:
                continue
            if url and url in seen_urls:
                continue
            if title:
                seen_titles.add(title)
            if url:
                seen_urls.add(url)
            out.append(raw)
            if len(out) >= limit:
                break
        return out

    def search_courses(self, **params) -> Any:
        page = int(params.get("page") or 1)
        query = params.get("query") or ""
        legacy = self._items_from_legacy(self._legacy_search("courses", **params), page)
        if legacy and legacy.get("items"):
            return legacy

        curated = self._static_course_items()
        html = self._extract_from_html_pages(
            [
                f"{SBA_SITE}/sba-learning-platform",
                f"{SBA_SITE}/local-assistance",
                f"{SBA_SITE}/business-guide",
            ],
            item_type="course",
            query=query,
            page=1,
        )
        extra = html.get("items") if isinstance(html, dict) else None
        items = self._merge_cards(curated, extra or [])
        live = bool(extra)
        return _normalize_page(
            _filter_items(items, query),
            page=page,
            source="sba_html" if live else "static",
            degraded=not live,
            is_current=live,
            message=(
                "Course cards from official SBA learning resources"
                + (" plus live sba.gov links." if live else ".")
            ),
        )

    def get_course(self, pathname: str) -> Any:
        detail = self.get_content_detail("courses", pathname)
        if detail and not detail.get("error"):
            return detail
        return self._get_json(f"{self.base_url}/course.json", {"pathname": pathname})

    def search_documents(self, **params) -> Any:
        page = int(params.get("page") or 1)
        query = params.get("query") or ""
        legacy = self._items_from_legacy(self._legacy_search("documents", **params), page)
        if legacy and legacy.get("items"):
            return legacy
        curated = self._static_document_items()
        html = self._extract_from_html_pages(
            [f"{SBA_SITE}/document", f"{SBA_SITE}/funding-programs/loans"],
            item_type="document",
            query=query,
            page=1,
        )
        extra = html.get("items") if isinstance(html, dict) else None
        items = self._merge_cards(curated, extra or [])
        live = bool(extra)
        return _normalize_page(
            _filter_items(items, query),
            page=page,
            source="sba_html" if live else "static",
            degraded=not live,
            is_current=live,
            message="Document cards from official SBA forms/program pages.",
        )

    def search_events(self, **params) -> Any:
        page = int(params.get("page") or 1)
        query = params.get("query") or ""
        legacy = self._items_from_legacy(self._legacy_search("events", **params), page)
        if legacy and legacy.get("items"):
            return legacy

        curated = self._static_event_items()
        html = self._extract_from_html_pages(
            [
                f"{SBA_SITE}/events",
                f"{SBA_SITE}/local-assistance/find",
                f"{SBA_SITE}/about-sba/sba-newsroom",
            ],
            item_type="event",
            query=query,
            page=1,
        )
        extra = html.get("items") if isinstance(html, dict) else None
        items = self._merge_cards(curated, extra or [])
        live = bool(extra)
        return _normalize_page(
            _filter_items(items, query),
            page=page,
            source="sba_html" if live else "static",
            degraded=not live,
            is_current=live,
            message="Event cards from official SBA events and partner training pages.",
        )

    def search_lenders(self, **params) -> Any:
        page = int(params.get("page") or 1)
        query = params.get("query") or ""
        legacy = self._items_from_legacy(self._legacy_search("lenders", **params), page)
        if legacy and legacy.get("items"):
            return legacy
        items = self._static_lender_items()
        return _normalize_page(
            _filter_items(items, query),
            page=page,
            source="static",
            degraded=True,
            message="Lenders API unavailable; showing Lender Match and financing partner cards.",
        )

    def _static_course_items(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "learning-center",
                "title": "SBA Learning Platform",
                "summary": "Free self-paced courses for starting, managing, and growing a small business.",
                "description": "Access free online courses covering business planning, funding, marketing, and more.",
                "url": f"{SBA_SITE}/sba-learning-platform",
                "link": f"{SBA_SITE}/sba-learning-platform",
                "type": "course",
            },
            {
                "id": "plan-course",
                "title": "Plan your business courses",
                "summary": "Market research, business plans, and startup fundamentals.",
                "description": "Official SBA business-guide learning path for planning a venture.",
                "url": f"{SBA_SITE}/business-guide/plan-your-business",
                "type": "course",
            },
            {
                "id": "fund-course",
                "title": "Fund your business courses",
                "summary": "How SBA loans, investors, and grants fit different stages.",
                "description": "Learning content tied to SBA funding programs and Lender Match.",
                "url": f"{SBA_SITE}/business-guide/grow-your-business/fund-your-business",
                "type": "course",
            },
            {
                "id": "launch-course",
                "title": "Launch your business courses",
                "summary": "Registration, licenses, and first-customer readiness.",
                "url": f"{SBA_SITE}/business-guide/launch-your-business",
                "type": "course",
            },
            {
                "id": "manage-course",
                "title": "Manage your business courses",
                "summary": "Employees, taxes, insurance, and day-to-day operations.",
                "url": f"{SBA_SITE}/business-guide/manage-your-business",
                "type": "course",
            },
            {
                "id": "contracting-course",
                "title": "Federal contracting basics",
                "summary": "Learn how small businesses sell to the government.",
                "url": f"{SBA_SITE}/federal-contracting",
                "type": "course",
            },
            {
                "id": "score-mentoring",
                "title": "SCORE mentoring & workshops",
                "summary": "Free mentoring and workshops through SCORE partners.",
                "url": f"{SBA_SITE}/local-assistance/find",
                "type": "course",
            },
            {
                "id": "sbdc-training",
                "title": "SBDC local training",
                "summary": "Small Business Development Centers offer free/low-cost classes nearby.",
                "url": f"{SBA_SITE}/local-assistance/find",
                "type": "course",
            },
        ]

    def _static_document_items(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "forms",
                "title": "SBA forms library",
                "summary": "Download official SBA forms used for lending and programs.",
                "description": "Browse current SBA forms and instructions.",
                "url": f"{SBA_SITE}/document",
                "fileUrl": f"{SBA_SITE}/document",
                "type": "document",
            },
            {
                "id": "sop",
                "title": "Standard Operating Procedures (SOPs)",
                "summary": "Policy manuals that govern SBA loan and program delivery.",
                "url": f"{SBA_SITE}/document",
                "fileUrl": f"{SBA_SITE}/document",
                "type": "document",
            },
            {
                "id": "7a-docs",
                "title": "7(a) loan program documentation",
                "summary": "Eligibility, uses of proceeds, and lender guidance for 7(a).",
                "url": f"{SBA_SITE}/funding-programs/loans/7a-loans",
                "type": "document",
            },
            {
                "id": "504-docs",
                "title": "504 loan program documentation",
                "summary": "CDC/504 fixed-asset financing requirements and structure.",
                "url": f"{SBA_SITE}/funding-programs/loans/504-loans",
                "type": "document",
            },
            {
                "id": "microloan-docs",
                "title": "Microloan program documentation",
                "summary": "Intermediary microloan rules and borrower guidance.",
                "url": f"{SBA_SITE}/funding-programs/loans/microloans",
                "type": "document",
            },
            {
                "id": "size-standards",
                "title": "Size standards documentation",
                "summary": "How SBA defines a small business by industry.",
                "url": f"{SBA_SITE}/size-standards",
                "type": "document",
            },
            {
                "id": "disaster-docs",
                "title": "Disaster assistance forms & guides",
                "summary": "Documents for disaster loan applicants and survivors.",
                "url": f"{SBA_SITE}/funding-programs/disaster-assistance",
                "type": "document",
            },
            {
                "id": "contracting-docs",
                "title": "Contracting certification guides",
                "summary": "8(a), HUBZone, WOSB, and SDVOSB program documentation.",
                "url": f"{SBA_SITE}/federal-contracting",
                "type": "document",
            },
        ]

    def _static_event_items(self) -> List[Dict[str, Any]]:
        now = _now_iso()
        return [
            {
                "id": "events-hub",
                "title": "SBA events calendar",
                "summary": "National webinars, workshops, and training listed on sba.gov/events.",
                "description": "Browse upcoming SBA-hosted and partner events, filter by topic, and register online.",
                "url": f"{SBA_SITE}/events",
                "registrationLink": f"{SBA_SITE}/events",
                "location": "Online & local",
                "startDate": now,
                "type": "event",
            },
            {
                "id": "local-assistance-events",
                "title": "Local counseling & training events",
                "summary": "SBDC, SCORE, WBC, and VBOC workshops near you.",
                "description": "Use the local assistance finder to discover partner-hosted classes and events.",
                "url": f"{SBA_SITE}/local-assistance/find",
                "registrationLink": f"{SBA_SITE}/local-assistance/find",
                "location": "Local partners",
                "startDate": now,
                "type": "event",
            },
            {
                "id": "lender-match-webinars",
                "title": "Financing readiness webinars",
                "summary": "Sessions that help owners prepare for Lender Match and SBA loans.",
                "url": f"{SBA_SITE}/funding-programs/loans/lender-match",
                "registrationLink": f"{SBA_SITE}/funding-programs/loans/lender-match",
                "location": "Online",
                "startDate": now,
                "type": "event",
            },
            {
                "id": "contracting-events",
                "title": "Government contracting events",
                "summary": "Matchmaking and training for federal contractors.",
                "url": f"{SBA_SITE}/federal-contracting",
                "location": "Online & regional",
                "startDate": now,
                "type": "event",
            },
            {
                "id": "export-events",
                "title": "Export & trade workshops",
                "summary": "International trade counseling events and webinars.",
                "url": f"{SBA_SITE}/business-guide/grow-your-business/export-products",
                "location": "Online",
                "startDate": now,
                "type": "event",
            },
            {
                "id": "disaster-briefings",
                "title": "Disaster recovery briefings",
                "summary": "Community briefings after declared disasters.",
                "url": f"{SBA_SITE}/funding-programs/disaster-assistance",
                "location": "Affected regions",
                "startDate": now,
                "type": "event",
            },
            {
                "id": "newsroom-events",
                "title": "SBA newsroom announcements",
                "summary": "Press events and program rollout announcements.",
                "url": f"{SBA_SITE}/about-sba/sba-newsroom",
                "location": "Online",
                "startDate": now,
                "type": "event",
            },
            {
                "id": "women-entrepreneurs",
                "title": "Women entrepreneur events",
                "summary": "WBC network events and national campaigns for women-owned firms.",
                "url": f"{SBA_SITE}/local-assistance/find",
                "location": "Local WBCs",
                "startDate": now,
                "type": "event",
            },
        ]

    def _static_lender_items(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "lender-match",
                "title": "Lender Match",
                "summary": "Official SBA tool that matches your financing needs to participating lenders.",
                "description": "Answer a short questionnaire and get connected with SBA lenders interested in your request.",
                "url": f"{SBA_SITE}/funding-programs/loans/lender-match",
                "type": "lender_tool",
            },
            {
                "id": "7a-lenders",
                "title": "7(a) participating lenders",
                "summary": "Community banks and CDFIs that deliver SBA 7(a) loans.",
                "url": f"{SBA_SITE}/funding-programs/loans/7a-loans",
                "type": "lender",
            },
            {
                "id": "504-cdc",
                "title": "504 Certified Development Companies",
                "summary": "CDCs partner with banks on fixed-asset 504 projects.",
                "url": f"{SBA_SITE}/funding-programs/loans/504-loans",
                "type": "lender",
            },
            {
                "id": "microloan-intermediaries",
                "title": "Microloan intermediaries",
                "summary": "Nonprofit lenders offering microloans up to $50,000 plus technical assistance.",
                "url": f"{SBA_SITE}/funding-programs/loans/microloans",
                "type": "lender",
            },
            {
                "id": "community-advantage",
                "title": "Mission-oriented lenders",
                "summary": "Lenders focused on underserved markets and smaller loan sizes.",
                "url": f"{SBA_SITE}/funding-programs/loans",
                "type": "lender",
            },
            {
                "id": "export-lenders",
                "title": "Export financing lenders",
                "summary": "SBA export working capital and international trade loan specialists.",
                "url": f"{SBA_SITE}/funding-programs/loans",
                "type": "lender",
            },
        ]

    def _static_sbir_items(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "sbir-overview",
                "title": "SBIR / STTR overview",
                "summary": "America’s Seed Fund for small business R&D — Phase I/II awards across federal agencies.",
                "url": "https://www.sbir.gov",
                "type": "sbir",
            },
            {
                "id": "sbir-solicitations",
                "title": "Current solicitations",
                "summary": "Browse open SBIR/STTR topics and agency solicitations.",
                "url": "https://www.sbir.gov/solicitations",
                "type": "sbir",
            },
            {
                "id": "sbir-awards",
                "title": "Award search",
                "summary": "Search historical SBIR/STTR awards by firm, agency, or keyword.",
                "url": "https://www.sbir.gov/awards",
                "type": "sbir",
            },
            {
                "id": "sbir-tutorials",
                "title": "How to apply tutorials",
                "summary": "Learn proposal basics, registration (SAM, SBIR.gov), and agency differences.",
                "url": "https://www.sbir.gov/tutorials",
                "type": "sbir",
            },
            {
                "id": "sba-innovation",
                "title": "SBA innovation programs",
                "summary": "SBA resources related to R&D and commercialization.",
                "url": f"{SBA_SITE}/funding-programs",
                "type": "sbir",
            },
            {
                "id": "sbir-events",
                "title": "SBIR events & road tours",
                "summary": "Agency outreach events for innovators and researchers.",
                "url": "https://www.sbir.gov/events",
                "type": "sbir",
            },
        ]

    def search_offices(self, **params) -> Any:
        page = int(params.get("page") or 1)
        query = params.get("query") or ""
        legacy = self._items_from_legacy(self._legacy_search("offices", **params), page)
        if legacy and legacy.get("items"):
            return legacy

        curated = self._static_office_items()
        html = self._extract_from_html_pages(
            [f"{SBA_SITE}/about-sba/sba-locations", f"{SBA_SITE}/local-assistance/find"],
            item_type="office",
            query=query,
            page=1,
        )
        extra = html.get("items") if isinstance(html, dict) else None
        items = self._merge_cards(curated, extra or [])
        live = bool(extra)
        return _normalize_page(
            _filter_items(items, query),
            page=page,
            source="sba_html" if live else "static",
            degraded=not live,
            is_current=bool(live),
            message="Office/local-help cards from official SBA location pages.",
        )

    def get_node(self, node_id: int) -> Any:
        return self._get_json(f"{self.base_url}/node.json", {"id": node_id})

    def search_taxonomys(self, **params) -> Any:
        return self._legacy_search("taxonomys", **params)

    def search_loans(self, **params) -> Dict[str, Any]:
        """
        Loan program catalog for rendered UI.

        Policy: use *current* official page text only when live fetch succeeds.
        Hard-coded program blurbs are last-resort and marked is_current=false
        (RAG/static — not for primary SBA rendering).
        """
        page = int(params.get("page") or 1)
        query = params.get("query") or params.get("q") or ""
        force_fresh = bool(params.get("fresh") or params.get("force_fresh"))

        # 1) Live program cards built from current sba.gov page copy
        live_cards = self._live_loan_program_cards(force_fresh=force_fresh)
        live_cards = _filter_items(live_cards, query)

        # 2) Additional current links from the loans hub
        hub = self._extract_from_html_pages(
            [self.LOAN_PAGES["loans_hub"]],
            item_type="loan",
            query=query,
            page=1,
            force_fresh=force_fresh,
        )
        extra = []
        if hub and hub.get("items"):
            known = {c.get("url", "").rstrip("/") for c in live_cards}
            for item in hub["items"]:
                u = (item.get("url") or "").rstrip("/")
                if u and u not in known:
                    extra.append(item)

        if live_cards:
            merged = live_cards + extra
            return _normalize_page(
                merged,
                page=page,
                source="sba_html",
                degraded=False,
                is_current=True,
                message="Current loan program text retrieved from official sba.gov pages.",
            )

        # 3) Static only if live pages unreachable — explicitly not current
        static_items = _filter_items(self._static_loan_items(), query)
        for item in static_items:
            item["is_current"] = False
            item["freshness"] = "not_current"
            item["description"] = (
                f"[Offline fallback — may be outdated] {item.get('description', '')}"
            )
        return _normalize_page(
            static_items,
            page=page,
            source="static",
            degraded=True,
            is_current=False,
            message=(
                "Live sba.gov pages unreachable. Showing offline fallback only "
                "(not current). Retry with ?fresh=1 when online."
            ),
        )

    def get_source_status(self) -> Dict[str, Any]:
        """Health snapshot of external public sources."""
        status = {
            "legacy_content_api": {"base": self.base_url, "ok": False},
            "sbir_api": {"base": SBIR_API_BASE, "ok": False},
            "sba_html": {"base": SBA_SITE, "ok": False},
            "api_key_configured": bool(SBA_API_KEY),
        }
        # Lightweight probes (short timeout)
        try:
            r = self.session.get(f"{self.base_url}/articles.json", params={"page": 1}, timeout=6)
            status["legacy_content_api"]["status_code"] = r.status_code
            status["legacy_content_api"]["ok"] = r.status_code == 200
        except requests.RequestException as e:
            status["legacy_content_api"]["error"] = str(e)

        try:
            r = self.session.get(f"{SBIR_API_BASE}/awards", params={"rows": 1}, timeout=8)
            status["sbir_api"]["status_code"] = r.status_code
            status["sbir_api"]["ok"] = r.status_code == 200
        except requests.RequestException as e:
            status["sbir_api"]["error"] = str(e)

        try:
            r = self.session.get(self.LOAN_PAGES["loans_hub"], timeout=8)
            status["sba_html"]["status_code"] = r.status_code
            status["sba_html"]["ok"] = r.status_code == 200
        except requests.RequestException as e:
            status["sba_html"]["error"] = str(e)

        return status

    # Back-compat private name used earlier
    def _get(self, url: str, params: Optional[dict] = None) -> Any:
        return self._get_json(url, params)
