"""/api/diagnostics needs a token; a failed Chroma connect is cached briefly."""
import pytest

import backend.config as config_module
import backend.services.rag as rag
from backend.app import create_app
from backend.models.chat import db
from backend.tests.auth_helpers import auth_header


@pytest.fixture
def app(monkeypatch):
    cls = config_module.config["testing"]
    monkeypatch.setattr(cls, "RATELIMIT_ENABLED", False, raising=False)
    app = create_app("testing")
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_diagnostics_requires_token(app):
    res = app.test_client().get("/api/diagnostics")
    assert res.status_code == 401
    assert res.get_json()["code"] == "token_missing"


def test_diagnostics_ok_with_token(app):
    res = app.test_client().get("/api/diagnostics", headers=auth_header(app))
    assert res.status_code == 200
    assert res.get_json()["status"] == "operational"


class _DownChroma:
    calls = 0

    def __init__(self, host=None, port=None):
        type(self).calls += 1

    def is_available(self):
        return False


@pytest.fixture
def down_chroma(monkeypatch):
    import backend.services.chroma_fixed as chroma_fixed

    _DownChroma.calls = 0
    monkeypatch.setattr(chroma_fixed, "ChromaService", _DownChroma)
    monkeypatch.setattr(rag, "_rag_manager_instance", None)
    monkeypatch.setattr(rag, "_rag_failed_at", None)
    monkeypatch.setattr(rag, "CHROMA_RETRY_SECONDS", 30)
    return _DownChroma


def test_failed_chroma_connect_is_cached(down_chroma, monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr(rag.time, "monotonic", lambda: clock[0])

    first = rag.get_rag_manager()
    assert not first.is_available()
    assert down_chroma.calls == 1

    # Within the window: no new connect attempt.
    clock[0] += 10
    assert not rag.get_rag_manager().is_available()
    assert down_chroma.calls == 1

    # After the window: tries again.
    clock[0] += 25
    rag.get_rag_manager()
    assert down_chroma.calls == 2


def test_successful_connect_clears_failure(down_chroma, monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr(rag.time, "monotonic", lambda: clock[0])
    rag.get_rag_manager()
    assert rag._rag_failed_at == 1000.0

    clock[0] += 31
    monkeypatch.setattr(_DownChroma, "is_available", lambda self: True)
    monkeypatch.setattr(rag.RAGManager, "is_available", lambda self: True)
    manager = rag.get_rag_manager()
    assert manager.is_available()
    assert rag._rag_failed_at is None
