"""The test suite is hermetic: live SBA ingests go to a temp dir (not the
tracked backend/knowledge_base/) and outbound network calls are blocked."""
import os
import socket
from pathlib import Path

import pytest
import requests

REPO_BACKEND = Path(__file__).resolve().parents[1]


def test_kb_live_dir_points_at_temp_dir():
    from backend.services.sba_rag_ingest import _kb_live_dir

    live = _kb_live_dir().resolve()
    assert os.environ.get("SBA_KB_LIVE_DIR")
    assert live == Path(os.environ["SBA_KB_LIVE_DIR"]).resolve()
    assert REPO_BACKEND not in live.parents


def test_ingest_writes_only_to_override_dir():
    from backend.services.sba_rag_ingest import ingest_sba_envelope

    envelope = {
        "path": "/api/sba/content/hermetic-test",
        "topic": {"title": "Hermetic test", "description": "Temp-dir ingest check."},
        "items": [{"id": "1", "title": "Item one", "summary": "Body text"}],
    }
    result = ingest_sba_envelope(envelope, route="/api/sba/content/hermetic-test", force=True)
    assert result.get("ok"), result
    kb_dir = Path(result["kb"]["dir"]).resolve()
    assert kb_dir == Path(os.environ["SBA_KB_LIVE_DIR"]).resolve()
    for written in result["kb"]["files"]:
        assert REPO_BACKEND not in Path(written).resolve().parents
    tracked_live = REPO_BACKEND / "knowledge_base" / "sba_api_live"
    assert not list(tracked_live.glob("api_sba_content_hermetic-test*"))


@pytest.mark.skipif(os.environ.get("ALLOW_NETWORK_TESTS") == "1", reason="network allowed")
def test_outbound_http_is_blocked():
    with pytest.raises((requests.exceptions.ConnectionError, OSError)):
        requests.get("https://www.sba.gov/", timeout=2)


@pytest.mark.skipif(os.environ.get("ALLOW_NETWORK_TESTS") == "1", reason="network allowed")
def test_outbound_socket_is_blocked_but_loopback_allowed():
    with pytest.raises(OSError):
        socket.create_connection(("93.184.216.34", 80), timeout=1)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        client = socket.create_connection(server.getsockname(), timeout=1)
        client.close()
    finally:
        server.close()
