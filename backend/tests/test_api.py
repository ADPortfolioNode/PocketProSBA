import pytest

def test_get_system_info(client):
    response = client.get('/api/info')
    assert response.status_code == 200
    assert response.json['service'] == 'PocketPro SBA'
    assert response.json['version'] == '1.0.0'
    assert response.json['status'] == 'running'

def test_decompose_task_success(client):
    response = client.post('/api/decompose', json={'message': 'test message', 'session_id': 'test_session'})
    assert response.status_code == 200
    assert 'response' in response.json

def test_decompose_task_no_message(client):
    response = client.post('/api/decompose', json={'session_id': 'test_session'})
    assert response.status_code == 400
    assert response.json['error'] == 'Message is required'

def test_execute_step_success(client):
    response = client.post('/api/execute', json={'task': {'step': 'test'}})
    assert response.status_code == 200
    assert 'result' in response.json

def test_execute_step_no_data(client):
    response = client.post('/api/execute', json={})
    assert response.status_code == 400
    assert response.json['error'] == 'No JSON data provided'

def test_validate_step_success(client):
    response = client.post('/api/validate', json={'result': 'test result', 'task': {'step': 'test'}})
    assert response.status_code == 200
    assert 'validation' in response.json

def test_validate_step_no_data(client):
    response = client.post('/api/validate', json={})
    assert response.status_code == 400
    assert response.json['error'] == 'No JSON data provided'

def test_query_documents_success(client):
    response = client.post('/api/query', json={'query': 'test query'})
    assert response.status_code == 200
    assert 'results' in response.json

def test_query_documents_no_query(client):
    response = client.post('/api/query', json={})
    assert response.status_code == 400
    assert response.json['error'] == 'Query is required'