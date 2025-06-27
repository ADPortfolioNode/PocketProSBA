import io
import os
import pytest
from fastapi.testclient import TestClient
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    client = TestClient(app)
    yield client

def test_file_upload_success(client):
    data = {
        'file': ('test.txt', io.BytesIO(b"dummy file content"), 'text/plain')
    }
    response = client.post('/api/files', files=data)
    assert response.status_code == 200
    json_data = response.json()
    assert 'message' in json_data and json_data['message'] == 'File uploaded successfully'
    assert 'filename' in json_data and json_data['filename'] == 'test.txt'

def test_file_upload_no_file(client):
    response = client.post('/api/files', files={})
    assert response.status_code == 400
    json_data = response.json()
    assert 'error' in json_data

def test_file_upload_disallowed_extension(client):
    data = {
        'file': ('test.exe', io.BytesIO(b"dummy content"), 'application/octet-stream')
    }
    response = client.post('/api/files', files=data)
    assert response.status_code == 400
    json_data = response.json()
    assert 'error' in json_data

def test_file_upload_exceeds_max_content_length(client):
    app = create_app()
    app.state.MAX_CONTENT_LENGTH = 10  # 10 bytes max
    client = TestClient(app)

    data = {
        'file': ('large.txt', io.BytesIO(b"this content is definitely longer than 10 bytes"), 'text/plain')
    }
    response = client.post('/api/files', files=data)
    # FastAPI returns 413 Request Entity Too Large for exceeding MAX_CONTENT_LENGTH
    assert response.status_code == 413 or response.status_code == 400
