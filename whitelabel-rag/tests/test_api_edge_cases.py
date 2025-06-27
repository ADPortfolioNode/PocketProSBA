import pytest
import io
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    # FastAPI app does not have 'config' attribute or 'test_client' method
    # Use TestClient from starlette.testclient for testing FastAPI apps
    from starlette.testclient import TestClient
    client = TestClient(app)
    yield client

def test_execute_task_with_missing_fields(client):
    # Missing suggested_agent_type
    task = {
        'task': {
            'instruction': 'Do something',
            'step_number': 1
        }
    }
    response = client.post('/api/execute', json=task)
    assert response.status_code == 400
    data = response.json()
    assert 'error' in data

def test_upload_file_invalid_content_type(client):
    data = {
        'file': (io.BytesIO(b'test content'), 'test.txt')
    }
    # Missing content_type
    response = client.post('/api/files', data=data)
    assert response.status_code == 400

def test_query_documents_empty_query(client):
    response = client.post('/api/query', json={'query': ''})
    assert response.status_code == 400
    data = response.json()
    assert 'error' in data

def test_validate_result_missing_task(client):
    payload = {
        'result': 'Some result'
    }
    response = client.post('/api/validate', json=payload)
    assert response.status_code == 400
    data = response.json()
    assert 'error' in data
