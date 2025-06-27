import pytest
from app import create_app
from starlette.testclient import TestClient

def test_query_documents():
    app = create_app()
    client = TestClient(app)

    # Query with no documents should return empty results
    response = client.post('/api/query', json={'query': 'test'})
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert isinstance(data['results'], list)
