#!/usr/bin/env bash

set -e

# Trap errors and print a message
trap 'echo "[ERROR] Script failed at line $LINENO. Exiting." >&2' ERR

# Check for Docker
if ! command -v docker &> /dev/null; then
  echo "[ERROR] Docker is not installed or not in PATH." >&2
  exit 1
fi

# Check for docker-compose or docker compose
if command -v docker-compose &> /dev/null; then
  DC="docker-compose"
elif docker compose version &> /dev/null; then
  DC="docker compose"
else
  echo "[ERROR] Neither docker-compose nor 'docker compose' is available." >&2
  exit 1
fi

# Enable Docker BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Clean up any existing containers
echo "Cleaning up existing containers..."
$DC down --remove-orphans

# Build and start services
echo "Building and starting services..."
$DC build --no-cache
$DC up -d

# Wait for services to be ready with health check
SERVICES=(frontend backend nginx)
MAX_ATTEMPTS=20
SLEEP_TIME=3

wait_for_healthy() {
  local service=$1
  local attempt=1
  while [ $attempt -le $MAX_ATTEMPTS ]; do
    STATUS=$($DC ps --format "{{.Name}}:{{.State.Health}}" | grep "$service" | cut -d: -f2)
    if [[ "$STATUS" == "healthy" || -z "$STATUS" ]]; then
      break
    fi
    echo "Waiting for $service to be healthy... ($attempt/$MAX_ATTEMPTS)"
    sleep $SLEEP_TIME
    attempt=$((attempt+1))
  done
  if [ "$STATUS" != "healthy" ] && [ -n "$STATUS" ]; then
    echo "[WARNING] $service did not become healthy after $((MAX_ATTEMPTS*SLEEP_TIME)) seconds."
  fi
}

echo "Waiting for services to start..."
for svc in "${SERVICES[@]}"; do
  wait_for_healthy $svc
done

# Check service status
echo "Checking service status..."
$DC ps

# Show logs
echo "Showing recent logs..."
$DC logs --tail=50

echo "Services started!"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:5000"
echo "Nginx Proxy: http://localhost:10000"
