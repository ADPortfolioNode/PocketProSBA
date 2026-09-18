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
HEALTH_URL_PROD="${HEALTH_URL_PROD:-http://localhost:8000/api/health}"
CHAT_URL_DEV="${CHAT_URL_DEV:-http://localhost:5000/api/chat}"
CHAT_URL_PROD="${CHAT_URL_PROD:-http://localhost:8000/api/chat}"
INIT_URL_DEV="${INIT_URL_DEV:-http://localhost:5000/api/startup_init}"
INIT_URL_PROD="${INIT_URL_PROD:-http://localhost:8000/api/startup_init}"
FRONT_URL_DEV="${FRONT_URL_DEV:-http://localhost:3000}"
FRONT_URL_PROD="${FRONT_URL_PROD:-http://localhost:3000}"
DOCKER_PORTS=(80 3000 5000 8000)
LOCAL_PORTS=(80 3000 5000 8000)
HEALTH_ATTEMPTS="${HEALTH_ATTEMPTS:-30}"
HEALTH_DELAY="${HEALTH_DELAY:-2}"

usage() {
  cat <<EOF
Usage: ./start.sh [flags]
Starts ${APP_NAME} with Docker Compose by default.

  --mode prod|dev   Compose file. Default: prod
  --host HOST       Bind host. Default: 0.0.0.0
  --port PORT       Bind port. Default: 8000 prod / 5000 dev
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
  if [[ "$MODE" == "prod" ]]; then PORT=8000; else PORT=5000; fi
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

clear_docker_ports() {
  command -v docker >/dev/null 2>&1 || return 0
  local port
  for port in "$@"; do
    local containers
    containers=$(docker ps --format '{{.ID}} {{.Names}} {{.Ports}}' | grep -E "(:|\s)${port}->" || true)
    [[ -z "$containers" ]] && continue
    echo "[INFO] Freeing Docker port ${port}..."
    while IFS= read -r line; do
      local container_id
      container_id=$(awk '{print $1}' <<< "$line")
      docker stop "$container_id" >/dev/null 2>&1 || true
      docker rm "$container_id" >/dev/null 2>&1 || true
    done <<< "$containers"
  done
}

clear_local_ports() {
  local port
  for port in "$@"; do
    if command -v lsof >/dev/null 2>&1; then
      local pids
      pids=$(lsof -ti tcp:"$port" 2>/dev/null || true)
      [[ -z "$pids" ]] && continue
      echo "[INFO] Freeing local port ${port}..."
      while IFS= read -r pid; do
        [[ -z "$pid" ]] && continue
        kill -9 "$pid" >/dev/null 2>&1 || true
      done <<< "$pids"
    fi
  done
}

docker_prune() {
  wait_for_docker 15 2 || { echo "[ERROR] Skip prune; Docker unavailable."; return 1; }
  echo "[INFO] Pruning unused Docker resources (volumes kept)..."
  docker system prune -af || true
  docker builder prune -af || true
  docker_daemon_ready || wait_for_docker 60 3
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
  export FLASK_APP="${FLASK_APP:-app.py}"
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

clear_docker_ports "${DOCKER_PORTS[@]}"
clear_local_ports "${LOCAL_PORTS[@]}"

if [[ "$LOCAL" == true ]]; then
  echo "[INFO] Starting ${APP_NAME} locally..."
  if [[ -f backend/.env ]]; then
    set -a
    # shellcheck disable=SC1091
    source backend/.env
    set +a
  fi
  if [[ "$MODE" == "prod" ]]; then
    CMD=(gunicorn --bind "$HOST:$PORT" --config backend/gunicorn.conf.py app:app)
  else
    export FLASK_ENV=development
    CMD=(python run.py)
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
[[ "$BUILD" == true ]] && UP_ARGS=(up --build -d)

echo "[INFO] ${APP_NAME} compose=$COMPOSE_FILE mode=$MODE"
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
