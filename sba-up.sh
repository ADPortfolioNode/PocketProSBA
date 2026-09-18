#!/usr/bin/env bash
# PocketPro:SBA local UP for testing
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
MODE="${1:-dev}"
exec "$ROOT/start.sh" --mode "$MODE" --build --smoke --open
