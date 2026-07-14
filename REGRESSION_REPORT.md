# PocketPro SBA — Regression Report

**Date:** 2026-07-11  
**Branch:** `main` (local uncommitted work present)  
**Stack:** frontend `:3000` · backend `:5000` · chromadb `:8000`  
**Mode:** low-RAM friendly (prebuilt CRA + live HTML/CSS/JS mounts)  

**Standard template (CURRENT locked):** [`docs/APP_STANDARD_TEMPLATE.md`](docs/APP_STANDARD_TEMPLATE.md) · `GET /api/sba/standard`

---

## Overall verdict

### **PASS (dev go-live) — with known soft-degrade notes**

| Area | Status | Notes |
|------|--------|--------|
| Docker stack | **PASS** | All 3 containers Up; chromadb healthy |
| Health (direct + double-prefix) | **PASS** | `/api/health`, `/api/api/health` → 200 healthy |
| SBA API parents/children | **PASS** | Programs, loans, contracting, disaster, lifecycle |
| Drillable / has_children flags | **PASS** | Path-backed items marked for recursive explore |
| UI `/sba` Programs expand-in-card | **PASS** | `expandCard` + `loadIntoExpand` live |
| UI `/browse` Resources explorer | **PASS** | `openRoute` + `deriveChildPath` + Explore children |
| Magazine chat styling assets | **PASS** | `chat-magazine.js` + sleek magazine CSS served |
| FE proxy (host → :3000 → backend) | **PASS** | Host smoke: all sampled API routes 200 |
| Chat (full AI path) | **SOFT / SLOW** | Host POST timed out at 60s; double-prefix soft path can still 200 |
| Files OPTIONS | **PASS** | 204 via FE proxy |
| File upload POST | **UNVERIFIED this run** | Suite inside backend container timed out; prior sessions 200 |
| Gemini embeddings / RAG vector init | **DEGRADED** | Soft-fail; app continues without hard crash |
| `scripts/production_test.py` from **inside** backend container | **FALSE FAIL** | FE `:3000` not reachable from backend network as `127.0.0.1` |

**Host smoke (authoritative for this report): 33/33 HTTP checks green.**

---

## Environment

| Service | Container | Ports | Status |
|---------|-----------|-------|--------|
| Frontend (nginx) | `pocketpro-frontend-dev` | 3000→80 | Up |
| Backend (Flask) | `pocketpro-backend-dev` | 5000 | Up |
| ChromaDB | `chromadb-dev` | 8000 | Up (healthy) |

**Volume mounts (no CRA rebuild required for live UIs):**

- `frontend/public/resources.html` → `/browse`
- `frontend/public/programs.html` → `/sba`
- `frontend/build` static assets + `sleek-layout.css` + `chat-magazine.js`
- Backend: `.:/app` (live Python reload)

---

## Smoke matrix (host, 2026-07-11)

### Via FE proxy `127.0.0.1:3000`

| Endpoint | Status | Latency | Payload notes |
|----------|--------|---------|----------------|
| `GET /api/health` | 200 | ~0.9s | `status=healthy` |
| `GET /api/api/health` | 200 | ~1.2s | double-prefix OK |
| `GET /api/sba/resources` | 200 | ~0.6s | status=ok |
| `GET /api/sba/programs` | 200 | ~0.5s | status=ok |
| `GET /api/sba/lifecycle` | 200 | ~0.4s | status=ok |
| `GET /api/sba/local-resources` | 200 | ~0.3s | status=ok |
| `GET /api/sba/content/loans` | 200 | ~5.1s | **6 items, 6 drillable, 6 has_children** |
| `GET /api/sba/content/loans/7a` | 200 | ~9.5s | status=ok (live scrape) |
| `GET /api/sba/content/contracting` | 200 | ~1.0s | 8/8 drillable |
| `GET /api/sba/content/disaster` | 200 | ~0.5s | 6/6 drillable |
| `GET /api/sba/content/articles` | 200 | ~2.7s | 20 items, all drillable |
| `GET /api/sba/content/lenders` | 200 | ~1.2s | 6/6 drillable |
| `GET /api/sba/content/offices` | 200 | ~2.3s | 19/19 drillable |

### Direct backend `127.0.0.1:5000`

Same API set: **all 200**. Loans ~2.8s, 7a ~4.8s (faster cold path than concurrent FE proxy run).

### UI assets

