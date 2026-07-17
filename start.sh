set -euo pipefail

if [ -z "${BASH_VERSION:-}" ]; then
  if command -v bash >/dev/null 2>&1; then
    exec bash "$0" "$@"
  fi
  echo "[ERROR] Bash is required to run this script."
  echo "Please use Git Bash, WSL, or install a Bash shell, then rerun ./start.sh."
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

usage() {
  cat <<'EOF'
Usage: ./start.sh [--mode prod|dev] [--host HOST] [--port PORT] [--local] [--docker] [--docker-arg ARG] [--prune] [--build] [--diag] [--build-diag-log] [--log] [--log-file FILE] [--no-logfile] [--help]

Starts PocketProSBA with Docker Compose by default.

Options:
  --mode prod|dev      Use production compose or development compose. Default: dev
  --host HOST          Host interface to bind. Default: 0.0.0.0
  --port PORT          Port to bind. Default: 8000 for prod, 5000 for dev
  --local              Run the app directly on the host instead of Docker
  --docker             Force Docker Compose startup (default behavior)
  --docker-arg ARG     Append an additional Docker Compose argument. Can be repeated.
  --prune              Run Docker system prune before startup (auto-yes)
  --build              Explicitly request rebuild and bring up Docker Compose
  --diag               Alias for --build-diag-log; capture build/startup output to a diagnostic log
  --build-diag-log     Capture Docker Compose build/startup output to a diagnostic log file
  --log                Enable build/startup logging to a default diagnostic log file
  --log-file FILE      Log output file for local startup or diagnostic logging
  --no-logfile         Send output only to stdout/stderr
  --help               Show this help message
EOF
}

DOCKER_PORTS=(80 3000 5000 8000)
LOCAL_PORTS=(80 3000 5000 8000)

clear_docker_ports() {
  if ! command -v docker >/dev/null 2>&1; then
    return
  fi

  local port
  for port in "$@"; do
    local containers
    containers=$(docker ps --format '{{.ID}} {{.Names}} {{.Ports}}' | grep -E "(:|\s)${port}->" || true)
    if [[ -n "$containers" ]]; then
      echo "[INFO] Found Docker containers using port ${port}. Stopping and removing them..."
      while IFS= read -r line; do
        local container_id
        container_id=$(awk '{print $1}' <<< "$line")
        echo "  - stopping ${container_id}"
        docker stop "$container_id" >/dev/null 2>&1 || true
        echo "  - removing ${container_id}"
        docker rm "$container_id" >/dev/null 2>&1 || true
      done <<< "$containers"
    fi
  done
}

clear_local_ports() {
  local port
  for port in "$@"; do
    if command -v lsof >/dev/null 2>&1; then
      local pids
      pids=$(lsof -ti tcp:"$port" 2>/dev/null || true)
      if [[ -n "$pids" ]]; then
        echo "[INFO] Found local processes using port ${port}. Stopping them..."
        while IFS= read -r pid; do
          [[ -z "$pid" ]] && continue
          echo "  - stopping PID ${pid}"
          kill -9 "$pid" >/dev/null 2>&1 || true
        done <<< "$pids"
      fi
    elif command -v netstat >/dev/null 2>&1; then
      local lines pids
      lines=$(netstat -ano | grep -E "(:|\.)${port} .*LISTENING" || true)
      if [[ -n "$lines" ]]; then
        echo "[INFO] Found local processes using port ${port}. Stopping them..."
        pids=$(printf '%s\n' "$lines" | awk '{print $5}' | tr -d '\r' | sort -u)
        while IFS= read -r pid; do
          [[ -z "$pid" || ! "$pid" =~ ^[0-9]+$ ]] && continue
          echo "  - stopping PID ${pid}"
          if command -v taskkill >/dev/null 2>&1; then
            taskkill /PID "$pid" /F >/dev/null 2>&1 || true
          else
            kill -9 "$pid" >/dev/null 2>&1 || true
          fi
        done <<< "$pids"
      fi
    fi
  done
}

