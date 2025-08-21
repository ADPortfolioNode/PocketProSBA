import pytest

def test_get_system_info(client):
    response = client.get('/api/info')
    assert response.status_code == 200
    assert response.json['service'] == 'PocketPro SBA'