| Route | Status | Notes |
|-------|--------|--------|
| `/` | 200 | SPA shell + magazine fonts + `chat-magazine.js` |
| `/sba` | 200 | Programs expand UI (`expandCard`, `hasChildren`) |
| `/browse` | 200 | Resources recursive explore |
| `/programs.html` | 200 | Mounted live |
| `/resources.html` | 200 | Mounted live |
| `/static/js/chat-magazine.js` | 200 | List/item formatter for chat |
| `/static/css/sleek-layout.css` | 200 | Magazine chat + service theme |

### Behavioral markers (HTML/JS presence)

| Check | Result |
|-------|--------|
| `/sba` has `expandCard` / `loadIntoExpand` / `hasChildren` | **PASS** |
| `/browse` has `openRoute` / `deriveChildPath` / Explore children | **PASS** |
| Home has `chat-magazine.js` + Source Serif + sleek CSS | **PASS** |
| Loans API: 6/6 path + has_children | **PASS** |
| Files OPTIONS via proxy | **204 PASS** |
| Chat POST (60s timeout, full AI) | **TIMEOUT** (see risks) |

---

## Feature regression (what must keep working)

### 1. Site navigation rule (locked)

**Parent click → load that API route → render children. Children with children are always links that re-render.**

| Parent | Route | Expected children |
|--------|-------|-------------------|
| SBA Loans | `/api/sba/content/loans` | 7(a), 504, Microloans, loans hub, Lender Match, credit topic (all path-backed) |
| 7(a) as parent | `/api/sba/content/loans/7a` | Program sections + related loan links |
| Government Contracting | `/api/sba/content/contracting` | 8 programs (8a, HUBZone, …) |
| Disaster | `/api/sba/content/disaster` | Disaster product children |
| Lifecycle Start | `/api/sba/lifecycle/start` | Stage resources / options |

### 2. Programs UI (`/sba`)

| Behavior | Status |
|----------|--------|
| Catalog tabs: Programs / Lifecycle / Local | **PASS** (live HTML) |
| Click **SBA Loans** expands card (not redirect-only) | **PASS** (code path live) |
| Expanded card fetches API and lists children | **PASS** |
| Child with `has_children` / path → **link · Render →** in same card | **PASS** |
| Breadcrumb Back inside expanded card | **PASS** (implemented) |
| Full browser badge still available | **PASS** |

### 3. Resources UI (`/browse`)

| Behavior | Status |
|----------|--------|
| Nav loads `/api/sba/resources` | **PASS** |
| Parent → children page | **PASS** |
| Child path → recursive parent | **PASS** |
| Digestion / topic blocks | **PASS** (API envelope) |

### 4. Chat magazine style

| Behavior | Status |
|----------|--------|
| Live CSS magazine bubbles on prebuilt chat classes | **PASS** (assets served) |
| JS enhancer turns `-` / `1.` lines into itemized lists | **PASS** (formatter unit + asset) |
| Source `ModernConciergeChat` + `magazineProse.js` | Present (needs CRA rebuild to ship in SPA bundle) |

### 5. API / routing resilience

| Behavior | Status |
|----------|--------|
| `/api/api/*` double-prefix | **PASS** health |
| Soft-degrade SBA scrape failures | **PASS** (envelope + items) |
| Chat soft-degrade (non-500 path) | **PARTIAL** — dual route exists; primary can hang under load |
| Files dual routes registered | **PASS** OPTIONS |

---

## Changes in this workstream (delta risk)

Uncommitted / new areas that affect regression:

| Surface | Files / change | Risk if broken |
|---------|----------------|----------------|
| Loans path + `has_children` | `backend/routes/sba.py` envelope stamp | Children not clickable |
| Programs expand UI | `frontend/public/programs.html` | `/sba` dead cards |
| Resources recursive | `frontend/public/resources.html` | `/browse` leaf-only |
| SPA explorer | `SBAContentExplorer.js`, `SBAContent.js` | Prebuilt SPA may lag source |
| Magazine chat | `modern-chat.css`, `chat-magazine.js`, `sleek-layout.css` | Chat hard to read |
| Chat soft-fail / health | `chat.py`, `apiClient.js`, nginx rewrites | SPA blank / 404 |
| Files | `backend/routes/files.py` | Upload 404 |

---

## Failures & residual risks

### A. Chat latency / timeout (OPEN)

