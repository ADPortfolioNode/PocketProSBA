#!/bin/bash

# Initialize data directory if it doesn't exist
if [ ! -d "$CHROMA_PERSIST_DIR" ]; then
    mkdir -p "$CHROMA_PERSIST_DIR"
    chown -R chroma:chroma "$CHROMA_PERSIST_DIR"
fi

# Initialize config directory if it doesn't exist
if [ ! -d "/chroma/config" ]; then
    mkdir -p /chroma/config
    chown -R chroma:chroma /chroma/config
fi

# Start ChromaDB server
exec uvicorn chromadb.app:app \
    --host ${CHROMA_SERVER_HOST:-0.0.0.0} \
    --port ${CHROMA_SERVER_HTTP_PORT:-8000} \
    --workers ${UVICORN_WORKERS:-4} \
    --loop uvloop \
    --http httptools