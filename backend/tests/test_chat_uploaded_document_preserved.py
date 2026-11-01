"""Regression tests for the /api/chat uploaded-document loss.

Root cause (2026-11-01): Concierge.handle_message correctly returned an
uploaded-document answer (SBA answer first, uploaded document as supporting
bonus material), but process_chat_message then replaced it wholesale with
generic SBA hits. Two defects combined:

1. The "already formatted" check compared the mixed-case phrase
   "clear summary from live SBA" against text.lower(), which can never
   match, so every SBA-summary answer was treated as unformatted.
2. Nothing protected an uploaded-document answer from that replacement.

These tests mock the concierge (as test_chat_service.py does) so they run
without Chroma or an LLM key, and assert the concierge answer survives.
"""

from unittest.mock import Mock, patch

from backend.services.chat_processing_service import process_chat_message


def _run_with_concierge_answer(text, sources):
    with patch(
        "backend.services.chat_processing_service.get_concierge"
    ) as mock_get_concierge:
        mock_concierge = Mock()
        mock_concierge.handle_message.return_value = {
            "success": True,
            "text": text,
            "sources": sources,
        }
        mock_concierge.conversation_store = {}
        mock_get_concierge.return_value = mock_concierge
        return process_chat_message(1, "What does the ZebraQuill program offer?", "test-uploaded")


def test_uploaded_document_answer_is_not_replaced_by_sba_hits():
    """An uploaded-document answer must survive process_chat_message."""
    text = (
        "Got it — I'll take that as a task: find SBA guidance on "
        "What does the ZebraQuill program offer?\n\n"
        "From your uploaded document **testdoc.txt**:\n\n"
        "The ZebraQuill program offers small businesses a lavender grant "
        "of up to 9000 dollars. Applicants must file form ZQ-7 within 30 days.\n\n"
        "Open Documents to see the full file."
    )
    sources = [{"title": "testdoc.txt", "path": "/documents", "url": "/documents"}]
    result = _run_with_concierge_answer(text, sources)
    assert result["success"] is True
    # Distinctive document content, not merely a word from the question.
    assert "lavender" in result["answer"]
    assert "ZQ-7" in result["answer"]
    # The uploaded source survives in the panel, not replaced by SBA hits.
    assert any(s.get("path") == "/documents" for s in result["sources"])
    assert not result["answer"].startswith("Here is what I found on")


def test_sba_summary_answer_is_recognised_as_formatted():
    """The SBA-summary phrase must match case-insensitively."""
    text = (
        "Here’s a clear summary from live SBA resources about loans:\n\n"
        "Some SBA guidance about loan programs."
    )
    sources = [{"title": "SBA Loans", "path": "/api/sba/content/loans"}]
    result = _run_with_concierge_answer(text, sources)
    assert result["success"] is True
    assert result["answer"].startswith(
        "Here’s a clear summary from live SBA resources about loans:"
    )
    assert not result["answer"].startswith("Here is what I found on")
