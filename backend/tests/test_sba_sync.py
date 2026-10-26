"""Tests for the SBA content sync: change detection, stable ids, scheduling.

No network: fetchers and RAG are fakes. The sync must never blank stored
content on failure, and a re-ingest must replace — never duplicate — a doc.
"""

import os
from datetime import datetime, timezone

import pytest

os.environ.setdefault("SBA_KB_LIVE_DIR", os.path.join(os.getcwd(), ".pytest-sba-sync"))

from backend.services import sba_sync
from backend.services.sba_rag_ingest import _ingest_chroma
from backend.services.rag import RAGManager


def _env(items):
    return {"path": "/api/sba/content/loans", "items": items, "is_current": True}


def test_canonical_hash_ignores_key_order_and_detects_change():
    a = _env([{"title": "7(a)", "amount": 5}])
    b = _env([{"amount": 5, "title": "7(a)"}])
    c = _env([{"title": "7(a)", "amount": 6}])
    assert sba_sync.canonical_hash(a) == sba_sync.canonical_hash(b)
    assert sba_sync.canonical_hash(a) != sba_sync.canonical_hash(c)


def test_run_sync_skips_unchanged_and_reingests_changed(monkeypatch, tmp_path):
    monkeypatch.setenv("SBA_KB_LIVE_DIR", str(tmp_path))
    calls = []

    def fetcher(route):
        return _env([{"title": "7(a)"}])

    def fake_ingest(envelope, route="", title="", force=False):
        calls.append(route)
        return {"ok": True}

    monkeypatch.setattr(sba_sync, "CORE_ROUTES", ["/api/sba/content/loans"])
    # Patch the ingest import site used inside run_sync.
    import backend.services.sba_rag_ingest as ingest_mod

    monkeypatch.setattr(ingest_mod, "ingest_sba_envelope", fake_ingest)

    first = sba_sync.run_sync(fetcher=fetcher)
    assert first["changed"] == 1 and first["unchanged"] == 0
    second = sba_sync.run_sync(fetcher=fetcher)
    assert second["changed"] == 0 and second["unchanged"] == 1
    assert len(calls) == 1, "unchanged routes must not be re-ingested"

    def changed_fetcher(route):
        return _env([{"title": "7(a) updated"}])

    third = sba_sync.run_sync(fetcher=changed_fetcher)
    assert third["changed"] == 1
    assert len(calls) == 2


def test_run_sync_keeps_last_good_on_fetch_failure(monkeypatch, tmp_path):
    monkeypatch.setenv("SBA_KB_LIVE_DIR", str(tmp_path))
    monkeypatch.setattr(sba_sync, "CORE_ROUTES", ["/api/sba/content/loans"])
    import backend.services.sba_rag_ingest as ingest_mod

    monkeypatch.setattr(ingest_mod, "ingest_sba_envelope", lambda *a, **k: {"ok": True})
    sba_sync.run_sync(fetcher=lambda r: _env([{"title": "7(a)"}]))

    def failing(route):
        raise RuntimeError("SBA unreachable")

    summary = sba_sync.run_sync(fetcher=failing)
    assert summary["failed"] == 1 and summary["changed"] == 0
    state = sba_sync.load_state()
    assert state["routes"]["/api/sba/content/loans"]["status"] == "changed"


def test_stable_doc_id_replaces_not_duplicates(monkeypatch):
    class FakeChroma:
        def __init__(self):
            self.store = {}

        def upsert_documents(self, texts, metadatas=None, ids=None):
            for text, meta, doc_id in zip(texts, metadatas or [{}], ids or []):
                self.store[doc_id] = (text, meta)
            return {"success": True, "count": len(texts), "ids": ids}

    fake = FakeChroma()

    class FakeRAG:
        def is_available(self):
            return True

        def add_document(self, text, metadata=None, doc_id=None):
            return fake.upsert_documents([text], [metadata or {}], ids=[doc_id])

    import backend.services.rag as rag_mod

    monkeypatch.setattr(rag_mod, "get_rag_manager", lambda: FakeRAG())
    docs_v1 = [("7(a) max $5M", {"kind": "child_item", "item_id": "7a", "title": "7(a)"})]
    docs_v2 = [("7(a) max $5M, updated", {"kind": "child_item", "item_id": "7a", "title": "7(a)"})]
    _ingest_chroma(docs_v1, "/api/sba/content/loans/7a")
    _ingest_chroma(docs_v2, "/api/sba/content/loans/7a")
    assert len(fake.store) == 1, "same route+item must map to one vector"
    assert "updated" in next(iter(fake.store.values()))[0]


def test_rag_manager_upsert_path():
    class FakeChroma:
        def __init__(self):
            self.calls = []

        def is_available(self):
            return True

        def upsert_documents(self, texts, metadatas=None, ids=None):
            self.calls.append(("upsert", ids))
            return {"success": True}

    fake = FakeChroma()
    mgr = RAGManager(chroma_service=fake)
    mgr.available = True
    result = mgr.add_document("hello", {}, doc_id="sba-abc")
    assert result["success"] is True
    assert fake.calls == [("upsert", ["sba-abc"])]


def test_seconds_until_next_run():
    now = datetime(2026, 10, 25, 1, 0, tzinfo=timezone.utc)
    assert sba_sync.seconds_until_next_run(now, 3) == 2 * 3600
    late = datetime(2026, 10, 25, 5, 0, tzinfo=timezone.utc)
    assert sba_sync.seconds_until_next_run(late, 3) == 22 * 3600
