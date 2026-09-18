#!/usr/bin/env bash
# PocketPro:SBA local DOWN for testing (keeps volumes / chromadb_data / uploads)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
if [[ -f docker-compose.dev.yml ]]; then
  docker compose -f docker-compose.dev.yml down --timeout 30 --remove-orphans || true
fi
if [[ -f docker-compose.yml ]]; then
  docker compose -f docker-compose.yml down --timeout 30 --remove-orphans || true
fi
if [[ -f docker-compose.prod.yml ]]; then
  docker compose -f docker-compose.prod.yml down --timeout 30 --remove-orphans || true
fi
echo "[OK] PocketPro:SBA down. Data kept in uploads/ and chromadb_data/"
docker compose -f docker-compose.dev.yml ps 2>/dev/null || true
