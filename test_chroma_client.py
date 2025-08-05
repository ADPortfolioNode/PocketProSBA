import pytest
from chromadb import Client
from chromadb.config import Settings


def test_chromadb_client():
    """Ensure ChromaDB client can connect, add, and query documents."""
    # Initialize client with Render-compatible host and port
    client = Client(
        settings=Settings(
            chroma_server_host="localhost",
            chroma_server_http_port=8000
        )
    )

    # Get or create a collection
    collection = client.get_or_create_collection("test_collection")
    assert collection is not None, "Failed to create or get collection"

    # Add a test document
    collection.add(
        documents=["This is a test document"],
        ids=["test_id"]
    )

    # Query the collection
    results = collection.query(
        query_texts=["test document"],
        n_results=1
    )
    returned_ids = results.get("ids", [[]])[0]
    assert returned_ids and returned_ids[0] == "test_id", f"Expected 'test_id', got {returned_ids}"
