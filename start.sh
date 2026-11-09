#!/usr/bin/env bash
# PocketPro family standard launcher — NYL workflow on SBA resources
set -euo pipefail

if [ -z "${BASH_VERSION:-}" ]; then
  if command -v bash >/dev/null 2>&1; then
    exec bash "$0" "$@"
  fi
  echo "[ERROR] Bash is required. Use Git Bash, WSL, or a real bash."
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

APP_NAME="${POCKETPRO_APP:-PocketProSBA}"
REQUIRED_KEYS=("GEMINI_API_KEY")
ENV_TEMPLATE="${ENV_TEMPLATE:-.env.template}"
[[ -f "$ENV_TEMPLATE" ]] || ENV_TEMPLATE=".env.example"
BACKEND_ENV_EXAMPLE="${BACKEND_ENV_EXAMPLE:-backend/.env.example}"
COMPOSE_PROD="${COMPOSE_PROD:-docker-compose.yml}"
[[ -f docker-compose.prod.yml ]] && COMPOSE_PROD="docker-compose.prod.yml"
COMPOSE_DEV="${COMPOSE_DEV:-docker-compose.dev.yml}"
HEALTH_URL_DEV="${HEALTH_URL_DEV:-http://localhost:5000/api/health}"
HEALTH_URL_PROD="${HEALTH_URL_PROD:-http://localhost:5000/api/health}"
CHAT_URL_DEV="${CHAT_URL_DEV:-http://localhost:5000/api/chat}"
CHAT_URL_PROD="${CHAT_URL_PROD:-http://localhost:5000/api/chat}"
INIT_URL_DEV="${INIT_URL_DEV:-http://localhost:5000/api/startup_init}"
INIT_URL_PROD="${INIT_URL_PROD:-http://localhost:5000/api/startup_init}"
FRONT_URL_DEV="${FRONT_URL_DEV:-http://localhost:3000}"
FRONT_URL_PROD="${FRONT_URL_PROD:-http://localhost:3000}"
HEALTH_ATTEMPTS="${HEALTH_ATTEMPTS:-30}"
HEALTH_DELAY="${HEALTH_DELAY:-2}"

usage() {
  cat <<EOF
Usage: ./start.sh [flags]
Starts ${APP_NAME} with Docker Compose by default.

  --mode prod|dev   Compose file. Default: prod
  --host HOST       Bind host. Default: 0.0.0.0
  --port PORT       Bind port. Default: 5000
  --local           Host process instead of Docker
  --docker          Force Docker Compose (default)
  --docker-arg ARG  Extra compose arg (repeatable)
  --build           Rebuild images on up
  --no-build        Up without --build
  --prune           docker system prune -af before start (no volumes)
  --diag|--log      Tee compose/startup to logs/build-diag-<ts>.log
  --log-file FILE   Explicit log path
  --no-logfile      stdout/stderr only
  --smoke           Wait /api/health then POST /api/chat (default)
  --no-smoke        Skip health + chat smoke
  --test            After smoke, run property tests if present
  --open            Open frontend URL when healthy
  --no-open         Do not open browser
  --wait-only       Smoke existing stack; do not start
  --help            This message

Examples
  ./start.sh --mode dev --build --smoke --open
  ./sba-up.sh
  ./sba-down.sh
EOF
}

