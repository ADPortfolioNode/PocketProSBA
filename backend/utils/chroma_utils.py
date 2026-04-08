import os


def init_chroma_client():
    CHROMADB_HOST = os.getenv('CHROMADB_HOST', 'chromadb')
    CHROMADB_PORT = int(os.getenv('CHROMADB_PORT', 8000))

    try:
        import chromadb
        from chromadb.config import Settings
    except Exception as exc:
        print(f"ChromaDB import failed: {exc}")
        raise

    # Initialize with v2 API settings
    settings = Settings(
        chroma_api_impl="rest",
        chroma_server_host=CHROMADB_HOST,
        chroma_server_http_port=CHROMADB_PORT
    )

    try:
        client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT, settings=settings)
    except Exception as exc:
        print(f"Failed to create ChromaDB HTTP client: {exc}")
        raise
    
    # Ensure default collection exists
    try:
        collection = client.get_or_create_collection("default_collection")
    except Exception as e:
        print(f"Error initializing ChromaDB collection: {e}")
        raise

    return client