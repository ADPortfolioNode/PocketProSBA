"""Startup entry points: the real app serves its health routes, and run.py
fails loudly (no stub fallback) when the backend app cannot be imported."""
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_app_factory_serves_health_routes(client):
    assert client.get('/health').status_code == 200
    assert client.get('/api/health').status_code == 200


def test_run_py_exits_nonzero_when_backend_import_fails():
    # Make `from backend.app import create_app` raise, then execute run.py.
    code = (
        "import sys, runpy; "
        "sys.modules['backend.app'] = None; "
        "runpy.run_path('run.py', run_name='run')"
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
    assert 'failed to start' in output
    assert 'Traceback' in output
    assert 'Fallback application created' not in output