MODE=prod
HOST=0.0.0.0
PORT=""
LOG_FILE=""
NO_LOGFILE=false
DOCKER=true
LOCAL=false
PRUNE=false
BUILD=true
BUILD_DIAG_LOG=false
SMOKE=true
RUN_TESTS=false
OPEN_BROWSER=false
WAIT_ONLY=false
DOCKER_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode) shift; MODE="${1:-}" ;;
    --host) shift; HOST="${1:-}" ;;
    --port) shift; PORT="${1:-}" ;;
    --log-file) shift; LOG_FILE="${1:-}" ;;
    --no-logfile) NO_LOGFILE=true ;;
    --docker) DOCKER=true ;;
    --local) LOCAL=true; DOCKER=false ;;
    --docker-arg)
      shift
      [[ -z "${1:-}" ]] && { echo "Missing value for --docker-arg" >&2; usage; exit 1; }
      DOCKER_ARGS+=("$1")
      ;;
    --prune) PRUNE=true ;;
    --build) BUILD=true ;;
    --no-build) BUILD=false ;;
    --diag|--build-diag-log|--log) BUILD_DIAG_LOG=true ;;
    --smoke) SMOKE=true ;;
    --no-smoke) SMOKE=false ;;
    --test) RUN_TESTS=true ;;
    --open) OPEN_BROWSER=true ;;
    --no-open) OPEN_BROWSER=false ;;
    --wait-only) WAIT_ONLY=true ;;
    --help|-h) usage; exit 0 ;;
    --)
      shift
      while [[ $# -gt 0 ]]; do DOCKER_ARGS+=("$1"); shift; done
      break
      ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
  shift
done

if [[ -z "$PORT" ]]; then
  if [[ "$MODE" == "prod" ]]; then PORT=5000; else PORT=5000; fi
fi

if [[ "$MODE" == "prod" ]]; then
  HEALTH_URL="$HEALTH_URL_PROD"
  CHAT_URL="$CHAT_URL_PROD"
  INIT_URL="$INIT_URL_PROD"
  FRONT_URL="$FRONT_URL_PROD"
else
  HEALTH_URL="$HEALTH_URL_DEV"
  CHAT_URL="$CHAT_URL_DEV"
  INIT_URL="$INIT_URL_DEV"
  FRONT_URL="$FRONT_URL_DEV"
fi

mkdir -p logs uploads chromadb_data

docker_daemon_ready() {
  command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1
}

wait_for_docker() {
  local attempts="${1:-30}" delay="${2:-2}" i
  if ! command -v docker >/dev/null 2>&1; then
    echo "[ERROR] Docker CLI is not on PATH."
    return 1
  fi
  if docker_daemon_ready; then return 0; fi
  echo "[INFO] Waiting for Docker engine..."
  for ((i = 1; i <= attempts; i++)); do
    docker_daemon_ready && { echo "[INFO] Docker engine is ready."; return 0; }
    sleep "$delay"
  done
  echo "[ERROR] Cannot connect to the Docker daemon. Start Docker Desktop, then retry."
  return 1
}

docker_prune() {
  wait_for_docker 15 2 || { echo "[ERROR] Skip prune; Docker unavailable."; return 1; }
  echo "[INFO] Pruning unused Docker resources (volumes kept)..."
  docker system prune -af || true
  docker builder prune -af || true
  docker_daemon_ready || wait_for_docker 60 3
}

# Port-conflict rule: a port held by another app is never freed by killing
# it — the SBA host port bumps +1 until a free port is found (up to +10).
# A holder that is one of this stack's own containers is stale, so it is
# stopped and removed and the original port is kept. This runs immediately
# before compose up (not at the top of the script), so a holder that appears
# during a long --build cannot break the startup. There is deliberately no
# separate "clear the ports first" step: an unconditional clear would kill
# other apps' containers and processes before this resolver ever runs.
SBA_CONTAINERS=(pocketpro-backend pocketpro-frontend chromadb-production pocketpro-backend-dev pocketpro-frontend-dev chromadb-dev)

# Find a real Python 3 interpreter, as an array in PY_CMD (empty when none
# works). On Windows, `python3` is often the Microsoft Store stub (an App
# execution alias): `command -v` finds it, but running it only prints
# "Python was not found..." and exits non-zero. So a candidate only counts
# when it actually runs Python code. Tries python3, then python, then the
# py launcher. The result is cached for the life of the shell.
PY_CMD=()

find_python() {
  if [ "${#PY_CMD[@]}" -gt 0 ]; then
    return 0
  fi
  local cand
  for cand in python3 python; do
    if command -v "$cand" >/dev/null 2>&1 \
        && "$cand" -c "import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)" >/dev/null 2>&1; then
      PY_CMD=("$cand")
      return 0
    fi
  done
  if command -v py >/dev/null 2>&1 \
      && py -3 -c "import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)" >/dev/null 2>&1; then
    PY_CMD=(py -3)
    return 0
  fi
  PY_CMD=()
  return 1
}

port_in_use() {
  local port="$1"

  # 1. Real bind test. We try to bind the port exactly as our server will:
  # a bind fails only when the port is really held. A connect test would be
  # wrong here — when a holder's accept queue is full, the connect times
  # out and looks "free" even though the port is taken.
  if find_python; then
    "${PY_CMD[@]}" -c 'import errno, socket, sys
port = int(sys.argv[1])
for family, addr in ((socket.AF_INET, ("127.0.0.1", port)),
                     (socket.AF_INET6, ("::1", port, 0, 0))):
    try:
        s = socket.socket(family, socket.SOCK_STREAM)
    except OSError:
        continue
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
    except OSError as e:
        s.close()
        if e.errno == errno.EADDRINUSE:
            sys.exit(0)
        continue
    s.close()
sys.exit(1)' "$port" 2>/dev/null
    return $?
  fi

  # 2. ss / netstat listener listings.
  if command -v ss >/dev/null 2>&1; then
    ss -ltn 2>/dev/null | grep -qE ":${port}[[:space:]]"
    return $?
  fi

  if command -v netstat >/dev/null 2>&1; then
    netstat -ltn 2>/dev/null | grep -qE ":${port}[[:space:]]"
    return $?
  fi

  # 3. Windows (Git Bash): ask PowerShell for a listener on the port.
  case "$(uname -s 2>/dev/null || echo unknown)" in
    MINGW*|MSYS*|CYGWIN*)
      if command -v powershell.exe >/dev/null 2>&1; then
        powershell.exe -NoProfile -Command \
          "if (Get-NetTCPConnection -LocalPort ${port} -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1) { exit 0 } else { exit 1 }" \
          >/dev/null 2>&1
        return $?
      fi
      ;;
  esac

  return 1
}

docker_holder_for_port() {
  local port="$1"
  command -v docker >/dev/null 2>&1 || return 0
  # `docker ps -a`, not `docker ps`: a created-but-not-running container
  # still holds its port mapping in Docker's allocator, so it is invisible
  # to `docker ps` (running only) yet compose would still fail to bind.
  # An exited container shows an empty Ports column, so it never matches.
  docker ps -a --format '{{.ID}} {{.Names}} {{.Ports}}' 2>/dev/null \
    | grep -E "(:|\\s)${port}->" | head -n 1 || true
}

# resolve_host_port VAR DEFAULT LABEL — sets $VAR to a free host port.
resolve_host_port() {
  local var_name="$1" default_port="$2" label="$3"
  local port="$default_port" tries=0 stops=0 holder name
  while (( tries <= 10 )); do
    holder=$(docker_holder_for_port "$port")
    if [[ -n "$holder" ]]; then
      name=$(awk '{print $2}' <<< "$holder")
      if [[ " ${SBA_CONTAINERS[*]} " == *" $name "* ]]; then
        # If stopping twice still leaves the holder there (e.g. something
        # recreates it), bump instead of looping forever.
        if (( stops >= 2 )); then
          echo "[WARN] $name still holds port $port after stopping — bumping +1..."
          port=$((port + 1)); tries=$((tries + 1)); continue
        fi
        echo "[INFO] Stopping stale SBA container $name holding port $port..."
        docker stop "$name" >/dev/null 2>&1 || true
        docker rm "$name" >/dev/null 2>&1 || true
        stops=$((stops + 1))
        sleep 1
        continue
      fi
      echo "[INFO] Port $port ($label) is held by $name — bumping +1..."
      port=$((port + 1)); tries=$((tries + 1)); continue
    fi
    if port_in_use "$port"; then
      echo "[INFO] Port $port ($label) is already in use — bumping +1..."
      port=$((port + 1)); tries=$((tries + 1)); continue
    fi
    break
  done
  if (( tries > 10 )); then
    echo "[ERROR] No free port found for $label near $default_port"
    return 1
  fi
  printf -v "$var_name" '%s' "$port"
  if [[ "$port" != "$default_port" ]]; then
    echo "[INFO] $label will use host port $port (was $default_port)"
  fi
  return 0
}

resolve_host_ports() {
  resolve_host_port FRONTEND_HOST_PORT 3000 frontend || return 1
  resolve_host_port BACKEND_HOST_PORT 5000 backend || return 1
  resolve_host_port CHROMA_HOST_PORT 8000 chromadb || return 1
  export FRONTEND_HOST_PORT BACKEND_HOST_PORT CHROMA_HOST_PORT
  # FRONTEND_URL is a CORS origin in the backend: if the frontend host port
  # bumped, the default localhost:3000 origin would no longer match the page
  # the browser actually loaded. Follow the bump, but never override a
  # custom FRONTEND_URL the user set (e.g. a deployed URL).
  if [[ -z "${FRONTEND_URL:-}" || "$FRONTEND_URL" == "http://localhost:3000" ]]; then
    export FRONTEND_URL="http://localhost:${FRONTEND_HOST_PORT}"
  fi
  # Health/smoke URLs and the final ready line must follow the bumped ports.
  HEALTH_URL="http://localhost:${BACKEND_HOST_PORT}/api/health"
  CHAT_URL="http://localhost:${BACKEND_HOST_PORT}/api/chat"
  INIT_URL="http://localhost:${BACKEND_HOST_PORT}/api/startup_init"
  FRONT_URL="http://localhost:${FRONTEND_HOST_PORT}"
  echo "[INFO] Ports: frontend=${FRONTEND_HOST_PORT} backend=${BACKEND_HOST_PORT} chromadb=${CHROMA_HOST_PORT}"
}

ensure_env() {
  if [[ ! -f .env ]]; then
    if [[ -f "$ENV_TEMPLATE" ]]; then
      echo "[INFO] Creating .env from $ENV_TEMPLATE"
      cp "$ENV_TEMPLATE" .env
    else
      echo "[ERROR] Missing .env and $ENV_TEMPLATE"
      exit 1
    fi
  fi
  if [[ -f "$BACKEND_ENV_EXAMPLE" && ! -f backend/.env ]]; then
    echo "[INFO] Creating backend/.env from $BACKEND_ENV_EXAMPLE"
    cp "$BACKEND_ENV_EXAMPLE" backend/.env
  fi
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
  local key
  for key in "${REQUIRED_KEYS[@]}"; do
    local val="${!key:-}"
    if [[ -z "$val" || "$val" == "your_api_key_here" ]]; then
      echo "[ERROR] Missing $key in .env"
      exit 1
    fi
  done
  if [[ -z "${REACT_APP_BACKEND_URL:-}" ]]; then
    if [[ "$LOCAL" == true ]]; then
      export REACT_APP_BACKEND_URL="http://localhost:${PORT}"
    else
      export REACT_APP_BACKEND_URL="$FRONT_URL"
    fi
    echo "[INFO] REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}"
  fi
  export HOST PORT
  export FLASK_ENV="${FLASK_ENV:-production}"
  export FLASK_APP="${FLASK_APP:-wsgi:application}"
  export PYTHONPATH="$ROOT:$ROOT/backend:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
}

compose_cmd() {
  if command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose"
  elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    echo "docker compose"
  else
    echo ""
  fi
}

wait_health() {
  local i
  echo "[INFO] Waiting for health: $HEALTH_URL"
  for ((i = 1; i <= HEALTH_ATTEMPTS; i++)); do
    if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
      echo "[OK] Health passed ($i/${HEALTH_ATTEMPTS})"
      return 0
    fi
    sleep "$HEALTH_DELAY"
  done
  echo "[ERROR] Health check failed: $HEALTH_URL"
  return 1
}

startup_init() {
  echo "[INFO] NYL-style workflow init: POST $INIT_URL"
  local code
  code=$(curl -sS -o /tmp/sba_init_body -w "%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d '{"force":true}' "$INIT_URL" || true)
  if [[ "$code" =~ ^2 ]]; then
    echo "[OK] startup_init HTTP $code"
    return 0
  fi
  echo "[WARN] startup_init not available (HTTP ${code:-000}) — using health + chat smoke"
  return 0
}

smoke_chat() {
  echo "[INFO] Chat smoke: POST $CHAT_URL"
  local body
  body=$(curl -sS -X POST -H "Content-Type: application/json" \
    -d '{"message":"hello"}' "$CHAT_URL" || true)
  if [[ -z "$body" ]]; then
    echo "[ERROR] Chat smoke returned empty"
    return 1
  fi
  echo "[OK] Chat smoke returned payload (${#body} bytes)"
}

run_property_tests() {
  echo "[INFO] --test: property workflow tests"
  if [[ -f scripts/run_full_diag.sh ]]; then
    bash scripts/run_full_diag.sh
  elif [[ -d backend/tests ]] && command -v pytest >/dev/null 2>&1; then
    pytest backend/tests -q
  elif [[ -f health_check.py ]]; then
    python health_check.py
  else
    echo "[WARN] No property test runner found; health+chat smoke already ran."
  fi
}

open_front() {
  echo "[INFO] Opening $FRONT_URL"
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$FRONT_URL" >/dev/null 2>&1 || true
  elif command -v open >/dev/null 2>&1; then
    open "$FRONT_URL" >/dev/null 2>&1 || true
  elif command -v start >/dev/null 2>&1; then
    start "$FRONT_URL" >/dev/null 2>&1 || true
  fi
}

post_start() {
  [[ "$SMOKE" == true ]] || { echo "[INFO] Smoke skipped (--no-smoke)"; return 0; }
  wait_health || return 1
  startup_init
  smoke_chat || return 1
  [[ "$RUN_TESTS" == true ]] && run_property_tests
  [[ "$OPEN_BROWSER" == true ]] && open_front
  echo "[OK] ${APP_NAME} workflow ready  front=$FRONT_URL  health=$HEALTH_URL"
}

if [[ "$WAIT_ONLY" == true ]]; then
  post_start
  exit $?
fi

ensure_env

if [[ "$PRUNE" == true ]]; then
  docker_prune || exit 1
fi

if [[ "$LOCAL" == true ]]; then
  echo "[INFO] Starting ${APP_NAME} locally..."
  if [[ -f backend/.env ]]; then
    set -a
    # shellcheck disable=SC1091
    source backend/.env
    set +a
  fi
  if [[ "$MODE" == "prod" ]]; then
    CMD=(gunicorn --config backend/gunicorn.conf.py --bind "$HOST:$PORT" wsgi:application)
  else
    export FLASK_ENV=development
    CMD=(gunicorn --bind "$HOST:$PORT" --reload --workers 1 --threads 4 --timeout 120 wsgi:application)
  fi
  if [[ "$NO_LOGFILE" == true ]]; then
    "${CMD[@]}" &
  else
    [[ -z "$LOG_FILE" ]] && LOG_FILE="logs/app-$(date +%Y%m%d-%H%M%S).log"
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[INFO] Logging to $LOG_FILE"
    "${CMD[@]}" 2>&1 | tee -a "$LOG_FILE" &
  fi
  post_start
  wait
  exit $?
fi

wait_for_docker 30 2 || exit 1

if [[ "$MODE" == "prod" ]]; then
  COMPOSE_FILE="$COMPOSE_PROD"
else
  COMPOSE_FILE="$COMPOSE_DEV"
fi
[[ -f "$COMPOSE_FILE" ]] || { echo "[ERROR] Missing $COMPOSE_FILE"; exit 1; }

DOCKER_COMPOSE_CMD="$(compose_cmd)"
[[ -n "$DOCKER_COMPOSE_CMD" ]] || { echo "[ERROR] docker compose not found"; exit 1; }

UP_ARGS=(up -d)
# Build first, on its own: with `up --build` the port check would run before
# a ~16-minute build, and a holder appearing during the build would still
# break container startup. Building separately means resolve_host_ports below
# runs immediately before `up`.
if [[ "$BUILD" == true ]]; then
  echo "[INFO] Building images..."
  if [[ "$BUILD_DIAG_LOG" == true ]]; then
    [[ -z "$LOG_FILE" ]] && LOG_FILE="logs/build-diag-$(date +%Y%m%d-%H%M%S).log"
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[INFO] Diagnostic log: $LOG_FILE"
    $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" build 2>&1 | tee -a "$LOG_FILE"
  else
    $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" build
  fi
fi

echo "[INFO] ${APP_NAME} compose=$COMPOSE_FILE mode=$MODE"
resolve_host_ports || exit 1
if [[ "$BUILD_DIAG_LOG" == true ]]; then
  [[ -z "$LOG_FILE" ]] && LOG_FILE="logs/build-diag-$(date +%Y%m%d-%H%M%S).log"
  mkdir -p "$(dirname "$LOG_FILE")"
  echo "[INFO] Diagnostic log: $LOG_FILE"
  $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" "${UP_ARGS[@]}" "${DOCKER_ARGS[@]}" 2>&1 | tee -a "$LOG_FILE"
else
  $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" "${UP_ARGS[@]}" "${DOCKER_ARGS[@]}"
fi

post_start
echo "[INFO] Inspect: $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE ps"
