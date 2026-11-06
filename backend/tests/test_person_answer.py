"""Person questions must be answered from the user's own documents only.

Regression for the 2026-10-27 screenshot report: "who is anthony
dickerson" was answered with SBA program documents (microloan docs,
business plan, microlenders) even though the user had uploaded a resume
to RAG. SBA API endpoints return program content, not person records,
so their results are not an answer to a person question — and the
concierge must check local uploads (wide enough that SBA chunks cannot
crowd them out) before any SBA path runs.
"""

from backend.assistants.concierge import Concierge, _person_name_from


RESUME_CHUNK = (
    "Anthony Dickerson — builder and operator. Experience in rehearsal "
    "studios, recording, and small business operations in New York."
)
SBA_CHUNK = (
    "Microloans of up to $50,000 help small businesses start up and expand. "
    "Current link on sba.gov — open source for full official details."
)


class _FakeRag:
    def __init__(self, documents, metadatas):
        self._documents = documents
        self._metadatas = metadatas
        self.seen_n_results = None

    def query_documents(self, message, n_results=6):
        self.seen_n_results = n_results
        return {"documents": [self._documents], "metadatas": [self._metadatas]}

    def is_available(self):
        return True


def _concierge_with(documents, metadatas):
    concierge = Concierge()
    concierge.rag_manager = _FakeRag(documents, metadatas)
    return concierge


def test_person_name_detection():
    assert _person_name_from("who is anthony dickerson") == (
        "anthony dickerson",
        ["anthony", "dickerson"],
    )
    assert _person_name_from("Who was Anthony Dickerson?") is not None
    # The assistant itself and SBA roles are not personal-name questions.
    assert _person_name_from("who are you") is None
    assert _person_name_from("who is the SBA administrator") is None
    assert _person_name_from("what is a microloan") is None
    assert _person_name_from("how do I get a loan") is None


def test_person_question_answered_from_uploaded_resume_not_sba():
    # SBA chunks crowd the result set; the resume chunk is last.
    concierge = _concierge_with(
        [SBA_CHUNK, SBA_CHUNK, SBA_CHUNK, RESUME_CHUNK],
        [{}, {}, {}, {"filename": "Anthony_Dickerson_Resume.pdf"}],
    )
    result = concierge.handle_message("who is anthony dickerson", "test-person")
    text = result.get("text", "")
    assert "Anthony_Dickerson_Resume.pdf" in text
    assert "Anthony Dickerson" in text
    # No SBA program content presented as the answer.
    assert "Microloans" not in text
    assert "microlenders" not in text.lower()
    assert "Current link" not in text
    assert "find SBA guidance on who is anthony dickerson" not in text
    # Sources carry only the uploaded document.
    assert result.get("sources") == [
        {"title": "Anthony_Dickerson_Resume.pdf", "path": "/documents", "url": "/documents"}
    ]
    # The wide RAG read is what lets the resume survive SBA crowding.
    assert concierge.rag_manager.seen_n_results >= 20


def test_person_question_with_only_first_name_in_doc_is_not_a_match():
    # A chunk mentioning only "Anthony" does not prove it is about
    # Anthony Dickerson, so it must not be presented as the answer.
    concierge = _concierge_with(
        ["Anthony worked in retail for ten years."],
        [{"filename": "someone_else_resume.pdf"}],
    )
    result = concierge.handle_message("who is anthony dickerson", "test-person-2")
    text = result.get("text", "")
    assert "don't have information about anthony dickerson" in text
    assert "someone_else_resume.pdf" not in text
    assert not result.get("sources")  # report_success omits empty sources


def test_person_question_with_no_uploaded_match_says_so_plainly():
    concierge = _concierge_with([], [])
    result = concierge.handle_message("who is jordan lee", "test-person-3")
    text = result.get("text", "")
    assert "don't have information about jordan lee" in text
    assert "don't hold person records" in text
    assert not result.get("sources")  # report_success omits empty sources
