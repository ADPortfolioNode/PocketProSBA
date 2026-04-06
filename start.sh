<<<<<<< HEAD
#!/bin/bash
# start.sh - Optimized startup script for PocketProSBA
# Usage:
#   ./start.sh [--dev] [--troubleshoot] [--no-build] [--force-fresh]
#
# Default: Fresh docker build and start
# Flags:
#   --dev           Start in development mode
#   --troubleshoot  Start in troubleshoot mode
#   --no-build      Skip docker build
#   --force-fresh   Force fresh build and start

set -e

# Parse flags
device_mode=""
troubleshoot_mode=""
skip_build=""
force_fresh=""
for arg in "$@"; do
  case $arg in
    --dev)
      device_mode=1
      ;;
    --troubleshoot)
      troubleshoot_mode=1
      ;;
    --no-build)
      skip_build=1
      ;;
    --force-fresh)
      force_fresh=1
      ;;
  esac
done

# Helper: Check for port conflicts
check_port_conflict() {
  # Check if port 80 or 3000 is in use
  if lsof -i :80 >/dev/null 2>&1 || lsof -i :3000 >/dev/null 2>&1; then
    return 0
  else
    return 1
  fi
}

# Helper: Run docker build
run_docker_build() {
  echo "[INFO] Running docker compose build..."
  docker-compose build --no-cache
}

# Helper: Start docker compose
run_docker_up() {
  echo "[INFO] Starting docker compose..."
  docker-compose up -d
}

# Helper: Start dev mode
run_dev_mode() {
  echo "[INFO] Starting in development mode..."
  ./start-dev.sh
}

# Helper: Start troubleshoot mode
run_troubleshoot_mode() {
  echo "[INFO] Starting in troubleshoot mode..."
  ./docker_troubleshoot.sh
}

# Main logic
if check_port_conflict; then
  echo "[WARN] Port conflict detected. Forcing fresh build and start."
  run_docker_build
  run_docker_up
  exit 0
else
  case 1 in
    $force_fresh)
      echo "[INFO] Force fresh build requested."
      run_docker_build
      run_docker_up
      ;;
    $device_mode)
      run_dev_mode
      ;;
    $troubleshoot_mode)
      run_troubleshoot_mode
      ;;
    *)
      if [ -z "$skip_build" ]; then
        run_docker_build
      fi
      run_docker_up
      ;;
  esac
fi

echo "[SUCCESS] Startup complete."
=======
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

usage() {
  cat <<'EOF'
Usage: ./start.sh [--mode prod|dev] [--host HOST] [--port PORT] [--local] [--docker] [--docker-arg ARG] [--] [docker compose args...] [--log-file FILE] [--no-logfile] [--help]

Starts PocketProSBA with Docker compose startup by default.

Options:
  --mode prod|dev    Use production compose or development compose. Default: dev
  --host HOST        Host interface to bind. Default: 0.0.0.0
  --port PORT        Port to bind. Default: 8000 for prod, 5000 for dev
  --local            Run the app locally on the host instead of in Docker
  --docker           Force Docker compose startup (default behavior)
  --docker-arg ARG   Append an additional docker compose argument. Can be repeated.
  --                 Forward all remaining arguments directly to docker compose.
  --log-file FILE    Log output file. Default: logs/app-<timestamp>.log
  --no-logfile       Send output only to stdout/stderr
  --help             Show this help message
EOF
}

DOCKER_PORTS=(5000 8000 3000)
LOCAL_PORTS=(5000 8000 3000)

clear_docker_ports() {
  if ! command -v docker >/dev/null 2>&1; then
    return
  fi

  local port
  for port in "$@"; do
    local containers
    containers=$(docker ps --format '{{.ID}} {{.Names}} {{.Ports}}' | grep -E "(:|\s)${port}->" || true)
    if [[ -n "$containers" ]]; then
      echo "Found Docker containers using port ${port}. Stopping and removing them..."
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
  if ! command -v netstat >/dev/null 2>&1; then
    return
  fi

  local port
  for port in "$@"; do
    local lines pids
    lines=$(netstat -ano | grep -E "(:|\.)${port} .*LISTENING" || true)
    if [[ -n "$lines" ]]; then
      echo "Found local processes using port ${port}. Stopping them..."
      pids=$(printf '%s\n' "$lines" | awk '{print $5}' | tr -d '\r' | sort -u)
      while IFS= read -r pid; do
        if [[ -z "$pid" || ! "$pid" =~ ^[0-9]+$ ]]; then
          continue
        fi
        echo "  - stopping PID ${pid}"
        if command -v taskkill >/dev/null 2>&1; then
          taskkill /PID "$pid" /F >/dev/null 2>&1 || true
        else
          kill -9 "$pid" >/dev/null 2>&1 || true
        fi
      done <<< "$pids"
    fi
  done
}

clear_service_ports() {
  clear_docker_ports "${DOCKER_PORTS[@]}"
  clear_local_ports "${LOCAL_PORTS[@]}"
}

MODE=dev
HOST=0.0.0.0
PORT=""
LOG_FILE=""
NO_LOGFILE=false
DOCKER=true
LOCAL=false
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

# Load environment variables from .env
set -a
source .env
set +a

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
  echo "Missing GEMINI_API_KEY in .env. Please set it before starting." >&2
  exit 1
fi

export HOST PORT
export FLASK_ENV="${FLASK_ENV:-production}"
export FLASK_APP="${FLASK_APP:-app.py}"
export PYTHONPATH="$ROOT:$ROOT/backend:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

clear_service_ports

if [[ "$LOCAL" == true ]]; then
  echo "Starting PocketProSBA locally in host mode..."
else
  if [[ "$MODE" == "prod" ]]; then
    COMPOSE_FILE="docker-compose.yml"
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
  $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" up --build -d "${DOCKER_ARGS[@]}"
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
>>>>>>> 5f379abe34fa77644c7e6bc209e7f10fca3f62f5
