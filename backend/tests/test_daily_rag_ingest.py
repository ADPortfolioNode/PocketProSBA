"""Daily workflows in RAG: KB parity with the UI cards, keyword search,
hash-guarded ingest, and the concierge's Daily answer.

Generic only: no client brand name appears in any Daily task document.
"""

import re
from pathlib import Path

from backend.services.daily_rag_ingest import (
    ingest_daily_workflows,
    load_tasks,
    search_daily_workflows,
)


def _ui_card_titles():
    js = Path("frontend/src/components/ServiceDaily.js").read_text(encoding="utf-8")
    # WORKFLOW_CARDS entries are `title: '...'` lines.
    return set(re.findall(r"title:\s*'([^']+)'", js))


def test_kb_tasks_match_ui_cards_and_have_no_brand():
    tasks = load_tasks()
    assert len(tasks) == 13
    kb_titles = {t["title"] for t in tasks}
    ui_titles = _ui_card_titles()
    assert kb_titles == ui_titles, f"KB/UI drift: KB-only={kb_titles - ui_titles} UI-only={ui_titles - kb_titles}"
    blob = "\n".join(t["body"] for t in tasks)
    assert "Funkadelic" not in blob
    # The demo-only note lives in the document header, not in each task.
    from backend.services.daily_rag_ingest import kb_path

    assert "Demo only" in kb_path().read_text(encoding="utf-8")


def test_search_finds_room_booking_not_recording():
    hits = search_daily_workflows("how do I book a room for a band practice?")
    assert hits, "room booking query should match Daily tasks"
    assert hits[0]["service"] == "Rooms"
    assert "recording" not in hits[0]["title"].lower()


def test_search_does_not_surface_growth_for_plain_loan_question():
    hits = search_daily_workflows("what is an SBA 7a loan?")
    assert all(h["service"] != "Growth" for h in hits)


def test_search_finds_repair_intake():
    hits = search_daily_workflows("my guitar amp is broken, how do I get a repair estimate?")
    assert hits
    assert any("repair" in h["title"].lower() for h in hits)


def test_ingest_is_hash_guarded(monkeypatch, tmp_path):
    monkeypatch.setenv("SBA_KB_LIVE_DIR", str(tmp_path))
    added = []

    class FakeRAG:
        def is_available(self):
            return True

        def add_document(self, text, metadata=None):
            added.append(metadata.get("title"))
            return {"success": True}

    import backend.services.rag as rag_mod

    monkeypatch.setattr(rag_mod, "get_rag_manager", lambda: FakeRAG())
    first = ingest_daily_workflows()
    assert first["added"] == 13 and len(added) == 13
    second = ingest_daily_workflows()
    assert second.get("skipped") is True and len(added) == 13
    third = ingest_daily_workflows(force=True)
    assert third["added"] == 13 and len(added) == 26


def test_concierge_answers_daily_question():
    from backend.assistants.concierge import Concierge

    concierge = Concierge()
    result = concierge._handle_document_search("how do I book a room?", {})
    text = result.get("text", "")
    assert "Check availability" in text or "Add a demo booking" in text
    assert "/daily" in str(result.get("sources", ""))
    assert "Demo only" in text
