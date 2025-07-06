import chromadb
from chromadb.config import Settings

# Test the new ChromaDB client API
try:
    print("Testing ChromaDB client...")
    client = chromadb.HttpClient(
        settings=Settings(
            chroma_server_host="localhost",
            chroma_server_http_port=8000
        )
    )
    print("Client created successfully!")
    
    # Try to get or create a collection
    collection = client.get_or_create_collection("test_collection")
    print("Collection created successfully!")
    
    # Try to add a document
    collection.add(
        documents=["This is a test document"],
        ids=["test_id"]
    )
    print("Document added successfully!")
    
except Exception as e:
