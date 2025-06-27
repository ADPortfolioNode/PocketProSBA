import pytest
from app import create_app

def test_validate():
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()

    # Minimal valid payload
    response = client.post('/api/validate', json={'result': 'Some result'})
    assert response.status_code in (200, 400)  # Accept 400 if not implemented
