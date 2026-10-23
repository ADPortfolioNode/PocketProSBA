import os
import shutil
import socket
import tempfile

import pytest

# --- Hermetic test environment --------------------------------------------
# Set up before the app is imported so module-level code sees it too.
#
# 1. Live SBA ingests write to a temp dir instead of the tracked
#    backend/knowledge_base/sba_api_live/ files, so `git status` stays clean
#    after a test run.
_KB_TMP = tempfile.mkdtemp(prefix="sba-kb-test-")
os.environ["SBA_KB_LIVE_DIR"] = os.path.join(_KB_TMP, "sba_api_live")

# 2. Outbound network is blocked: any connection to a non-loopback address
#    (sba.gov, Gemini, an HTTP proxy, ...) fails fast with OSError, which the
#    services already treat as "upstream unavailable". This makes the chat and
#    SBA tests deterministic and offline. Set ALLOW_NETWORK_TESTS=1 to opt out.
_LOOPBACK = {"127.0.0.1", "::1", "localhost", "0.0.0.0"}
_real_connect = socket.socket.connect
_real_connect_ex = socket.socket.connect_ex
_real_getaddrinfo = socket.getaddrinfo


class NetworkBlockedError(OSError):
    """Raised when a test tries to reach the network."""


def _is_local(address):
    if not isinstance(address, tuple):  # AF_UNIX path
        return True
    host = str(address[0])
    return host in _LOOPBACK or host.startswith("127.")


def _guarded_connect(self, address, *args, **kwargs):
    if not _is_local(address):
        raise NetworkBlockedError(f"network access blocked in tests: {address!r}")
    return _real_connect(self, address, *args, **kwargs)


def _guarded_connect_ex(self, address, *args, **kwargs):
    if not _is_local(address):
        raise NetworkBlockedError(f"network access blocked in tests: {address!r}")
    return _real_connect_ex(self, address, *args, **kwargs)


def _guarded_getaddrinfo(host, *args, **kwargs):
    if host is not None and not _is_local((host, 0)):
        raise socket.gaierror(f"DNS lookup blocked in tests: {host!r}")
    return _real_getaddrinfo(host, *args, **kwargs)


if os.environ.get("ALLOW_NETWORK_TESTS") != "1":
    socket.socket.connect = _guarded_connect
    socket.socket.connect_ex = _guarded_connect_ex
    socket.getaddrinfo = _guarded_getaddrinfo


def pytest_unconfigure(config):
    shutil.rmtree(_KB_TMP, ignore_errors=True)


from backend.app import create_app  # noqa: E402
from backend.models.chat import db  # noqa: E402


@pytest.fixture
def app():
    """Create application for testing with in-memory database."""
    app = create_app('testing')

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.drop_all()
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///'):
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            if db_path and db_path != ':memory:' and os.path.exists(db_path):
                os.remove(db_path)


@pytest.fixture
def client(app):
    return app.test_client()
