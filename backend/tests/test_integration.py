import pytest
from backend.app import app
from unittest.mock import patch

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

@pytest.mark.integration
def test_full_chat_flow(client):
    """Test complete chat flow from frontend to backend"""
    # Test chat message processing
    payload = {
        "user_id": 1,
        "message": "What SBA loans are available?",
        "session_id": "integration_test_session"
    }

    with patch('services.chat_processing_service.get_concierge') as mock_get_concierge:
        mock_concierge = type('MockConcierge', (), {})()
        mock_concierge.handle_message = lambda msg: {
            'success': True,
            'text': 'I can help you with SBA loans.',
            'sources': []
        }
        mock_concierge.conversation_store = {}
        mock_get_concierge.return_value = mock_concierge

        response = client.post('/chat', json=payload)
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['success'] is True
        assert 'SBA loans' in json_data['text']

@pytest.mark.integration
def test_data_and_rag_integration(client):
    """Test data and RAG service integration"""
    # Test data endpoint
    data_response = client.get('/data')
    assert data_response.status_code == 200

    # Test RAG endpoint
    rag_response = client.get('/rag')
    assert rag_response.status_code == 200

    # Verify both return JSON
    assert data_response.is_json
    assert rag_response.is_json

@pytest.mark.integration
def test_error_handling_integration(client):
    """Test error handling across endpoints"""
    # Test invalid JSON
    response = client.post('/chat', data='invalid json')
    assert response.status_code == 400

    # Test missing required fields
    response = client.post('/chat', json={})
    assert response.status_code == 400

@pytest.mark.integration
def test_conversation_persistence(client):
    """Test conversation history persistence"""
    session_id = "persistence_test_session"

    # Send first message
    payload1 = {
        "user_id": 1,
        "message": "Hello",
        "session_id": session_id
    }

    with patch('services.chat_processing_service.get_concierge') as mock_get_concierge:
        mock_concierge = type('MockConcierge', (), {})()
        mock_concierge.handle_message = lambda msg: {
            'success': True,
            'text': 'Hi there!',
            'sources': []
        }
        mock_concierge.conversation_store = {}
        mock_get_concierge.return_value = mock_concierge

        client.post('/chat', json=payload1)

        # Send second message
        payload2 = {
            "user_id": 1,
            "message": "How are you?",
            "session_id": session_id
        }

        client.post('/chat', json=payload2)

        # Check conversation history
        history_response = client.get(f'/chat/history/{session_id}')
        assert history_response.status_code == 200
        history_data = history_response.get_json()
        assert len(history_data) >= 2
