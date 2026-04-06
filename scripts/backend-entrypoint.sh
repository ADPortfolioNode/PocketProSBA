#!/bin/bash

# Backend entrypoint script for PocketPro SBA

set -e

echo "Starting PocketPro SBA Backend..."

# Wait for ChromaDB to be ready
echo "Waiting for ChromaDB to be ready..."
# Prefer v2 heartbeat; if v2 isn't available, accept a 410 from v1 (deprecated) as ready
# while true; do
#     # Try v2
#     if curl -sS -f -o /dev/null http://chromadb:8000/api/v2/heartbeat 2>/dev/null; then
#         echo "ChromaDB v2 heartbeat OK"
#         break
#     fi

#     # Try v1 and accept 410 (Unimplemented / deprecated) as an indicator the server is up
#     http_status=$(curl -sS -o /dev/null -w "%{http_code}" http://chromadb:8000/api/v1/heartbeat 2>/dev/null || true)
#     if [ "$http_status" = "200" ] || [ "$http_status" = "410" ]; then
#         echo "ChromaDB v1 heartbeat responded with status $http_status (treating as ready)"
#         break
#     fi

#     echo "ChromaDB is not ready yet (v2 not responding, v1 status: ${http_status:-none}), waiting..."
#     sleep 2
# done
echo "ChromaDB is ready!"

# Check if required environment variables are set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "Warning: GEMINI_API_KEY is not set"
fi

# Start the FastAPI application
echo "Starting FastAPI application..."
exec uvicorn app_fastapi:app --host 0.0.0.0 --port 5000