"""Concierge answers from the user's own uploaded documents first.

Covers: chunking splits long text; DOCX text is extracted (PDF/DOCX were
previously ingested as binary garbage); the concierge's uploaded-document
check finds a RAG chunk by filename metadata, and its direct-file fallback
finds a file even when RAG is unavailable; an unrelated question does not
hijack an uploaded document.
"""
from docx import Document

from backend.assistants.concierge import Concierge
from backend.routes.files import _chunk_text, _read_text


def test_chunking_splits_long_text(tmp_path):
    text = "\n".join(f"Paragraph {i} about rehearsal room rates." for i in range(60))
    chunks = _chunk_text(text)
    assert len(chunks) > 1
    assert all(len(c) <= 1200 for c in chunks)
    assert "Paragraph 59" in chunks[-1]


def test_docx_text_extracted(tmp_path):
    path = tmp_path / "lease.docx"
    doc = Document()
    doc.add_paragraph("Monthly rent is $2,400 for Studio 3.")
    doc.add_paragraph("The lease renews every twelve months.")
    doc.save(str(path))
    text = _read_text(str(path), "lease.docx")
    assert "Monthly rent is $2,400" in text
    assert "twelve months" in text


def test_txt_extracted(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("Deposit is fifty percent, due at booking.")
    assert "fifty percent" in _read_text(str(path), "notes.txt")


class _FakeRag:
    def __init__(self, hits):
        self._hits = hits

    def query_documents(self, message, n_results=6):
        return self._hits


def test_uploaded_document_answer_from_rag_chunk():
    concierge = Concierge()
    concierge.rag_manager = _FakeRag({
        "documents": [["Monthly rent is $2,400 for Studio 3, due on the first."]],
        "metadatas": [[{"filename": "lease.docx"}]],
    })
    answer = concierge._uploaded_document_answer("what does my lease say about rent?")
    assert answer is not None
    assert "lease.docx" in answer["text"]
    assert "$2,400" in answer["text"]
    assert answer["sources"][0]["path"] == "/documents"


def test_uploaded_document_answer_from_file_when_rag_down(monkeypatch, tmp_path):
    (tmp_path / "policy.txt").write_text("Cancellation requires five days notice for Studio 1.")
    import backend.routes.files as files_routes
    monkeypatch.setattr(files_routes, "UPLOAD_FOLDER", str(tmp_path))
    concierge = Concierge()
    concierge.rag_manager = None
    answer = concierge._uploaded_document_answer("what is the cancellation policy in my document?")
    assert answer is not None
    assert "policy.txt" in answer["text"]
    assert "five days" in answer["text"]


def test_unrelated_question_does_not_hijack_uploaded_document():
    concierge = Concierge()
    concierge.rag_manager = _FakeRag({
        "documents": [["Monthly rent is $2,400 for Studio 3."]],
        "metadatas": [[{"filename": "lease.docx"}]],
    })
    # Only one overlapping word ("loan" is not in the doc; "sba" neither).
    assert concierge._uploaded_document_answer("what is an SBA 7a loan?") is None


# --- Combined SBA + uploaded-file answers (conversation first, files bonus) ---

def _concierge_with_uploaded(monkeypatch):
    concierge = Concierge()
    concierge.rag_manager = None
    monkeypatch.setattr(
        concierge,
        "_uploaded_document_answer",
        lambda message: {
            "text": "From your uploaded document **lease.docx**:\n\nMonthly rent is $2,400.",
            "sources": [{"title": "lease.docx", "path": "/documents", "url": "/documents"}],
        },
    )
    return concierge


def test_sba_answer_first_with_uploaded_file_as_bonus(monkeypatch):
    import backend.routes.rag as rag_routes

    monkeypatch.setattr(
        rag_routes,
        "_local_kb_sba_answer",
        lambda message, max_chunks=6: {
            "mode": "sba_api_live",
            "answer": "SBA 7(a) loans support working capital.",
            "source_documents": [],
            "sources": [],
        },
    )
    concierge = _concierge_with_uploaded(monkeypatch)
    result = concierge._handle_document_search("what does my lease say about rent?", {})
    assert "SBA 7(a)" in result["text"]
    # SBA leads, the file is a bonus after it — not a replacement answer.
    assert result["text"].index("SBA 7(a)") < result["text"].index("lease.docx")
    assert "As a bonus" in result["text"]
    # The file link lives in Resources (sources), not as a link list in the bubble.
    assert "## Links" not in result["text"]
    assert any(s.get("path") == "/documents" for s in result["sources"])


def test_sba_only_when_no_uploaded_match(monkeypatch):
    import backend.routes.rag as rag_routes

    monkeypatch.setattr(
        rag_routes,
        "_local_kb_sba_answer",
        lambda message, max_chunks=6: {
            "mode": "sba_api_live",
            "answer": "SBA 7(a) loans support working capital.",
            "source_documents": [],
            "sources": [],
        },
    )
    concierge = Concierge()
    concierge.rag_manager = None
    monkeypatch.setattr(concierge, "_uploaded_document_answer", lambda message: None)
    result = concierge._handle_document_search("what is an SBA 7a loan?", {})
    assert "SBA 7(a)" in result["text"]
    assert "As a bonus" not in result["text"]
