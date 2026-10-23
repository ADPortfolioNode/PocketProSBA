"""Startup entry points: the real app serves its health routes, and wsgi.py
(the single entry) fails loudly (no stub fallback) when the backend app cannot
be imported."""
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_app_factory_serves_health_routes(client):
    assert client.get('/health').status_code == 200
    assert client.get('/api/health').status_code == 200


def test_wsgi_exits_nonzero_when_backend_import_fails():
    # Make `from backend.app import create_app` raise, then execute wsgi.py.
    code = (
        "import sys, runpy; "
        "sys.modules['backend.app'] = None; "
        "runpy.run_path('wsgi.py', run_name='wsgi')"
    )
    env = dict(os.environ, SECRET_KEY=os.environ.get('SECRET_KEY', 'test-key'))
    proc = subprocess.run(
        [sys.executable, '-c', code],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = proc.stdout + proc.stderr
    assert proc.returncode != 0, output
    assert 'Error starting application' in output
    assert 'Traceback' in output
    assert 'Fallback application created' not in output
