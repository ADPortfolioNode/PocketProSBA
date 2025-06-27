import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app({'TESTING': True})
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

def test_decompose_endpoint(client):
    """Test the decompose endpoint."""
    response = client.post('/api/decompose', json={'message': 'Hello'})
    assert response.status_code == 200
    assert 'response' in response.json
