import os
import pytest
import json
from app import create_app

@pytest.mark.skipif(not os.environ.get("RUN_E2E_TESTS"), reason="E2E tests not enabled")
def test_chat_flow(client):
    # Simulate a chat flow with multiple messages and responses
    messages = [
        {"message": "Hello, how can I upload a document?"},
        {"message": "I want to search for climate change."},
        {"message": "Can you help me with a chat feature?"}
    ]

    for msg in messages:
        response = client.post('/api/chat', json=msg)
        assert response.status_code == 200
        data = response.get_json()
        assert 'response' in data
        assert isinstance(data['response'], str)
