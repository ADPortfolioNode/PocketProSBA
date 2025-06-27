import os
import pytest
import socket
import subprocess
import time
import requests
import redis

@pytest.fixture(scope="module")
def docker_container():
    # Build and start the docker container for testing
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    build_cmd = ['docker-compose', 'build', '--no-cache']
    up_cmd = ['docker-compose', 'up', '-d']

    subprocess.run(build_cmd, cwd=project_root, check=True)
    subprocess.run(up_cmd, cwd=project_root, check=True)

    # Wait for container to be healthy
    time.sleep(10)  # Wait for initial startup

    yield

    # Tear down container after tests
    down_cmd = ['docker-compose', 'down']
    subprocess.run(down_cmd, cwd=project_root, check=True)

def test_container_dynamic_port(docker_container):
    port = os.environ.get('PORT', '10000')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', int(port)))
    sock.close()
    assert result == 0, f"Container port {port} is not open"

def test_healthcheck_endpoint(docker_container):
    port = os.environ.get('PORT', '10000')
    url = f"http://localhost:{port}/health"
    for _ in range(10):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                break
        except requests.ConnectionError:
            time.sleep(1)
    else:
        pytest.fail(f"Healthcheck endpoint {url} not responding with 200 OK")
    assert response.json() == {"status": "healthy"}

def test_redis_connectivity(docker_container):
    redis_host = 'localhost'
    redis_port = 6379
    r = redis.Redis(host=redis_host, port=redis_port)
    try:
        pong = r.ping()
    except redis.ConnectionError:
        pytest.fail("Could not connect to Redis server")
    assert pong is True

def test_api_endpoints_basic(client):
    # Basic smoke test for API root
    response = client.get('/')
    assert response.status_code == 200

def test_document_upload_and_search(client):
    # Upload a test document and query it
    data = {
        'file': (io.BytesIO(b'Test document content'), 'test_doc.txt')
    }
    upload_resp = client.post('/api/files', data=data, content_type='multipart/form-data')
    assert upload_resp.status_code == 200

    query_resp = client.post('/api/query', json={'query': 'Test'})
    assert query_resp.status_code == 200
    json_data = query_resp.get_json()
    assert json_data.get('success') is True

def test_chat_feature_placeholder():
    # Placeholder for chat feature tests, to be expanded
    assert True