clear_service_ports() {
  clear_docker_ports "${DOCKER_PORTS[@]}"
  clear_local_ports "${LOCAL_PORTS[@]}"
}

docker_daemon_ready() {
  command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1
}

# Wait until the Docker engine answers, or return 1.
# Useful on Windows when Docker Desktop is still starting (or recovering).
wait_for_docker() {
  local attempts="${1:-30}"
  local delay="${2:-2}"
  local i

  if ! command -v docker >/dev/null 2>&1; then
    echo "[ERROR] Docker CLI is not installed or not on PATH."
    return 1
  fi

  if docker_daemon_ready; then
    return 0
  fi

  echo "[INFO] Waiting for Docker engine to become ready..."
  for ((i = 1; i <= attempts; i++)); do
    if docker_daemon_ready; then
      echo "[INFO] Docker engine is ready."
      return 0
    fi
    sleep "$delay"
  done

  echo "[ERROR] Cannot connect to the Docker daemon."
  echo "        On Windows, start Docker Desktop and wait until it shows 'Engine running'."
  echo "        Then re-run: ./start.sh ..."
  echo "        Quick check: docker info"
  return 1
}

docker_prune() {
  if ! wait_for_docker 15 2; then
    echo "[ERROR] Skipping prune because Docker is not available."
    return 1
  fi

  echo "[INFO] Pruning unused Docker resources..."
  # Avoid --volumes by default risk of wiping named volumes; keep -af for unused images/containers/networks.
  # builder prune can momentarily stress Docker Desktop on Windows; tolerate failure and re-check daemon.
  docker system prune -af || true
  docker builder prune -af || true

  if ! docker_daemon_ready; then
    echo "[WARN] Docker engine became unreachable during prune (common on Docker Desktop after large cleanups)."
    echo "[INFO] Waiting for Docker to recover..."
    if ! wait_for_docker 60 3; then
      echo "[ERROR] Docker did not recover after prune. Start Docker Desktop, then re-run without --prune:"
      echo "        ./start.sh --build --diag"
      return 1
    fi
  fi
}

