import pytest

def test_root_endpoint(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.json['service'] == 'PocketPro SBA'
    assert response.json['version'] == '1.0.0'
    assert response.json['status'] == 'running'

def test_404_error_handler(client):
    response = client.get('/nonexistent_route')
    assert response.status_code == 404
    assert response.json['error'] == 'Not Found'

def test_400_error_handler(client):
    # Assuming a route that can trigger a 400, e.g., a POST with invalid JSON
    # For this test, we'll simulate a bad request to a known endpoint
    response = client.post('/api/decompose', data='invalid json', content_type='application/json')
    assert response.status_code == 400
    assert response.json['error'] == 'Bad Request'

def test_500_error_handler(client):
    # To test 500, we need to simulate an internal server error.
    # This might require temporarily modifying a route to raise an exception.
    # For now, we'll skip direct testing of 500 unless a specific route is designed for it.
    pass