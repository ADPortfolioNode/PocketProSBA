# PocketPro SBA — App Standard Template (LOCKED)

**Status:** CURRENT functionality is the **mandatory standard** for every surface in this app.  
**Date locked:** 2026-07-11  
**Do not invent alternate navigation, dead-end cards, or text-only chat without usable links.**

This document is the single source of truth for product behavior. New features must copy this template exactly.

---

## 1. Core rule (non-negotiable)

```
PARENT  →  GET its API path  →  render CHILDREN
CHILD with children  →  always a LINK  →  becomes next PARENT
LEAF  →  detail + official / form / document actions
API response  →  soft-ingest into RAG
Answers  →  human-readable + clickable + usable (forms/tools/docs)
```

**Users must be able to use information** — open links, forms, documents, tools, and in-app Resources — not only read prose.

---

## 2. Surface map (current live stack)

| Surface | URL | Implementation (standard) |
|---------|-----|---------------------------|
| Programs | `/sba` | `frontend/public/programs.html` — expand card, load API in-card, child links |
| Resources browser | `/browse` | `frontend/public/resources.html` — recursive parent→children |
| Chat | `/chat` (SPA) | Magazine prose + `chat-magazine.js` + actionable links |
| Backend catalog | `/api/sba/resources` | Nav + programs + lifecycle + local |
| Backend content | `/api/sba/content/*` | Envelope with `path`, `drillable`, `has_children`, `actions` |
| Backend explore | `/api/sba/content/{type}/{id}` | Child-as-parent |
| RAG ingest | auto on envelope + `/api/sba/rag-ingest` | Live KB + Chroma soft-add |
| Chat/RAG answers | `/api/chat`, `/api/rag` | Formatted hits + **Use this information** + **Links** |

Prefer **volume-mounted** HTML/CSS/JS under `frontend/public/` and `frontend/build/static/` over CRA rebuilds for live UX.

---

## 3. Navigation template

### 3.1 Parent card / badge

- Every parent **must** have `path` starting with `/api/…`
- Click parent:
  - **Always open on Resources page (`/browse#r={path}&t={title}`)** — single explorer for all SBA API topics
  - **Programs (`/sba`):** catalog only; card click → `/browse` (not in-card expand for API routes)
  - **Browse (`/browse`):** `openRoute(path)` → full topic page of children
- Show: title, short description, `path`, badge **Has children** / **API** · CTA **Open on Resources page →**

### 3.2 Child items

| Child state | UI | Action |
|-------------|----|--------|
| `drillable` / `has_children` / `path` starts `/api/` | **Link** (“Explore children” / “Render →”) | Load child path as new parent |
| `resources[]` only | Link / expand | Local parent of nested resources |
| Leaf (no path, no children) | Details | Modal/detail + official/form actions |

**Never** open a leaf modal first when the item has an API path or children.

### 3.3 Recursive explore

- Breadcrumb / Back stack required
- Child path examples:
  - `/api/sba/content/loans` → `/api/sba/content/loans/7a`
  - `/api/sba/content/contracting` → `/api/sba/content/contracting/8a`
  - `/api/sba/lifecycle/start` → stage resources

### 3.4 Path stamping (backend)

In `_envelope` / normalize:

- Stamp missing child paths under parent: `{parent}/{id}` when non-leaf
- Set `drillable = path starts with /api/`
- Set `has_children = drillable OR resources[]`
- Do **not** stamp leaf types: `overview`, `link`, `notice`, `loan_section`, `*-overview`, `*-official`

---

## 4. API response envelope template

Every list/explore response must include:

```json
{
  "path": "/api/sba/content/loans",
  "title": "SBA Loans",
  "items": [
    {
      "id": "7a",
      "title": "SBA 7(a) loans",
      "description": "…",
      "path": "/api/sba/content/loans/7a",
      "url": "https://www.sba.gov/…",
      "fileUrl": null,
      "registrationLink": null,
      "type": "loan_program",
      "drillable": true,
      "has_children": true,
      "parent_path": "/api/sba/content/loans",
      "actions": [
        { "id": "open_route", "label": "Explore children", "path": "/api/sba/content/loans/7a" },
        { "id": "official", "label": "Official source", "href": "https://www.sba.gov/…" }
      ]
    }
  ],
  "topic": { "title": "…", "description": "…", "sections": [], "actions": [] },
  "digestion": { "pipeline": [], "facets": [], "quality": {} },
  "rag_ingest": { "scheduled": true, "route": "/api/sba/content/loans", "items": 6 }
}
```

### Usable content actions (required when present)

