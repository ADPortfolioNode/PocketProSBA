import pytest
from app import create_app

@pytest.fixture
def app():
    app = create_app()
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_health_check(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert b'healthy' in response.data

def test_get_data_endpoint(client):
    response = client.get('/data')
    assert response.status_code == 200
    assert response.is_json

def test_post_chat_message(client):
    payload = {
        "user_id": 1,
        "message": "Hello",
        "session_id": "test_session"
    }
    response = client.post('/chat', json=payload)
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'success' in json_data
    assert 'text' in json_data

def test_rag_endpoint(client):
    response = client.get('/rag')
    assert response.status_code == 200
    assert response.is_json
