# Deploying PocketPro:SBA

## One backend entry point

Every launcher starts the same WSGI app, `wsgi:application` (`wsgi.py` → `backend.app.create_app()`):

| Where | Command |
|---|---|
| Procfile (Fly / Render / Heroku-style hosts) | `gunicorn wsgi:application --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 4 --timeout 60` |
| `Dockerfile.production` / `docker-compose.yml` | `gunicorn wsgi:application --bind 0.0.0.0:5000 ...` |
| `Dockerfile.dev` / `docker-compose.dev.yml` | `gunicorn wsgi:application --reload ...` with `FLASK_ENV=development` |
| `start.sh --local`, `start-dev.sh`, `start-dev-full.sh` | `gunicorn ... wsgi:application` |
| Windows `.bat` / `.ps1` launchers (gunicorn has no Windows build) | `python wsgi.py` with `FLASK_ENV=development`, `PORT=5000` |

`wsgi.py` defaults `FLASK_ENV` to `production`, so it refuses to start without `SECRET_KEY` unless you export `FLASK_ENV=development` first.

Smoke test after any deploy: `GET /health`, `GET /api/health` and `GET /api/info` must all return 200.

## Production environment variables

Set these in the host's secret store (Fly secrets, Render env, etc.), never in a committed file. `.env.example` lists them with placeholders.

| Variable | Required | What it does |
|---|---|---|
| `FLASK_ENV` | yes | `production`. Turns on the production config and makes `SECRET_KEY` mandatory. |
| `SECRET_KEY` | yes | Flask signing key. Long and random: `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Rotating it invalidates existing sessions/tokens. |
| `GEMINI_API_KEY` | yes, for chat/RAG answers | Google AI Studio key. Without it the app runs but LLM answers degrade. Restrict the key to the Generative Language API. |
| `FRONTEND_URL` | yes | Public URL of the frontend (e.g. `https://pocket-pro-sba.vercel.app`). Always allowed as a CORS origin. |
| `CORS_ALLOWED_ORIGINS` | optional | Extra allowed origins, comma-separated, exact scheme+host (e.g. a custom domain). No wildcards. |
| `TRUSTED_PROXY_COUNT` | **yes, behind a proxy** | Number of reverse proxies in front of the app whose `X-Forwarded-For` is trusted. Set **`1`** behind Fly, Render, Vercel rewrites or the compose nginx (one hop); `0` (default) only when clients hit gunicorn directly. Too low and every client shares the proxy's IP (one user can rate-limit everyone); too high and clients can spoof their IP to dodge limits. |
| `RATELIMIT_STORAGE_URI` | **yes, with >1 worker** | Flask-Limiter (4.1.1) storage. `memory://` (default) is per process: the Procfile runs 2 gunicorn workers, so each keeps its own counters and the effective limit doubles (more with several machines). Use Redis, e.g. `redis://default:<password>@host:6379/0` (Upstash/Fly Redis/Render Key Value). |
| `AUTH_REQUIRED` | no | Defaults to **`true`** in every environment. Chat/LLM, RAG, document upload/list, orchestrator and assistant routes then need `Authorization: Bearer <token>` from `POST /api/auth/login` (or `/api/login`) and answer `401` JSON (`code`: `token_missing`, `token_expired` or `token_invalid`) without one. Health, info, `/api/auth/*` and public SBA content (`/api/sba/*`, `/api/programs`, `/api/rag/sba-overview`) stay open. Set `AUTH_REQUIRED=false` **only for local demos**; the app logs an error if production runs with it off. |
| `JWT_ACCESS_TTL_SECONDS` | optional | Access-token lifetime, default `3600` (1 hour). A client holding a still-valid token can call `POST /api/auth/refresh` for a fresh one; after expiry the user logs in again (the SPA redirects to `/login?next=<page>`). |
| `JWT_SECRET_KEY` | optional | Signs access tokens (HS256). Defaults to `SECRET_KEY`. Rotating whichever is used signs everyone out. Tokens are also bound to the user's password, so a password reset ends that user's older sessions. |
| `RATELIMIT_ENABLED` | no | Defaults to on. `false` turns rate limiting off (tests/debugging only). |
| `RATELIMIT_AUTH`, `RATELIMIT_LLM` | optional | Limit strings for auth and LLM routes (defaults `10 per minute;100 per hour` and `30 per minute;500 per hour`). |
| `MAX_CONTENT_LENGTH` | optional | Max request body in bytes, uploads included. Default 16 MB (`16777216`); larger requests get a 413. |
| `DATABASE_URL` | recommended | SQLAlchemy URL. Default is SQLite in the working dir, which is lost on redeploy unless it sits on a persistent volume. Use Postgres (`postgresql://user:pass@host:5432/db`) for anything shared. |
| `CHROMADB_HOST`, `CHROMADB_PORT` | if using Chroma | Chroma server. Compose uses `chromadb/chroma:0.5.3` for the persisted 0.5.x database schema; the backend pins `chromadb==0.4.24` to retain its Pydantic v1 AI stack and uses the compatible HTTP CRUD/query API. Avoid opening the same data directory with Chroma 0.4.x. |
| `PORT` | set by host | Port gunicorn binds (Procfile). |
| `FLASK_DEBUG` (or `DEBUG`) | no | Debug is **off in every environment** unless `FLASK_DEBUG=1` (or `DEBUG=1`) is set. Never set it in production: debug mode logs password-reset tokens to the server log. |
| `PASSWORD_RESET_DELIVERY` | yes, before enabling password reset | Not an env var: an `app.config` hook. Set `app.config["PASSWORD_RESET_DELIVERY"]` to a callable `(email, token) -> None` that sends the token (email gateway, queue). Reset tokens are never returned in the HTTP response; without this hook, production users never receive one (a warning is logged). |
| `SBA_KB_LIVE_DIR` | no | Overrides where live SBA API ingests are written (the test suite points it at a temp dir). Leave unset in production: keyword RAG reads `backend/knowledge_base/`. |

