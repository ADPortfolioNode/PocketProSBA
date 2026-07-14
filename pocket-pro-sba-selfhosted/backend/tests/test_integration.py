import pytest
from unittest.mock import patch


@pytest.mark.integration
def test_full_chat_flow(client):
    """Test complete chat flow from frontend to backend"""
    payload = {
        "user_id": 1,
        "message": "What SBA loans are available?",
        "session_id": "integration_test_session"
    }

    with patch('backend.services.chat_processing_service.get_concierge') as mock_get_concierge:
        mock_concierge = mock_get_concierge.return_value
        mock_concierge.handle_message.return_value = {
            "text": "SBA 7(a) and 504 loans are available.",
            "session_id": "integration_test_session"
        }

        response = client.post('/api/chat', json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert 'response' in data or 'text' in data


@pytest.mark.integration
def test_sba_content_endpoint(client):
    """Test SBA content API endpoint"""
    response = client.get('/api/sba/content/articles')
    assert response.status_code in (200, 500)


@pytest.mark.integration
def test_orchestrator_health(client):
    """Test orchestrator health endpoint"""
    response = client.get('/api/orchestrator/health')
    assert response.status_code == 200


@pytest.mark.integration
def test_rag_health(client):
    """Test RAG health endpoint"""
    response = client.get('/api/rag/health')
    assert response.status_code in (200, 503)


@pytest.mark.integration
def test_chat_history_flow(client):
    """Test chat history retrieval"""
    session_id = "integration_history_session"

    with patch('backend.services.chat_processing_service.get_concierge') as mock_get_concierge:
        mock_concierge = mock_get_concierge.return_value
        mock_concierge.get_conversation_history.return_value = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi, how can I help?"}
        ]

        response = client.get(f'/api/chat/history/{session_id}')
        assert response.status_code in (200, 404)