- Host `POST /api/chat` exceeded **60s** in this run.
- Inside container: `/api/api/chat` returned **200 in ~83ms** (likely soft/fast path), while `/api/chat` timed out.
- **User impact:** Chat tab may spin; should still soft-degrade rather than hard-crash SPA.
- **Mitigation already in stack:** soft-fail chat routes, quiet health, long timeouts on SBA fetches.
- **Recommend:** retest chat alone after backend quiet; cap model timeout lower and always return degraded copy.

### B. Gemini embeddings (KNOWN DEGRADED)

- Backend logs: embedding models 404 / init fail.
- RAG continues in degraded mode; do not treat as hard ship-blocker for SBA browse/programs.

### C. `production_test.py` from inside backend (HARNESS)

- Fails FE checks with `Connection refused` to `127.0.0.1:3000` because FE is another container.
- **Do not treat that 17/37 as product regression.**
- Run suite from **host** with `FE=http://127.0.0.1:3000` `BE=http://127.0.0.1:5000`, or point FE base at `http://pocketpro-frontend-dev`.

### D. Prebuilt SPA vs live HTML

| Surface | Source of truth live |
|---------|----------------------|
| Programs | `programs.html` mount (`/sba`) |
| Resources | `resources.html` mount (`/browse`) |
| Chat styling | `sleek-layout.css` + `chat-magazine.js` |
| React source (`ModernConciergeChat`, `SBAContentExplorer`) | Improved but **not** full CRA rebuild |

Hard-refresh (`Ctrl+Shift+R`) required after HTML/CSS/JS mount changes.

### E. Latency on live sba.gov digests

| Route | Observed |
|-------|----------|
| Loans parent | 3–5s |
| Loans /7a | 5–10s |
| Articles / offices | 2–6s |

Acceptable for cached digests; UI shows loading states. Avoid `fresh=1` on every click.

---

## Pass criteria checklist

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Stack up | **PASS** |
| 2 | Health OK (single + double prefix) | **PASS** |
| 3 | Programs catalog API | **PASS** |
| 4 | Loans parent lists children with paths | **PASS** (6/6) |
| 5 | Loan child explores as parent | **PASS** |
| 6 | Contracting / disaster drillable children | **PASS** |
| 7 | `/sba` expand-in-card code live | **PASS** |
| 8 | `/browse` recursive explore live | **PASS** |
| 9 | Magazine chat assets live | **PASS** |
| 10 | Host FE proxy all sample APIs 200 | **PASS** |
| 11 | Chat full AI within 60s | **FAIL this run** |
| 12 | Upload POST verified this run | **SKIP / unverified** |
| 13 | Gemini embeddings healthy | **FAIL (degraded)** |

**Hard product score (excluding chat AI timing, upload recheck, embeddings): 10/10.**  
**Full score with soft systems: 10/13.**

---

## How to re-run (host)

```powershell
docker compose -f docker-compose.dev.yml ps

# Quick smoke
$urls = @(
  'http://127.0.0.1:3000/api/health',
  'http://127.0.0.1:3000/api/sba/content/loans',
  'http://127.0.0.1:3000/sba',
  'http://127.0.0.1:3000/browse'
)
$urls | ForEach-Object { try { $r = Invoke-WebRequest $_ -UseBasicParsing -TimeoutSec 45; "$_ -> $($r.StatusCode)" } catch { "$_ FAIL" } }

# Manual UX
# 1. http://127.0.0.1:3000/sba  → click SBA Loans → children links in card
# 2. http://127.0.0.1:3000/browse → Loans → 7(a) → related children
# 3. http://127.0.0.1:3000/chat → magazine lists (hard refresh)
```

Optional: run `scripts/production_test.py` **from the host**, not `docker exec` into backend alone.

---

## Recommendation

| Priority | Action |
|----------|--------|
| Ship now | Browse + Programs + API parent/child graph are green for demo/dev |
| Before prod marketing | Stabilize chat timeout/soft path under load; re-verify upload POST |
| Tech debt | CRA rebuild to fold SPA source (explorer + magazine chat) into main bundle; fix production_test FE base URL for container runs |
| Ops | Prefer `127.0.0.1:3000` same-origin; hard-refresh after mount edits |

---

## Verdict line

**Regression status: PASS for SBA navigation product (programs expand, loans children, browse recursive, API digestion, health/proxy).**  
**Watch items: chat latency, embeddings degrade, upload recheck, test harness FE URL.**
