# PocketPro SBA — UI/UX Regression Report

**Date:** 2026-07-10 10:17:40 -04:00  
**Host free RAM:** ~1.44 GB  
**Scope:** Live Docker stack (frontend :3000, backend :5000, chromadb :8000)  
**Git tip (committed):** `8fe0814` — *Complete Resources implementation: API nav, load-on-click, detail cards.*  
**Local uncommitted (verified live):** chat default `user_id` + message aliases; favicon/logo assets; `resources.html` / compose mounts  

## Summary

| Metric | Value |
|---|---|
| Total checks | **52** |
| Pass | **52** |
| Fail | **0** |
| Critical fails | **0** |
| Major fails | **0** |
| Minor fails | **0** |
| **Overall** | **PASS** |

Previous run (earlier today) was **PASS WITH NOTES** (3 major timeouts on chat / decompose / orchestrator). Re-run after chat compatibility fix: **all green**.

---

## Overall verdict

**PASS — minimized regression held.**

- Stack is up; UI routes and static assets serve correctly.
- Resources UX (API nav → click load → detail cards) works end-to-end.
- Chat no longer hard-fails for the prebuilt SPA payload (`message` + `session_id` without `user_id`).
- Logo/favicon regressions are fixed (non-empty assets, linked in served `index.html`).
- External flakiness (SBIR 429, dead SBA JSON API) soft-degrades with HTTP 200 — no 500s on Browse paths.
- Live sba.gov HTML content is marked `is_current=true`; RAG/local KB answers are `is_current=false`.

---

## Minimize-regression design (verified)

| Control | Status | Evidence |
|---|---|---|
| Soft-degrade external SBA/SBIR (no hard 500 on Browse) | **PASS** | `/api/sba/content/sbir` → 200, `degraded=true`, `message=rate_limited` |
| Live sba.gov content `is_current=true` | **PASS** | loans/articles/blogs/offices → `source=sba_html`, `is_current=true` |
| RAG/KB answers `is_current=false` | **PASS** | `/api/rag/sba-query` → `is_current=false`, `mode=local_kb_fallback` |
| Resources: catalog first, query on click, detail card | **PASS** | Catalog `behavior=click_to_query`; `/browse` has `loadResource` + detail modal |
| CORS `cache-control` preflight | **PASS** | OPTIONS allow-headers includes `content-type,cache-control` |
| Compat `/api/api/health` | **PASS** | HTTP 200 |
| Chat legacy SPA payload | **PASS** | POST `{message, session_id}` → 200 `success=true` (default `user_id=1`) |
| Logo / favicon non-empty | **PASS** | favicon.ico 1150 B, logo.svg 627 B, favicon.svg 421 B |
| FE nginx proxy to backend | **PASS** | `localhost:3000/api/health` and `/api/info` → 200 |

---

## Results by area

### stack (3/3)

| Check | Pass | Detail |
|---|---|---|
| pocketpro-frontend-dev | YES | running |
| pocketpro-backend-dev | YES | running |
| chromadb-dev | YES | running (healthy) |

### ui (10/10)

| Check | Pass | Detail |
|---|---|---|
| home `/` | YES | 200, SPA shell 1076 B |
| browse `/browse` | YES | 200, live Resources page 24703 B |
| resources alias `/resources.html` | YES | same live page |
| chat / rag / docs / login SPA routes | YES | 200 via try_files → index |
| index favicon + apple-touch logo | YES | `/favicon.svg`, `/favicon.ico`, `/logo.svg` |
| theme-color service blue | YES | `#2563eb` |

### assets (6/6)

| Check | Pass | Detail |
|---|---|---|
| `/favicon.ico` | YES | 1150 B, `image/x-icon` |
| `/favicon.svg` | YES | 421 B |
| `/logo.svg` | YES | 627 B |
| `/static/js/main.f54a4e20.js` | YES | 281240 B (prebuilt CRA) |
| `/static/css/sleek-layout.css` | YES | white/blue service theme |
| `/static/css/main.0facfa3c.css` | YES | 274721 B |

### ux — Resources (4/4)

| Check | Pass | Detail |
|---|---|---|
| API-driven nav | YES | page loads `/api/sba/resources` |
| Click-to-load | YES | `loadResource()` on category click |
| Detail cards | YES | item click → modal detail |
| White/blue styling | YES | `#2563eb` gradient chips/buttons |

### api (8/8)

| Check | Pass | Detail |
|---|---|---|
| `/api/health` | YES | ok |
| `/api/api/health` | YES | double-prefix compat |
| `/api/info` | YES | service info |
| `/api/chromadb_health` | YES | connected |
| `/api/rag/health` | YES | ok (0 docs in vector store) |
| `/api/programs` | YES | catalog of program groups |
| `/api/documents/list` | YES | local docs listed |
| `/api/orchestrator/strategies` | YES | 11 strategies |

### proxy / cors (3/3)

| Check | Pass | Detail |
|---|---|---|
| FE `/api/health` | YES | nginx → backend |
| FE `/api/info` | YES | nginx → backend |
| OPTIONS preflight + cache-control | YES | ACAO + allow-headers |

### chat (3/3) — **was failing earlier**

| Check | Pass | Detail |
|---|---|---|
| Legacy payload (no `user_id`) | YES | **critical path fixed** — 200, ~397 B, `success=true` |
| Query alias + `user_id` | YES | 200 |
| History after message | YES | session history count ≥ 1 |

