import pytest
from backend.app import create_app

@pytest.fixture
def app():
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_health_check(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert b'healthy' in response.data

def test_get_info_endpoint(client):
    response = client.get('/api/info')
    assert response.status_code == 200
    assert response.is_json
    assert response.json['status'] == 'operational'

def test_post_chat_message(client):
    payload = {
        "user_id": 1,
        "message": "Hello",
        "session_id": "test_session"
    }
    response = client.post('/api/chat', json=payload)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data.get('success') is True
    assert 'response' in json_data

def test_rag_health_endpoint(client):
    response = client.get('/api/rag/health')
    assert response.status_code in (200, 503)
    assert response.is_json