import os

# ChromaDB 0.4+ rejects these legacy environment variables from older .env templates.
_LEGACY_CHROMA_ENV_KEYS = (
    'CHROMA_DB_IMPL',
    'CHROMA_API_IMPL',
    'CHROMA_SERVER_HOST',
    'CHROMA_SERVER_HTTP_PORT',
)


def clear_legacy_chroma_env():
    """Remove legacy Chroma env vars that break chromadb 0.4+ client construction."""
    cleared = {}
    for key in _LEGACY_CHROMA_ENV_KEYS:
        if key in os.environ:
            cleared[key] = os.environ.pop(key)
    return cleared


def restore_chroma_env(cleared):
    """Restore env vars cleared by clear_legacy_chroma_env."""
    if cleared:
        os.environ.update(cleared)


def init_chroma_client():
    CHROMADB_HOST = os.getenv('CHROMADB_HOST', 'chromadb')
    CHROMADB_PORT = int(os.getenv('CHROMADB_PORT', 8000))

    try:
        import chromadb
        from chromadb.config import Settings
    except Exception as exc:
        print(f"ChromaDB import failed: {exc}")
        raise

    cleared = clear_legacy_chroma_env()
    try:
        client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)
    except Exception as exc:
        print(f"Failed to create ChromaDB HTTP client: {exc}")
        raise
    finally:
        restore_chroma_env(cleared)
    
    # Ensure default collection exists
    try:
        collection = client.get_or_create_collection("default_collection")
    except Exception as e:
        print(f"Error initializing ChromaDB collection: {e}")
        raise

    return client