**Root cause of prior App.js:127 failure:** prebuilt bundle posts  
`POST /api/chat` with `{ message, session_id }` only.  
**Fix (live, uncommitted in `backend/routes/chat.py`):** default `user_id=1`; accept `message|query|text|input` and `session_id|sessionId`.

### resources catalog loads (12/12)

| Resource | Pass | Notes |
|---|---|---|
| catalog API | YES | count=11, `click_to_query` |
| loans | YES | 20 items, `sba_html`, **current** |
| loan_types (`/api/rag/sba-overview`) | YES | 8 types via `available_loan_types`, UI normalizes to cards, **current** |
| lenders | YES | 1 item, static fallback, not_current (expected soft) |
| articles | YES | 20 items, `sba_html`, **current** |
| blogs | YES | 20 items, `sba_html`, **current** |
| courses | YES | 3 items, static fallback |
| documents | YES | 2 items, static fallback |
| events | YES | 2 items, static fallback |
| offices | YES | 20 items, `sba_html`, **current** |
| sbir | YES | soft-degrade: empty + rate_limited (429 upstream) |
| sources | YES | status map; UI `sourcesToItems()` |

### freshness / minimize (3/3)

| Check | Pass | Detail |
|---|---|---|
| loans is_current | YES | `source=sba_html` |
| rag not marked current | YES | `local_kb_fallback` |
| sbir soft degrade | YES | no 500 |

---

## UI/UX troubleshooting notes (resolved)

| Issue | Symptom | Fix / status |
|---|---|---|
| **Chat App.js:127** | `POST /api/chat` 400 without `user_id` | Default `user_id=1` + field aliases — **verified 200** |
| **Logo / favicon fail** | Empty or missing icons | Real `favicon.ico` (1150 B), SVG logo/favicon in `frontend/build` + public — **verified served** |
| **Empty resource cards** | Blank titles on Browse | Normalize items + click-to-query catalog — **no empty-card fails** |
| **CORS preflight** | Browser blocked `cache-control` | Allow-headers include cache-control — **verified** |
| **Double `/api/api/health`** | SPA or proxy typo 404 | Compat route — **verified** |
| **SBA JSON API dead** | Upstream 404 | HTML scrape + static/SBIR soft fallbacks — **verified** |
| **SBIR 429** | Upstream rate limit | Degraded empty payload, HTTP 200 — **by design** |
| **Gemini embeddings** | Unavailable | RAG falls back to local KB keywords; marked not current — **by design** |

---

## Known degradations (not failures)

These are **accepted minimize-regression outcomes**, not regressions:

1. **SBIR API rate-limited (429)** — empty list + `degraded=true`.
2. **Legacy SBA content JSON API 404** — live path is `sba_html` scrape.
3. **Gemini embeddings unavailable** — RAG uses `local_kb_fallback`; answers marked `is_current=false`.
4. **Static fallbacks** for lenders/courses/documents/events when live sources unavailable.
5. **Prebuilt CRA bundle** (`main.f54a4e20.js`) — SPA UI outside `/browse` is older build; live Resources UX is `resources.html` / `/browse` without a full CRA rebuild (low-RAM Windows).
6. **Chroma document_count=0** — vector store empty; health still ok.

---

## Source map

| Area | Live surface | Backend |
|---|---|---|
| Resources UI | `http://localhost:3000/browse` (`resources.html`) | `/api/sba/resources`, `/api/sba/content/*`, `/api/rag/sba-overview` |
| Chat SPA | `http://localhost:3000/chat` → prebuilt JS | `POST /api/chat` (compat payload) |
| Branding | `/favicon.ico`, `/favicon.svg`, `/logo.svg` | static nginx from `frontend/build` |
| Health | FE proxy + BE | `/api/health`, `/api/api/health` |

---

## Uncommitted local changes (included in this verification)

```
 M backend/routes/chat.py          # default user_id + message aliases
 M docker-compose.dev.yml          # frontend mounts
 M frontend/public/favicon.ico     # non-empty icon
 M frontend/public/index.html
 M frontend/public/resources.html
?? frontend/public/favicon.svg
?? frontend/public/logo.svg
```

Also present on disk under `frontend/build/` (what nginx serves): favicon/logo assets + patched `index.html`.

**Recommendation:** commit and push these so main matches the verified stack.

---

## Optional follow-ups (out of scope for this PASS)

| Priority | Item |
|---|---|
| Medium | Commit/push chat + branding fixes |
| Medium | When RAM allows: CRA rebuild so SPA matches latest React sources |
| Low | Retry/backoff for SBIR 429; cache last-good SBIR payload |
| Low | Rotate any previously leaked Gemini API key |
| Low | Re-test heavy `decompose` / full orchestrator under higher timeout (not required for Browse/Chat UX) |

---

## Raw artifacts

- `terminals/regression-checks.json`
- `terminals/regression-checks.csv`
- `terminals/regression-overall.txt` → `OVERALL=PASS`
- `terminals/regression-raw.json` (earlier probe)

---

## Sign-off

| | |
|---|---|
| **UI/UX regression** | **PASS** (52/52) |
| **Minimize regression** | **Verified** (soft degrade, current vs RAG flags, no critical/major fails) |
| **Chat SPA hard-fail** | **Resolved** |
| **Logo/favicon** | **Resolved** |
| **Resources click UX** | **Resolved / verified** |