MODE=prod
HOST=0.0.0.0
PORT=""
LOG_FILE=""
NO_LOGFILE=false
DOCKER=true
LOCAL=false
PRUNE=false
BUILD_DIAG_LOG=false
DOCKER_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      shift
      MODE="${1:-}"
      ;;
    --host)
      shift
      HOST="${1:-}"
      ;;
    --port)
      shift
      PORT="${1:-}"
      ;;
    --log-file)
      shift
      LOG_FILE="${1:-}"
      ;;
    --no-logfile)
      NO_LOGFILE=true
      ;;
    --docker)
      DOCKER=true
      ;;
    --local)
      LOCAL=true
      DOCKER=false
      ;;
    --docker-arg)
      shift
      if [[ -z "${1:-}" ]]; then
        echo "Missing value for --docker-arg" >&2
        usage
        exit 1
      fi
      DOCKER_ARGS+=("$1")
      ;;
    --prune)
      PRUNE=true
      ;;
    --build)
      # Explicit build request; Docker Compose always builds by default.
      ;;
    --diag)
      BUILD_DIAG_LOG=true
      ;;
    --build-diag-log)
      BUILD_DIAG_LOG=true
      ;;
    --log)
      BUILD_DIAG_LOG=true
      ;;
    --)
      shift
      while [[ $# -gt 0 ]]; do
        DOCKER_ARGS+=("$1")
        shift
      done
      break
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done

if [[ -z "$PORT" ]]; then
  if [[ "$MODE" == "prod" ]]; then
    PORT=8000
  else
    PORT=5000
  fi
fi

mkdir -p logs uploads chromadb_data

if [[ ! -f .env ]]; then
  if [[ -f .env.template ]]; then
    echo "Creating .env from .env.template..."
    cp .env.template .env
    echo "Please edit .env before starting if you need real credentials." >&2
  else
    echo "Missing .env and .env.template; cannot continue." >&2
    exit 1
  fi
fi

if [[ ! -f backend/.env ]]; then
  if [[ -f backend/.env.example ]]; then
    echo "Creating backend/.env from backend/.env.example..."
    cp backend/.env.example backend/.env
  else
    echo "Missing backend/.env and backend/.env.example; cannot continue." >&2
    exit 1
  fi
fi

set -a
source .env
set +a
if [[ -z "${GEMINI_API_KEY:-}" ]] || [[ "${GEMINI_API_KEY}" == "your_api_key_here" ]]; then
  echo "[ERROR] Missing GEMINI_API_KEY in .env. Please set it before starting." >&2
  echo "        You can get a key from: https://makersuite.google.com/app/apikey" >&2
  exit 1
fi

if [[ -z "${REACT_APP_BACKEND_URL:-}" ]]; then
  if [[ "$LOCAL" == true ]]; then
    export REACT_APP_BACKEND_URL="http://localhost:${PORT}"
    echo "[INFO] REACT_APP_BACKEND_URL not set. Defaulting to local backend: ${REACT_APP_BACKEND_URL}"
  else
    export REACT_APP_BACKEND_URL="http://localhost:3000"
    echo "[INFO] REACT_APP_BACKEND_URL not set. Defaulting to Docker proxy: ${REACT_APP_BACKEND_URL}"
  fi
fi
export HOST PORT
export FLASK_ENV="${FLASK_ENV:-production}"
export FLASK_APP="${FLASK_APP:-app.py}"
export PYTHONPATH="$ROOT:$ROOT/backend:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

if [[ "$PRUNE" == true ]]; then
  docker_prune || exit 1
fi

clear_service_ports

if [[ "$LOCAL" == true ]]; then
  echo "Starting PocketProSBA locally in host mode..."
  # Ensure backend/.env is sourced for local runs if it exists
  if [[ -f backend/.env ]]; then
    set -a
    source backend/.env
    set +a
  fi
else
  if ! wait_for_docker 30 2; then
    exit 1
  fi

  if [[ "$MODE" == "prod" ]]; then
    if [[ -f "docker-compose.prod.yml" ]]; then
      COMPOSE_FILE="docker-compose.prod.yml"
    else
      COMPOSE_FILE="docker-compose.yml"
    fi
  else
    COMPOSE_FILE="docker-compose.dev.yml"
  fi

  if command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker-compose"
  elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
  else
    echo "docker-compose not found. Install Docker Compose or Docker Compose plugin, or run with --local instead." >&2
    exit 1
  fi

  echo "Initializing Docker Compose using $COMPOSE_FILE..."
  if [[ "$BUILD_DIAG_LOG" == true ]]; then
    if [[ -z "$LOG_FILE" ]]; then
      LOG_FILE="logs/build-diag-$(date +%Y%m%d-%H%M%S).log"
    fi
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "Logging Docker Compose output to: $LOG_FILE"
    $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" up --build "${DOCKER_ARGS[@]}" 2>&1 | tee -a "$LOG_FILE"
  else
    $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" up --build -d "${DOCKER_ARGS[@]}"
  fi
  echo "Docker Compose started. Use $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE ps to inspect services."
  exit 0
fi

if [[ "$MODE" == "prod" ]]; then
  echo "Starting PocketProSBA in production mode..."
  CMD=(gunicorn --bind "$HOST:$PORT" --config backend/gunicorn.conf.py app:app)
else
  echo "Starting PocketProSBA in development mode..."
  export FLASK_ENV=development
  CMD=(python run.py)
fi

if [[ "$NO_LOGFILE" == true ]]; then
  exec "${CMD[@]}"
else
  if [[ -z "$LOG_FILE" ]]; then
    LOG_FILE="logs/app-$(date +%Y%m%d-%H%M%S).log"
  fi
  mkdir -p "$(dirname "$LOG_FILE")"
  echo "Logging output to: $LOG_FILE"
  exec "${CMD[@]}" 2>&1 | tee -a "$LOG_FILE"
fi