| Field / action | Label | Opens |
|----------------|-------|--------|
| `fileUrl` | Open form / document | Form or file |
| `registrationLink` | Register / RSVP | Event signup |
| `url` / `link` | Official source | sba.gov |
| `path` | Explore children / Open in Resources | In-app drill |
| curated tools | Lender Match, forms library, offices | Official or `/browse#…` |

---

## 5. RAG template

On every successful content envelope (parent or child):

1. **Async soft-ingest** via `schedule_sba_rag_ingest(envelope, route, title)`
2. Write `backend/knowledge_base/sba_api_live/{slug}__*.txt`
3. Soft-add chunks to Chroma when available
4. Never fail the HTTP response if RAG fails
5. Throttle re-ingest (~45s/route)

Chat/RAG query order:

1. Live API digests (`sba_api_live`) + local KB  
2. Chroma / RAGManager  
3. Enhanced Gemini (if initialized)  
4. Soft fallback with **still-usable links**

---

## 6. Chat / answer template

### Forbidden

```
Here's what I found regarding your query:
Source 1: sba_api
Type: loan_program API path: /api/...
```

(No raw metadata dumps, no duplicate identical sources.)

### Required shape

```markdown
Here’s a clear summary from live SBA resources about **{query}**:

### 1. [Title](https://official-or-app-url)
Short human blurb…

 → [Official page](https://…) · [Open in Resources](/browse#r=…)

## Use this information
Open a link below to **use** forms, tools, or full program pages:
- 📝 [SBA forms library (official)](https://www.sba.gov/document)
- 🛠️ [Lender Match tool](https://www.sba.gov/…)
- 📂 [Explore topic in Resources](/browse#r=…)

## Links
- …
```

### Presentation

- Magazine-readable prose (`chat-magazine.js` + sleek CSS)
- Itemized lists for steps
- Markdown → real `<a>` tags (external + in-app)
- Hard-refresh after static asset changes

### Code modules (standard)

| Module | Role |
|--------|------|
| `backend/services/chat_answer_format.py` | Dedupe hits → human answer |
| `backend/services/link_enrichment.py` | Markdown hyperlinks |
| `backend/services/actionable_content.py` | Forms / docs / tools section |
| `backend/services/sba_rag_ingest.py` | API → RAG |
| `backend/services/app_standard.py` | Machine-readable standard constants |
| `frontend/public/programs.html` | Expand-card parent→child |
| `frontend/public/resources.html` | Recursive browse + form buttons |
| `frontend/build/static/js/chat-magazine.js` | Linkify + lists |

---

## 7. UI copy standard

| Context | CTA |
|---------|-----|
| Parent with API path | Expand · load API children → |
| Child with children | Explore children → / Render → |
| Leaf | Open details → |
| Form/doc | Open form / document |
| Event | Register |
| Official | Official / Official page |

---

## 8. Soft-degrade standard

| Failure | Behavior |
|---------|----------|
| sba.gov scrape down | Cached/fallback items; `degraded` flag; still list children if catalog |
| Chroma / embeddings down | Local KB + live digests; no 500 |
| Chat model timeout | Soft message + **Use this information** links |
| Missing path on child | Derive from parent + id when non-leaf |

---

## 9. Checklist for any new feature

Copy this into PRs / agent tasks:

- [ ] Parent has `/api/…` path and loads children on click  
- [ ] Children with children are links (not modal-only)  
- [ ] Recursive back/breadcrumb works  
- [ ] Envelope has `drillable`, `has_children`, `actions`  
- [ ] Forms/docs expose `fileUrl` + Open form/document  
- [ ] Envelope schedules RAG ingest  
- [ ] User-facing text is human-readable (no `Source N: sba_api`)  
- [ ] Answer includes usable links (official + in-app + forms/tools)  
- [ ] Live HTML/CSS/JS mounted (no dependency on CRA rebuild for core UX)  
- [ ] Soft-fail never blanks the whole surface  

---

## 10. Canonical examples

| User action | Expected |
|-------------|----------|
| `/sba` → SBA Loans | Card expands; children 7(a), 504, Microloans… each linkable |
| Click 7(a) | Card/browse loads `/api/sba/content/loans/7a`; ingest RAG |
| Chat: “forms for 7a” | Summary + **Use this information** with forms library + 7(a) docs + Lender Match |
| `/browse` → Documents | Cards with **Open form / document** when `fileUrl` set |

---

## 11. Enforcement

- **Product:** This file is the UX contract.  
- **Code:** `backend/services/app_standard.py` exports the same rules for imports/tests.  
- **Agents / contributors:** Follow this template; do not reintroduce modal-only parents or text-only answers.

**CURRENT = STANDARD. Ship variations only by extending this template, never by replacing it.**
