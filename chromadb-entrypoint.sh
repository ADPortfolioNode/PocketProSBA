#!/bin/bash
set -e

# Wait for a few seconds to allow system initialization
sleep 2

# Initialize ChromaDB server
exec uvicorn chromadb.app:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --loop uvloop \
    --http httptools