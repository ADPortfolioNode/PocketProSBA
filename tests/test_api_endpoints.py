import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app_full import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_api_health(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert 'status' in response.json

def test_api_registry(client):
    response = client.get('/api/registry')
    assert response.status_code == 200
    assert 'documents' in response.json

def test_chromadb_health(client):
    response = client.get('/api/chromadb/health')
    assert response.status_code == 200
    assert 'chroma_enabled' in response.json

def test_get_resources(client):
    response = client.get('/api/resources')
    assert response.status_code == 200
    assert 'resources' in response.json

def test_list_uploaded_files(client):
    response = client.get('/api/uploads')
    assert response.status_code == 200
    assert 'files' in response.json or 'error' in response.json
