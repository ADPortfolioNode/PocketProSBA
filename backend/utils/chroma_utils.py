import os
import chromadb
from chromadb.config import Settings

def init_chroma_client():
    CHROMADB_HOST = os.getenv('CHROMADB_HOST', 'chromadb')
    CHROMADB_PORT = int(os.getenv('CHROMADB_PORT', 8000))

    # Initialize with v2 API settings
    settings = Settings(
        chroma_api_impl="rest",
        chroma_server_host=CHROMADB_HOST,
        chroma_server_http_port=CHROMADB_PORT
    )

    client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT, settings=settings)
    
    # Ensure default collection exists
    try:
        collection = client.get_or_create_collection("default_collection")
    except Exception as e:
        print(f"Error initializing ChromaDB collection: {e}")
        raise

    return client