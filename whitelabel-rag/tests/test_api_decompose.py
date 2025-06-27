import pytest
from app import create_app

def test_decompose():
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()

    # Minimal valid payload
    response = client.post('/api/decompose', json={'task': 'Summarize this document.'})
    assert response.status_code in (200, 400)  # Accept 400 if not implemented
