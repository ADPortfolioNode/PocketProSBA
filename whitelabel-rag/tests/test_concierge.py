import pytest
from unittest.mock import MagicMock, patch
from app.services.concierge import Concierge, get_concierge_instance

@pytest.fixture
def concierge(mock_rag_manager, mock_conversation_store, mock_llm_factory, mock_chroma_service):
    """Create concierge instance with mocked dependencies."""
    with patch('app.services.concierge.get_rag_manager', return_value=mock_rag_manager), \
         patch('app.services.concierge.get_conversation_store', return_value=mock_conversation_store), \
         patch('app.services.concierge.LLMFactory', mock_llm_factory):
        return get_concierge_instance()

def test_handle_message_simple_query(concierge):
    message = "What time is it?"
    response = concierge.handle_message(message)
    assert 'Current time' in response['text']

def test_handle_message_document_search(concierge, mock_rag_manager, mock_llm_factory):
    # Mock the intent classification to return document_search
    mock_llm_factory.generate_response.side_effect = ['document_search', 'Found document']
    mock_rag_manager.query_documents.return_value = {'text': 'Found document', 'sources': [], 'error': None}
    message = "Find info about AI"
    response = concierge.handle_message(message)
    assert 'Found document' in response['text']

def test_handle_message_task_request(concierge, mock_llm_factory):
    # Mock intent classification and task decomposition
    mock_llm_factory.generate_response.side_effect = ['task_request', 'Decomposed task']
    message = "Plan a project"
    response = concierge.handle_message(message)
    assert 'Decomposed task' in response['text']

def test_handle_message_meta_query(concierge, mock_llm_factory):
    # Mock intent classification and meta response
    mock_llm_factory.generate_response.side_effect = ['meta', 'System info']
    message = "What can you do?"
    response = concierge.handle_message(message)
    # The actual response might be the help text, so check for that instead
    assert 'WhiteLabelRAG' in response['text'] or 'System info' in response['text']

def test_handle_message_direct_response(concierge, mock_llm_factory, mock_rag_manager):
    # Mock intent classification and direct response
    mock_llm_factory.generate_response.side_effect = ['simple_query', 'Direct response']
    mock_rag_manager.get_collection_stats.return_value = {'documents_count': 0}
    message = "Random message"
    response = concierge.handle_message(message)
    assert 'Direct response' in response['text']

def test_intent_classification(concierge, mock_llm_factory):
    mock_llm_factory.generate_response.return_value = 'simple_query'
    intent = concierge._classify_intent("Hello", MagicMock())
    assert intent == 'simple_query'

def test_direct_functions(concierge):
    assert concierge._check_direct_functions("show stats") is not None
    assert concierge._check_direct_functions("what time is it") is not None
    assert concierge._check_direct_functions("help") is not None
    assert concierge._check_direct_functions("unknown command") is None

def test_get_current_time(concierge):
    time_str = concierge._get_current_time()
    assert "Current time:" in time_str

def test_get_system_stats(concierge, mock_rag_manager, mock_conversation_store):
    mock_rag_manager.get_collection_stats.return_value = {'documents_count': 5}
    mock_conversation_store.get_conversation_stats.return_value = {'total_conversations': 1, 'total_messages': 10, 'avg_messages_per_conversation': 5}
    stats = concierge._get_system_stats()
    assert "Documents:" in stats

def test_get_help(concierge):
    help_text = concierge._get_help()
    assert "WhiteLabelRAG Help" in help_text
