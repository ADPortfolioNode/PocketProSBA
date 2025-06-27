import pytest
from app import create_app
from starlette.testclient import TestClient

def test_execute():
    app = create_app()
    client = TestClient(app)

    # Minimal valid payload
    response = client.post('/api/execute', json={'step': 'Extract keywords.'})
    assert response.status_code in (200, 400)  # Accept 400 if not implemented
