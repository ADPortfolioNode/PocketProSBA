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

# In-process TTL cache (seconds) to avoid thrashing external sites on low-RAM hosts
_CACHE: Dict[str, Tuple[float, Any]] = {}
_CACHE_TTL = int(os.getenv("SBA_CACHE_TTL_SECONDS", "300"))


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


class _LinkHeadingParser(HTMLParser):
    """Extract (text, href) pairs and h1-h3 headings from SBA HTML pages."""

    def __init__(self) -> None:
        super().__init__()
        self.links: List[Dict[str, str]] = []
        self.headings: List[str] = []
        self._in_a = False
        self._a_href = ""
        self._a_text: List[str] = []
        self._in_heading = False
        self._heading_text: List[str] = []

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)
        if tag == "a" and attrs_d.get("href"):
            self._in_a = True
            self._a_href = attrs_d.get("href", "")
            self._a_text = []
        if tag in ("h1", "h2", "h3"):
            self._in_heading = True
            self._heading_text = []

    def handle_endtag(self, tag):
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

    def handle_data(self, data):
        if self._in_a:
            self._a_text.append(data)
        if self._in_heading:
            self._heading_text.append(data)


def _normalize_page(
    items: List[Dict[str, Any]],
    page: int = 1,
    page_size: int = 20,
    source: str = "static",
    degraded: bool = False,
    message: Optional[str] = None,
) -> Dict[str, Any]:
    page = max(1, int(page or 1))
    page_size = max(1, min(int(page_size or 20), 50))
    total = len(items)
    total_pages = max(1, (total + page_size - 1) // page_size) if total else 0
    start = (page - 1) * page_size
    chunk = items[start : start + page_size]
    out: Dict[str, Any] = {
        "items": chunk,
        "results": chunk,  # legacy key used by some callers
        "total_pages": total_pages,
        "totalPages": total_pages,
        "currentPage": page,
        "count": total,
        "source": source,
        "degraded": degraded,
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
    def _get_json(self, url: str, params: Optional[dict] = None, timeout: int = 12) -> Any:
        cache_key = f"json:{url}?{urlencode(params or {}, doseq=True)}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            if response.status_code == 429:
                return {"error": "rate_limited", "status_code": 429, "success": False}
            response.raise_for_status()
            data = response.json()
            _cache_set(cache_key, data)
            return data
        except requests.RequestException as e:
            return {"error": str(e), "success": False}
        except ValueError as e:
            return {"error": f"invalid_json: {e}", "success": False}

    def _get_html(self, url: str, timeout: int = 15) -> Optional[str]:
        cache_key = f"html:{url}"
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
            _cache_set(cache_key, text, ttl=max(_CACHE_TTL, 600))
            return text
        except requests.RequestException as e:
            logger.warning("SBA HTML fetch failed %s: %s", url, e)
            return None

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
    ) -> Optional[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        seen = set()
        for url in urls:
            html = self._get_html(url)
            if not html:
                continue
            parser = _LinkHeadingParser()
            try:
                parser.feed(html)
            except Exception as e:
                logger.warning("HTML parse failed for %s: %s", url, e)
                continue
            # Prefer in-site content links
            for link in parser.links:
                title = link["title"]
                href = urljoin(SBA_SITE, link["href"])
                if "sba.gov" not in href:
                    continue
                # Skip chrome/nav noise
                low = title.lower()
                if low in {
                    "home",
                    "menu",
                    "search",
                    "skip to main content",
                    "primary navigation",
                    "footer navigation",
                    "breadcrumb",
                    "login",
                    "sign in",
                }:
                    continue
                if len(title) < 4 or len(title) > 160:
                    continue
                key = (title.lower(), href.rstrip("/"))
                if key in seen:
                    continue
                seen.add(key)
                items.append(
                    {
                        "id": abs(hash(key)) % (10**10),
                        "title": title,
                        "description": f"From {url}",
                        "url": href,
                        "type": item_type,
                        "source_page": url,
                    }
                )
            # Also capture headings as topic stubs when few links
            if len(items) < 5:
                for h in parser.headings:
                    low = h.lower()
                    if low in {"primary navigation", "breadcrumb", "footer navigation"}:
                        continue
                    key = (h.lower(), url)
                    if key in seen:
                        continue
                    seen.add(key)
                    items.append(
                        {
                            "id": abs(hash(key)) % (10**10),
                            "title": h,
                            "description": f"Topic on {url}",
                            "url": url,
                            "type": item_type,
                            "source_page": url,
                        }
                    )
        if not items:
            return None
        items = _filter_items(items, query)
        return _normalize_page(
            items,
            page=page,
            source="sba_html",
            degraded=True,
            message="Served from official sba.gov HTML (JSON content API unavailable).",
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
        Loan program catalog: prefer live HTML from official loan pages,
        fall back to curated catalog.
        """
        page = int(params.get("page") or 1)
        query = params.get("query") or params.get("q") or ""

        html = self._extract_from_html_pages(
            [
                self.LOAN_PAGES["loans_hub"],
                self.LOAN_PAGES["7a"],
                self.LOAN_PAGES["504"],
                self.LOAN_PAGES["microloans"],
            ],
            item_type="loan",
            query=query,
            page=page,
        )
        # Always merge curated loan types so UI has stable program cards
        static_items = _filter_items(self._static_loan_items(), query)
        if html and html.get("items"):
            # Prepend static program cards (dedupe by title)
            titles = {i.get("title", "").lower() for i in html["items"]}
            merged = list(static_items)
            for item in html["items"]:
                if item.get("title", "").lower() not in titles:
                    merged.append(item)
            return _normalize_page(
                merged,
                page=page,
                source="sba_html+static",
                degraded=True,
                message="Loan content from official sba.gov pages + curated program cards.",
            )

        return _normalize_page(
            static_items,
            page=page,
            source="static",
            degraded=True,
            message="Using curated loan catalog from official SBA program definitions.",
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
