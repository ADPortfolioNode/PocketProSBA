"""Asserted concierge workflow tests.

These replace the old return-bool scripts in backend/test_concierge_workflows*.py
and test_hierarchical_workflow.py for CI purposes: pytest used to report those
scripts as "passed" even when they returned False, because they never asserted.
The scripts themselves are kept for manual runs, with canonical backend.*
imports, but this file is the asserted gate.
"""

from backend.assistants.concierge import Concierge
from backend.services.api_service import decompose_task_service
from backend.services.rag import RAGManager


def _concierge():
    return Concierge()


def test_intent_document_search():
    concierge = _concierge()
    assert concierge._classify_intent("find SBA loan documents", {}) == "document_search"
    assert concierge._classify_intent("search for business grants", {}) == "document_search"
    assert concierge._classify_intent("what is SBA", {}) == "document_search"


def test_intent_task_request():
    concierge = _concierge()
    assert concierge._classify_intent("help me create a business plan", {}) == "task_request"
    assert concierge._classify_intent("build a marketing strategy", {}) == "task_request"


def test_intent_strong_task_phrase_beats_embedded_search_word():
    # "research" contains "search", but the explicit task phrase must win.
    concierge = _concierge()
    message = (
        "Help me create a business plan for a small coffee shop. "
        "I need to research SBA loan options and create a marketing strategy."
    )
    assert concierge._classify_intent(message, {}) == "task_request"


def test_intent_greeting_and_acknowledgment():
    concierge = _concierge()
    assert concierge._classify_intent("hello how are you", {}) == "greeting"
    assert concierge._classify_intent("thank you", {}) == "acknowledgment"


def test_intent_follow_up_with_context():
    concierge = _concierge()
    conversation = {
        "messages": [
            {"role": "user", "content": "find SBA loan information"},
            {"role": "assistant", "content": "I found some documents about SBA loans..."},
        ]
    }
    assert concierge._classify_intent("more information", conversation) == "follow_up_query"
    assert concierge._classify_intent("next step", conversation) == "follow_up_query"
    assert concierge._classify_intent("what about grants", conversation) == "follow_up_query"


def test_concierge_handle_message_returns_text():
    concierge = _concierge()
    result = concierge.handle_message("Tell me about SBA loans", "test-concierge-workflow")
    assert isinstance(result, dict)
    assert result.get("text"), "concierge must return a non-empty text response"


def test_decompose_task_service_returns_steps():
    result = decompose_task_service("How to get SBA loan", "test-session-api")
    assert result["steps"]
    assert result["response"]["text"]


def test_info_request_is_a_task_with_expectation_and_limitation_notes():
    concierge = _concierge()
    result = concierge.handle_message(
        "What is an SBA 7(a) loan?", "test-concierge-expectation"
    )
    text = result.get("text", "")
    # Conversational task lead first, not a raw dump.
    assert text.startswith("Got it")
    assert "as a task" in text
    # Funding answers must carry expectation / liability management.
    assert "Expectation note:" in text
    assert "not a loan approval" in text
    # No Chroma in the test env, so the limitation must be stated.
    assert "Limitation:" in text


def test_rag_manager_unavailable_is_explicit():
    manager = RAGManager()
    assert manager.is_available() is False
    assert "error" in manager.query_documents("SBA loans", n_results=2)
