#!/usr/bin/env bash
# Codespaces / dev container setup for PocketPro:SBA.
# Installs backend + frontend deps so tests run right away.
# Run the full stack with:  ./start.sh --mode dev --build   (frontend on port 3000)
set -euo pipefail
python -m pip install --upgrade pip
# backend/requirements.txt is the pinned set CI tests against (root requirements.txt is stale).
pip install -r backend/requirements.txt
(cd frontend && npm ci)
# Create runtime env files from templates if missing (same as start.sh). Both are gitignored.
[ -f .env ] || cp .env.template .env
[ -f backend/.env ] || cp backend/.env.example backend/.env
# start.sh sources .env and docker compose reads it via env_file, so a Codespaces secret
# only reaches the app once it is in the (gitignored) .env files. Copy it in if present.
if [ -n "${GEMINI_API_KEY:-}" ]; then
  python - <<'PYEOF'
import os, re
key = os.environ["GEMINI_API_KEY"]
for path in (".env", "backend/.env"):
    text = open(path).read()
    line = "GEMINI_API_KEY=" + key
    if re.search(r"^GEMINI_API_KEY=.*$", text, flags=re.M):
        text = re.sub(r"^GEMINI_API_KEY=.*$", lambda _: line, text, flags=re.M)
    else:
        text = text.rstrip("\n") + "\n" + line + "\n"
    open(path, "w").write(text)
print("GEMINI_API_KEY copied from Codespaces secret into .env and backend/.env (gitignored).")
PYEOF
else
  echo "NOTE: GEMINI_API_KEY is not set. Add it as a Codespaces secret (then rebuild), or put it in .env, before ./start.sh."
fi
echo "Ready. Tests: python -m pytest backend/tests | Frontend: cd frontend && npm run build | Stack: ./start.sh --mode dev --build"
