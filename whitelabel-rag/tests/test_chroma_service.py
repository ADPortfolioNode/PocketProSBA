import pytest
from src.services.chroma_service import ChromaService

@pytest.fixture
def chroma_service():
    return ChromaService()

def test_chroma_service_initialization(chroma_service):
    assert chroma_service is not None
    # The client may be None if ChromaDB is not available in the environment
    # So we check the _chroma_available flag
    assert hasattr(chroma_service, '_chroma_available')
    # _chroma_available should be a boolean
    assert isinstance(chroma_service._chroma_available, bool)

def test_add_query_delete_documents(chroma_service):
    if not chroma_service._chroma_available:
        pytest.skip("ChromaDB not available, skipping add/query/delete tests")

    # Add a test document
    add_result = chroma_service.add_documents(
        documents=["Test document content"],
        metadatas=[{"source": "test"}],
        ids=["test_doc_1"]
    )
    assert add_result["success"] is True
    assert add_result["count"] == 1

    # Query the document
    query_result = chroma_service.query_documents("Test document content", n_results=1)
    assert query_result["success"] is True
    assert "results" in query_result
    assert len(query_result["results"]["documents"][0]) > 0

    # Delete the document
    delete_result = chroma_service.delete_documents(["test_doc_1"])
    assert delete_result is True

def test_collection_stats(chroma_service):
    if not chroma_service._chroma_available:
        pytest.skip("ChromaDB not available, skipping collection stats test")

    stats = chroma_service.get_collection_stats()
    assert "success" in stats
    assert isinstance(stats.get("document_count", 0), int)

def test_update_documents(chroma_service):
    if not chroma_service._chroma_available:
        pytest.skip("ChromaDB not available, skipping update documents test")

    # Add a document to update
    chroma_service.add_documents(
        documents=["Original content"],
        metadatas=[{"source": "test"}],
        ids=["update_doc_1"]
    )

    # Update the document
    update_result = chroma_service.update_documents(
        ids=["update_doc_1"],
        documents=["Updated content"],
        metadatas=[{"source": "test_updated"}]
    )
    assert update_result is True

    # Clean up
    chroma_service.delete_documents(["update_doc_1"])

def test_get_embedding_info(chroma_service):
    info = chroma_service.get_embedding_info()
    assert "has_custom_embedding" in info
    assert "embedding_type" in info
    assert "collection_exists" in info
    assert "compatible" in info
