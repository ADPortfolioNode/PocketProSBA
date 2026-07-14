# Agent instructions — PocketPro SBA

## Standard template (mandatory)

**CURRENT app functionality is the locked standard.** Do not replace it with alternate UX.

Full contract: [`docs/APP_STANDARD_TEMPLATE.md`](docs/APP_STANDARD_TEMPLATE.md)  
Code constants: [`backend/services/app_standard.py`](backend/services/app_standard.py)

### Always implement

1. **Parent → API → children** — always open API topics on **`/browse`** (Resources page).
2. **Children with children are always links** that load the next parent (still on `/browse`).
3. **API envelope → soft RAG ingest** (`sba_rag_ingest`).
4. **Human answers** + **Use this information** (forms/docs/tools) + **Links**.
5. **Soft-degrade**; never hard-blank Programs / Browse / Chat.

### Live files (prefer mounts over CRA rebuild)

- `frontend/public/programs.html` → `/sba`
- `frontend/public/resources.html` → `/browse`
- `frontend/build/static/js/chat-magazine.js`
- `frontend/build/static/css/sleek-layout.css`

### Forbidden

- `Source N: sba_api` style chat dumps  
- Modal-only parents that have `/api/` paths  
- Text-only answers with no usable forms/links when content exists  

### Stack

- Dev: `docker compose -f docker-compose.dev.yml` — FE `:3000`, BE `:5000`, Chroma `:8000`
- Prefer `127.0.0.1` / same-origin via nginx proxy
