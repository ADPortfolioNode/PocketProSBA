# PocketPro:SBA

PocketPro:SBA is a Retrieval-Augmented Generation (RAG) application that provides Small Business Administration guidance via a React frontend, a Flask backend, and ChromaDB for persistent vector storage. The repository is distributed and run primarily via Docker Compose.

## Key points
- The repository uses `start.sh` as the canonical launcher. `start.sh` prefers `.env.template` (root) and `backend/.env.example` to create runtime `.env` files when missing.
- `GEMINI_API_KEY` is required for LLM features — `start.sh` will abort if it is not set.
- Production and development compose files live in the repo (`docker-compose.yml`, `docker-compose.dev.yml`).

## Quick start (recommended)

Prerequisites:
- Docker Desktop (engine + compose plugin)
- Git
- A valid `GEMINI_API_KEY`

1. Create environment files (copy templates):

```bash
cp .env.template .env
cp backend/.env.example backend/.env
# Edit both .env files and set GEMINI_API_KEY and any other secrets
```

2. Start the app (development mode):

```bash
./start.sh --mode dev --build
# or explicitly with compose
docker compose -f docker-compose.dev.yml up --build -d
```

3. Service URLs (local dev defaults):

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 (nginx may also serve on port 80) |
| Backend API | http://localhost:5000 (routes mounted under `/api`) |
| ChromaDB | http://localhost:8000 |

## Health & quick checks
- Backend health endpoint: `GET /api/health` (e.g. `http://localhost:5000/api/health`)
- Chat endpoint: `POST /api/chat` (JSON payload)

Example curl checks:

```bash
curl -sS http://localhost:5000/api/health
curl -sS -X POST -H "Content-Type: application/json" -d '{"message":"hello"}' http://localhost:5000/api/chat
```

## Project layout (high level)

```
.
├─ backend/                 # Flask app, routes, services, tests
│  ├─ routes/               # API Blueprints: chat, rag, orchestrator, auth, etc.
│  ├─ services/             # RAG, chat and assistant implementations
│  └─ .env.example
├─ frontend/                # React application (src, public)
├─ docker-compose.yml       # Production compose definition
├─ docker-compose.dev.yml   # Development compose (hot-reload, mounts)
├─ start.sh                 # Launcher script (creates .env, starts compose)
├─ .env.template            # Root env template used by start.sh
├─ uploads/                 # Uploaded documents persisted on host
└─ chromadb_data/           # Persistent data for ChromaDB
```

## Development notes
- Use `./start.sh --mode dev` for local development; it handles creating `.env` files and selecting the dev compose file.
- Tests are in `backend/tests/` — the repo contains multiple test scripts and diagnostics used during CI/development. Do not remove production code or Dockerfiles when cleaning up test artifacts.

## Logs and data
- `logs/` is used for startup and runtime logs when `start.sh` runs without `--no-logfile`.
- Keep `uploads/` and `chromadb_data/` directories mounted/persisted between restarts to avoid re-indexing.

## Troubleshooting

Common commands:

```bash
# Show compose services and status
docker compose -f docker-compose.dev.yml ps

# Tail recent logs
docker compose -f docker-compose.dev.yml logs --no-color --tail=200

# Stop and remove compose services
docker compose -f docker-compose.dev.yml down --remove-orphans
```

If `./start.sh` exits early with a message about `GEMINI_API_KEY`, set the key in `.env` (or export it in your shell) and retry.

## Contributing / housekeeping
- The repo includes many ad-hoc test/diagnostic files at the root for development; when doing cleanup be conservative: keep anything under `backend/`, `frontend/`, `docker*` and core services. Remove test artifacts only after verifying services start and run correctly.

---
Updated to reflect the current codebase and `start.sh` behavior.