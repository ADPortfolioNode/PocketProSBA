import os

try:
    import chromadb
    from chromadb import Settings
    _CHROMADB_AVAILABLE = True
except Exception as exc:
    chromadb = None
    Settings = None
    _CHROMADB_AVAILABLE = False
    _CHROMADB_IMPORT_ERROR = exc

def init_chromadb():
    """Initialize ChromaDB client with proper configuration"""
    host = os.environ.get('CHROMADB_HOST', 'localhost')
    port = int(os.environ.get('CHROMADB_PORT', '8000'))
    
    settings = Settings(
        chroma_api_impl="rest",
        chroma_server_host=host,
        chroma_server_http_port=port,
        anonymized_telemetry=False
    )
    
    return chromadb.HttpClient(host=host, port=port, settings=settings)