import pytest
from fastapi.testclient import TestClient
from app import create_app

app = create_app()
client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
