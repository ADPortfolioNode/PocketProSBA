import pytest
from unittest.mock import patch, MagicMock
from app.services.concierge import Concierge
from app.services.rag_manager import RAGManager

@pytest.fixture
def concierge():
    return Concierge()

@pytest.fixture
def rag_manager_mock():
    with patch('app.services.concierge.get_rag_manager') as mock_get_rag_manager:
        mock_rag_manager = MagicMock(spec=RAGManager)
        # Setup mock to return a specific response for query_documents
        mock_rag_manager.query_documents.return_value = {
            'documents': [['Mocked document content']],
            'metadatas': [[{'source': 'mock_source'}]],
            'distances': [[0.1]]
        }
        mock_get_rag_manager.return_value = mock_rag_manager
        yield mock_rag_manager

def test_concierge_handles_document_search_with_mock(concierge, rag_manager_mock):
    # Patch the rag_manager in concierge to use the mock
    concierge.rag_manager = rag_manager_mock

    user_query = "Find information about climate change impacts"
    response = concierge.handle_message(user_query)

    # Assert that the mock was called
    rag_manager_mock.query_documents.assert_called_once_with(user_query, n_results=3, where=None)

    # Assert response contains expected mocked content
    assert 'Mocked document content' in response['text']
    assert 'mock_source' in response.get('sources', []) or 'mock_source' in response.get('text', '')

if __name__ == "__main__":
    pytest.main([__file__])
