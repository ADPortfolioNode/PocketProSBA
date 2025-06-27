import pytest
from fastapi.testclient import TestClient
from app import create_app
import json

@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as client:
        yield client

def test_websocket_chat(client):
    client_id = "testclient"
    with client.websocket_connect(f"/ws/{client_id}") as websocket:
        # Receive connection confirmation message
        data = websocket.receive_json()
        assert data['status'] == 'connected'
        assert data['session_id'] == client_id

        # Send a chat_message event with a message
        websocket.send_json({
            "event": "chat_message",
            "data": {"message": "Hello"}
        })

        # Receive processing status message
        data = websocket.receive_json()
        assert data['status'] == 'processing'
        assert data['progress'] == 10

        # Receive chat response message
        data = websocket.receive_json()
        assert 'text' in data
        assert 'timestamp' in data
        assert 'session_id' in data
        assert data['session_id'] == client_id

        # Receive completion status message
        data = websocket.receive_json()
        assert data['status'] in ['completed', 'error']
        assert data['progress'] == 100

def test_websocket_health_check(client):
    client_id = "healthcheckclient"
    with client.websocket_connect(f"/ws/{client_id}") as websocket:
        # Receive connection confirmation message
        data = websocket.receive_json()
        assert data['status'] == 'connected'
        assert data['session_id'] == client_id

        # Send a health_check event
        websocket.send_json({
            "event": "health_check",
            "data": {}
        })

        # Receive health status message
        data = websocket.receive_json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
