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
