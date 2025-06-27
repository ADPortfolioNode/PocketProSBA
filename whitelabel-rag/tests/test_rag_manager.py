import pytest
from unittest.mock import MagicMock, patch
from app.services.rag_manager import RAGManager

@pytest.fixture
def rag_manager():
    return RAGManager()

def test_query_documents_basic_rag_only(rag_manager):
    with patch.object(rag_manager, '_basic_rag_workflow') as mock_basic_rag:
        mock_basic_rag.return_value = {
            'text': 'Answer from RAG',
            'context_used': True,
            'error': None
        }
        response = rag_manager.query_documents('test query', n_results=3, workflow_type='basic')
        assert 'rag_response' in response
        assert 'internet_search_response' in response
        assert response['rag_response']['text'] == 'Answer from RAG'
        assert response['internet_search_response'] is None

def test_query_documents_fallback_to_internet_search(rag_manager):
    with patch.object(rag_manager, '_basic_rag_workflow') as mock_basic_rag, \
         patch.object(rag_manager.internet_search_agent, 'search') as mock_internet_search:
        mock_basic_rag.return_value = {
            'text': "I couldn't find any relevant documents to answer your question.",
            'context_used': False,
            'error': None
        }
        mock_internet_search.return_value = {
            'text': 'Answer from internet search',
            'additional_data': {'results': []}
        }
        response = rag_manager.query_documents('test query', n_results=3, workflow_type='basic')
        assert 'rag_response' in response
        assert 'internet_search_response' in response
        assert response['rag_response']['text'].startswith("I couldn't find")
        assert response['internet_search_response']['text'] == 'Answer from internet search'
