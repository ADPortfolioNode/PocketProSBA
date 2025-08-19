#!/bin/sh
# wait-for-chroma.sh

set -e

host="$1"
shift

# Loop until we can connect to ChromaDB
until curl -s "http://$host/api/v1/heartbeat"; do
  >&2 echo "ChromaDB is unavailable - sleeping"
  sleep 1
done

>&2 echo "ChromaDB is up - executing command"
exec "$@"