# PocketPro SBA Workflow Verification Report

**Run date:** 2026-10-24  
**Overall result:** Partial verification — core SBA navigation and chat respond. The Chroma compatibility fix is implemented and passed an isolated CRUD/retrieval check, but the live RAG service remains unavailable until the Chroma container is recreated with the updated image.

**Health-check note (2026-10-25):** After the later `start.sh` run, the standalone health-check scripts were found probing stale endpoints (`/api/v2/heartbeat` and port `10000`). The running deployment exposed ChromaDB 0.4.24 at `/api/v1/heartbeat`, the backend at `/api/health` on port `5000`, and the frontend at port `3000`. Both root health-check scripts now use those endpoints and ASCII status markers for Windows console compatibility. Both scripts passed against the running services. A successful Chroma heartbeat verifies service availability only: `/api/info` still reports `rag_status: unavailable`, and `/api/rag/health` still returns 503.

## Executive summary

- The frontend, backend, ChromaDB heartbeat, chat health, and orchestrator health endpoints responded.
- Programs and Resources follow the expected parent → API → child flow. A program card opened Resources, and the SBA Loans parent opened the 7(a) child topic at a 1280 × 800 viewport.
- A real chat question returned an answer with sources. This does **not** verify Chroma-backed retrieval: the backend reports RAG unavailable, the RAG health route returns 503, and the documents collection is not initialized.
- Backend and frontend full suites both exit non-zero. The focused chat component tests pass, and the production frontend build succeeds.

## Live workflow checks

| Workflow | Result | Evidence |
|---|---|---|
| Frontend availability | PASS | `GET /` on port 3000 returned 200. Home page and primary navigation rendered. |
| Chat interface and message send | PARTIAL | Submitted an SBA 7(a) eligibility question in the signed-in chat UI. The chat POST completed with HTTP 200; backend logs recorded a 4,613-character response with sources. The response path cannot be confirmed as vector RAG while the RAG manager is unavailable. |
| Programs → Resources | PASS | The SBA Loans program card opened `/browse` with `/api/sba/content/loans`. |
| Resources parent → child | PASS at desktop width | The `7(a) loans` child opened `/browse` with `/api/sba/content/loans/7a`; the child topic rendered official-source and follow-on actions. |
| Resources at narrower viewport | PARTIAL | At 957 × 658, browser clicks on a child action were intercepted by the sidebar. The same flow succeeded at 1280 × 800. |
| SBA catalog/content APIs | PASS (sampled) | Articles: 200 / 30 items; loans: 200 / 9 items; lifecycle start: 200 / 26 items; programs: 200 / 9 items; local resources: 200 / 8 items. |
| Programs page | PASS | `/sba` rendered the catalog and its API-topic cards with “Open on Resources page” actions. |
| Documents page | PARTIAL | The signed-in UI rendered the upload form and uploaded-file list. An unauthenticated direct `GET /api/documents/list` returned 401, as expected for a protected endpoint. No file was uploaded during verification to avoid changing persistent user data. |
| Orchestrator | PASS (health/UI smoke) | `/api/orchestrator/health` returned 200; the task form rendered. Task execution was not submitted. |
| RAG query/ingest | FAIL / BLOCKED | `/api/rag/health` returned 503; `/api/info` reported `rag_status: unavailable` and `document_count: 0`. ChromaDB heartbeat returned 200, but `/api/chromadb_health` reported an error and zero documents. |
| SBA ingest status | PARTIAL | `GET /api/sba/rag-ingest` returned 200, but this status response does not establish that chunks can be stored or retrieved while the collection is unavailable. |

### RAG diagnosis

The persisted database records Chroma `sysdb` migration 5 (`00005-remove-topic`) and migration 7 (`config_json_str`), and its `collections` table has no `topic` column. The running server was Chroma 0.4.24, whose schema expectations do not match that 0.5.x database. Backend logs show collection initialization failing with:

```text
OperationalError('no such column: collections.topic')
Collection documents not initialized
```

The ChromaDB service itself answers its heartbeat, but the app cannot initialize its documents collection. Treat chat answers as fallback/hybrid responses until the updated Chroma server is running and RAG health returns healthy.

### Compatibility fix and verification (2026-10-25)

- Updated production Compose, development Compose, and `Dockerfile.chromadb` to use `chromadb/chroma:0.5.3`, matching the persistent database schema. The backend client remains pinned at 0.4.24 to retain the Pydantic v1-dependent AI stack.
- Updated `DEPLOY.md` and the deployment-config test to document and enforce the intended client/server split.
- On a disposable Chroma 0.5.3 server, the actual backend `ChromaService` using client 0.4.24 initialized both collections, passed heartbeat, added a document, retrieved the matching document, and deleted the probe successfully. The disposable server was stopped afterward; the persistent database was not modified.
- The deployment-config test file passes: 53 passed.
- The running production container is still `chromadb/chroma:0.4.24`; live `/api/rag/health` still returns 503. Recreate the Chroma service through the normal `start.sh` workflow, then repeat live health and chat ingest/retrieval checks. Do not downgrade the Chroma image or remove `chromadb_data`.

## Automated verification

| Suite/check | Result | Notes |
|---|---|---|
| Backend, in the app container (before Chroma config fix) | FAIL: 344 passed, 37 failed, 10 skipped | All 37 reported failures were in deployment-config assertions; the updated deployment-config file now passes all 53 tests. Runtime: 529.75 seconds. |
| Backend, host Python collection attempt | BLOCKED | The host Python environment lacks `jwt` / PyJWT. The full backend suite was therefore run in the backend container. |
| Frontend full Jest suite | FAIL: 13 suites passed, 28 failed; 85 tests passed | Jest exited 1. The targeted `RAGWorkflowInterface.test.js` suite fails during collection with `SyntaxError: Cannot use import statement outside a module` and runs zero tests. |
| Chat component Jest suite | PASS: 5/5 tests | `ModernConciergeChat.test.js` passed. |
| Frontend production build | PASS | `npm run build --prefix frontend` completed with `GENERATE_SOURCEMAP=false`. Build emitted the bundle and injected API base `http://localhost:5000`. Browserslist data is stale; the build also reports existing Node deprecation warnings. |
| Whitespace validation | PASS | `git diff --check` completed without errors. |

## Chat UI update

The chat window now has:

- A compact SBA-branded header with a direct **Browse SBA resources** link.
- A clearer welcome state and selectable prompt cards with short descriptions.
- A less bulky composer with a compact SBA tip, improved focus states, and a visible keyboard hint.
- Responsive chat sizing and styling aligned with the app’s blue-and-white theme.
- Conversation auto-scroll contained within the message panel, avoiding page-level scrolling when a response arrives.

The running frontend container serves an immutable image and has no bind mount to the generated build output. The updated source and local production bundle are ready, but the container on port 3000 was not rebuilt/replaced during this verification; redeploy/recreate that frontend service to publish the new chat UI there.

## Recommended follow-up

1. Recreate Chroma using the updated 0.5.3 image via `start.sh`, then verify live RAG health and a document ingest followed by retrieval through chat.
2. Fix the Jest transform/configuration issue that prevents the RAG workflow suite from collecting.
3. Review the 37 backend deployment-configuration assertions.
4. Check the Resources sidebar overlay at tablet/narrow widths.
5. Rebuild and recreate the frontend container to publish the chat UI update on port 3000.