Minimum production set: `FLASK_ENV=production`, `SECRET_KEY`, `GEMINI_API_KEY`, `FRONTEND_URL`, `TRUSTED_PROXY_COUNT=1`, `RATELIMIT_STORAGE_URI=redis://...`, and a persistent `DATABASE_URL`.

## Deploy backend on Render

`render.yaml` (repo root) is a Render Blueprint: one Python web service `pocketpro-sba-api` (Starter plan, `pip install -r backend/requirements.txt` plus `redis` for the limiter storage, the Procfile's gunicorn command, health check `/api/health`, 1 GB disk at `/var/data`) plus a free Key Value (Redis) `pocketpro-sba-ratelimit` for rate limits.

1. Render dashboard → **New → Blueprint** → connect `ADPortfolioNode/PocketProSBA`, branch `main`.
2. Fill the prompted (`sync: false`) values: `GEMINI_API_KEY` (a **new, rotated** key), `FRONTEND_URL` (the Vercel URL), optionally `CORS_ALLOWED_ORIGINS`, `GOOGLE_API_KEY`, `SBA_API_KEY`, `SBA_CONTENT_API_KEY`. Leave `PASSWORD_RESET_DELIVERY` blank (see below). Apply.
3. Wait for the deploy to go live; note the URL (`https://pocketpro-sba-api.onrender.com` or similar).
4. Vercel → project `pocket-pro-sba` → Settings → Environment Variables: `REACT_APP_API_URL` = that Render URL (with or without `/api`), then **redeploy** (it is baked in at build time).

| Variable | Set by | Value |
|---|---|---|
| `PYTHON_VERSION` | render.yaml | `3.11.11` (chroma-hnswlib does not build on 3.12) |
| `FLASK_ENV` | render.yaml | `production` |
| `SECRET_KEY` | render.yaml | `generateValue: true` (random 256-bit) |
| `AUTH_REQUIRED` | render.yaml | `true` |
| `TRUSTED_PROXY_COUNT` | render.yaml | `1` (Render's proxy) |
| `RATELIMIT_STORAGE_URI` | render.yaml | Key Value `connectionString` (private network) |
| `DATABASE_URL` | render.yaml | `sqlite:////var/data/pocketpro.db` (on the disk) |
| `UPLOAD_FOLDER` | render.yaml | `/var/data/uploads` |
| `GEMINI_API_KEY` | you | rotated Google AI Studio key |
| `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS` | you | Vercel URL / extra origins |
| `GOOGLE_API_KEY`, `SBA_API_KEY`, `SBA_CONTENT_API_KEY` | you | optional |
| `PASSWORD_RESET_DELIVERY` | you | placeholder only: the code reads an `app.config` callable, not this env var |

Disk notes: a disk needs a paid instance and turns off zero-downtime deploys. `backend/routes/documents.py` still writes to a relative `uploads/` (ignores `UPLOAD_FOLDER`), and `backend/instance/task_memory.json` is not on the disk, so both reset on redeploy until the code reads env paths.

Smoke checks after deploy (`API=https://<your-service>.onrender.com`):

```bash
curl -fsS $API/api/health                                   # 200 JSON
curl -s -o /dev/null -w "%{http_code}\n" $API/api/documents/list   # 401 (auth on)
curl -s -o /dev/null -w "%{http_code}\n" -H "Origin: https://<vercel-app>" -I $API/api/health  # 200, check Access-Control-Allow-Origin
```

Then open the Vercel site, register, log in and send one chat message.

**Security must-dos before going public**

- **Rotate the Google API key** leaked in commit `fecb828` (Google Cloud console → Credentials → delete/regenerate), restrict the new one to the Generative Language API, and put it only in Render.
- **Treat the old committed `SECRET_KEY` as compromised.** Never reuse it; the Blueprint generates a fresh one.
- **Wire password-reset email**: set `app.config["PASSWORD_RESET_DELIVERY"]` to a callable `(email, token)` that sends mail (e.g. an SMTP/Resend/SendGrid helper). Until then production users can't receive reset tokens.

## Docker Compose

`docker compose up --build` (prod-like) and `docker compose -f docker-compose.dev.yml up --build` work on a fresh clone without a `.env`: the `env_file` entries are optional and the prod compose falls back to a clearly-named local-only `SECRET_KEY`. For anything reachable from the internet, put a real `SECRET_KEY` (and `GEMINI_API_KEY`) in `.env` or the shell; Compose reads `.env` for `${...}` interpolation. Requires Docker Compose v2.24+ (for `env_file: required: false`).

## Vercel (frontend)

The frontend is a Create React App in `frontend/`. Both possible Vercel layouts are covered in the repo:

- Vercel project **Root Directory = `frontend`** → `frontend/vercel.json` (install `npm ci`, build `npm run build`, output `build`, SPA rewrites).
- Root Directory = repo root → `vercel.json` (installs and builds inside `frontend/`, output `frontend/build`).

Vercel sets `CI=1` during builds, so react-scripts treats every ESLint warning as an error. That is what broke the Vercel deploys from Sep 18 on (the build had ~15-20 warnings). GitHub CI now builds with `CI=true` too, so a warning fails the PR before it can reach Vercel. Keep the build warning-free rather than adding `CI=false`.

Dashboard settings to check (Vercel → project `pocket-pro-sba` → Settings):
1. **Build & Development Settings**: leave Build Command, Output Directory and Install Command on their defaults (no override toggled), so `vercel.json` applies. Framework Preset: Create React App.
2. **Root Directory**: `frontend` (recommended).
3. **Node.js Version**: 22.x (20.x also works). Older versions are discontinued on Vercel and fail the build.
4. **Environment Variables**: `REACT_APP_API_URL` = the public backend URL (e.g. `https://<backend-host>/api`). It is baked in at build time, so redeploy after changing it. Without it the app calls `/api` on the Vercel domain, which has no backend. Add the Vercel domain to the backend's `FRONTEND_URL` / `CORS_ALLOWED_ORIGINS`.
