import os
import time
import requests


def test_nginx_backend_chroma_flow():
    """Minimal e2e smoke test for nginx -> backend -> chroma health.

    This test only runs when RUN_DOCKER_E2E=1 to avoid running in normal unit CI.
    It checks that frontend and backend respond over IPv4 and that the chroma
    health endpoint returns OK (if available).
    """
    if os.getenv('RUN_DOCKER_E2E', '0') != '1':
        import pytest

        pytest.skip('Docker e2e tests disabled')

    # Give services a few seconds to settle
    time.sleep(2)

    # Check frontend (nginx) on IPv4
    r = requests.get('http://127.0.0.1:3000/', timeout=5)
    assert r.status_code == 200

    # Check backend via nginx proxy
    r = requests.get('http://127.0.0.1:3000/api/health', timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert data.get('status') == 'healthy'

    # Check backend chromadb health directly
    try:
        r = requests.get('http://127.0.0.1:8000/api/chromadb_health', timeout=5)
        # chroma may be unavailable in some environments; ensure endpoint responds
        assert r.status_code in (200, 503)
    except requests.exceptions.RequestException:
        # network error — fail the test
        assert False, 'Could not contact backend chromadb_health endpoint'
