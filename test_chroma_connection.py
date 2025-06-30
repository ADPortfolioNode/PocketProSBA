import chromadb
import os

chroma_host = os.getenv("CHROMA_HOST", "chromadb")
chroma_port = os.getenv("CHROMA_PORT", "8000")

print(f"Attempting to connect to ChromaDB at {chroma_host}:{chroma_port}")

try:
    client = chromadb.HttpClient(host=chroma_host, port=int(chroma_port))
    version = client.version()
    print(f"Successfully connected to ChromaDB version: {version}")
    heartbeat = client.heartbeat()
    print(f"ChromaDB heartbeat: {heartbeat}")
except Exception as e:
    print(f"Failed to connect to ChromaDB: {e}")
