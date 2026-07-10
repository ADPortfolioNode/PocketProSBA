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
    total = len(items)
    total_pages = max(1, (total + page_size - 1) // page_size) if total else 0
    start = (page - 1) * page_size
    retrieved_at = retrieved_at or _now_iso()
    if is_current is None:
        is_current = source in _LIVE_SOURCES and not degraded
        # HTML scrape is still "current" (live page) even if labeled degraded vs JSON API
        if source.startswith("sba_html"):
            is_current = True
        if source in ("static", "static_fallback", "rag", "local_kb_fallback"):
            is_current = False

    chunk = []
    for raw in items[start : start + page_size]:
        item = dict(raw) if isinstance(raw, dict) else {"title": str(raw)}
        item.setdefault("is_current", is_current)
        item.setdefault("retrieved_at", retrieved_at)
        item.setdefault("freshness", "current" if is_current else "not_current")
        item.setdefault("source", source)
        chunk.append(item)

    out: Dict[str, Any] = {
        "items": chunk,
        "results": chunk,
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
    return out


def _filter_items(items: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    q = (query or "").strip().lower()
    if not q:
        return items
    tokens = [t for t in re.findall(r"[a-z0-9]{2,}", q) if t not in {"the", "and", "for", "sba"}]
    if not tokens:
        return items
    scored = []
    for item in items:
        blob = " ".join(
            str(item.get(k, "")) for k in ("title", "name", "description", "summary", "body", "url")
        ).lower()
        score = sum(1 for t in tokens if t in blob)
        if score:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
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
            return {
                "error": data.get("error"),
                "success": False,
                "message": data.get("Message") or data.get("error"),
                "items": [],
                "source": "sbir",
                "degraded": True,
            }

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
                    "url": raw.get("award_link") or "",
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
        return _normalize_page(
            items,
            page=page,
            page_size=params["rows"],
            source="sbir",
            degraded=False,
            message=None if items else "SBIR API returned no awards for this query",
        )

    # ------------------------------------------------------------------
    # Public search methods used by routes
    # ------------------------------------------------------------------
    def search_articles(self, **params) -> Dict[str, Any]:
        page = int(params.get("page") or 1)
        query = params.get("query") or params.get("q") or ""

        legacy = self._items_from_legacy(self._legacy_search("articles", **params), page)
        if legacy and legacy.get("items") is not None and not legacy.get("degraded"):
            return legacy

        html = self._extract_from_html_pages(
            [
                f"{SBA_SITE}/business-guide",
                f"{SBA_SITE}/funding-programs/loans",
                f"{SBA_SITE}/federal-contracting",
            ],
            item_type="article",
            query=query,
            page=page,
        )
        if html and html.get("items"):
            return html

        items = _filter_items(self._static_article_like(), query)
        return _normalize_page(
            items,
            page=page,
            source="static",
            degraded=True,
            message="Live SBA JSON content API unavailable; using curated official SBA guide links.",
        )

    def get_article(self, article_id: int) -> Dict[str, Any]:
        legacy = self._get_json(f"{self.base_url}/articles/{article_id}.json")
        if isinstance(legacy, dict) and not legacy.get("error"):
            return legacy
        # Fallback: search static/guides by id hash is not useful; return catalog entry
        for item in self._static_article_like():
            if str(item.get("id")) == str(article_id):
                return item
        return {"error": "Article not found", "success": False}

    def search_blogs(self, **params) -> Dict[str, Any]:
        page = int(params.get("page") or 1)
        query = params.get("query") or params.get("q") or ""

        legacy = self._items_from_legacy(self._legacy_search("blogs", **params), page)
        if legacy and legacy.get("items"):
            return legacy

        html = self._extract_from_html_pages(
            [f"{SBA_SITE}/blog", f"{SBA_SITE}/about-sba/sba-newsroom/press-releases-media-advisories"],
            item_type="blog",
            query=query,
            page=page,
        )
        if html and html.get("items"):
            return html

        return _normalize_page(
            _filter_items(self._static_article_like()[:6], query),
            page=page,
            source="static",
            degraded=True,
            message="SBA blog JSON unavailable; showing related official guides.",
        )

    def get_blog(self, blog_id: int) -> Dict[str, Any]:
        legacy = self._get_json(f"{self.base_url}/blogs/{blog_id}.json")
        if isinstance(legacy, dict) and not legacy.get("error"):
            return legacy
        return {"error": "Blog not found", "success": False}

    def search_contacts(self, **params) -> Any:
        return self._legacy_search("contacts", **params)

    def search_courses(self, **params) -> Any:
        page = int(params.get("page") or 1)
        query = params.get("query") or ""
        legacy = self._items_from_legacy(self._legacy_search("courses", **params), page)
        if legacy and legacy.get("items"):
            return legacy
        items = [
            {
                "id": "learning-center",
                "title": "SBA Learning Center",
                "description": "Free online courses for small business owners.",
                "url": f"{SBA_SITE}/sba-learning-platform",
                "type": "course",
            },
            {
                "id": "ascent",
                "title": "Ascent for women entrepreneurs",
                "description": "Online learning for women-owned small businesses.",
                "url": f"{SBA_SITE}/business-guide",
                "type": "course",
            },
            {
                "id": "local-training",
                "title": "Local training partners",
                "description": "SBDC / SCORE / WBC training near you.",
                "url": f"{SBA_SITE}/local-assistance/find",
                "type": "course",
            },
        ]
        return _normalize_page(
            _filter_items(items, query),
            page=page,
            source="static",
            degraded=True,
            message="Courses JSON API unavailable; linking official learning resources.",
        )

    def get_course(self, pathname: str) -> Any:
        return self._get_json(f"{self.base_url}/course.json", {"pathname": pathname})

    def search_documents(self, **params) -> Any:
        page = int(params.get("page") or 1)
        query = params.get("query") or ""
        legacy = self._items_from_legacy(self._legacy_search("documents", **params), page)
        if legacy and legacy.get("items"):
            return legacy
        items = [
            {
                "id": "forms",
                "title": "SBA forms",
                "description": "Official SBA forms library.",
                "url": f"{SBA_SITE}/document",
                "type": "document",
            },
            {
                "id": "sop",
                "title": "Standard Operating Procedures",
                "description": "SBA SOPs and policy guidance documents.",
                "url": f"{SBA_SITE}/document",
                "type": "document",
            },
        ]
        return _normalize_page(
            _filter_items(items, query),
            page=page,
            source="static",
            degraded=True,
            message="Documents JSON API unavailable; linking official document hub.",
        )

    def search_events(self, **params) -> Any:
        page = int(params.get("page") or 1)
        query = params.get("query") or ""
        legacy = self._items_from_legacy(self._legacy_search("events", **params), page)
        if legacy and legacy.get("items"):
            return legacy
        items = [
            {
                "id": "events-hub",
                "title": "SBA events & training",
                "description": "Find webinars and local events from SBA and partners.",
                "url": f"{SBA_SITE}/events",
                "type": "event",
            },
            {
                "id": "local-assistance-events",
                "title": "Partner counseling events",
                "description": "Events via SBDC, SCORE, and local resource partners.",
                "url": f"{SBA_SITE}/local-assistance/find",
                "type": "event",
            },
        ]
        return _normalize_page(
            _filter_items(items, query),
            page=page,
            source="static",
            degraded=True,
            message="Events JSON API unavailable; linking official events/local assistance.",
        )

    def search_lenders(self, **params) -> Any:
        page = int(params.get("page") or 1)
        query = params.get("query") or ""
        legacy = self._items_from_legacy(self._legacy_search("lenders", **params), page)
        if legacy and legacy.get("items"):
            return legacy
        items = [
            {
                "id": "lender-match",
                "title": "Lender Match",
                "description": "Official SBA tool to match with participating lenders.",
                "url": f"{SBA_SITE}/funding-programs/loans/lender-match",
                "type": "lender_tool",
            }
        ]
        return _normalize_page(
            _filter_items(items, query),
            page=page,
            source="static",
            degraded=True,
            message="Lenders CloudSearch API unavailable; use Lender Match.",
        )

    def search_offices(self, **params) -> Any:
        page = int(params.get("page") or 1)
        query = params.get("query") or ""
        legacy = self._items_from_legacy(self._legacy_search("offices", **params), page)
        if legacy and legacy.get("items"):
            return legacy

        html = self._extract_from_html_pages(
            [f"{SBA_SITE}/about-sba/sba-locations", f"{SBA_SITE}/local-assistance/find"],
            item_type="office",
            query=query,
            page=page,
        )
        if html and html.get("items"):
            return html

        return _normalize_page(
            _filter_items(self._static_office_items(), query),
            page=page,
            source="static",
            degraded=True,
            message="Offices JSON API unavailable; linking official location finders.",
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
