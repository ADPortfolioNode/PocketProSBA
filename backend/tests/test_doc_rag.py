"""Upload -> index -> retrieve -> answer, for PDF, DOCX and TXT, without Chroma or Gemini.

Also covers the chat action layer: booking/task proposals and next steps.
"""
import io

import pytest

from backend.app import create_app
from backend.models.chat import db
from backend.tests.auth_helpers import auth_header

LEASE_TEXT = (
    "Commercial Lease Agreement for Night Owl Rehearsal Studios, 41-20 Main Street, Queens.\n\n"
    "Term. The lease term is five years, starting March 1, 2026 and ending February 28, 2031.\n\n"
    "Rent. Monthly base rent is $6,500, due on the first day of each month. Rent rises 3% each year.\n\n"
    "Soundproofing. The tenant may install soundproofing in rooms 1 through 4 with written landlord approval.\n\n"
    "Renewal. The tenant has one option to renew for five more years with 90 days written notice."
)


def make_pdf(lines):
    """A tiny valid text PDF (one page, Helvetica) built by hand."""
    content = "BT /F1 11 Tf 50 750 Td 14 TL " + " ".join(
        "(" + ln.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") + ") '" for ln in lines
    ) + " ET"
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{body}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


def make_docx(paragraphs):
    import docx

    d = docx.Document()
    for p in paragraphs:
        d.add_paragraph(p)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


@pytest.fixture
def app(tmp_path, monkeypatch):
    import backend.routes.files as files

    monkeypatch.setattr(files, "UPLOAD_FOLDER", str(tmp_path / "uploads"))
    monkeypatch.setenv("CHROMA_INGEST_ON_UPLOAD", "false")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    app = create_app("testing")
    app.config.update(TESTING=True, AUTH_REQUIRED=True)
    with app.app_context():
        db.create_all()
    return app


@pytest.fixture
def client(app):
    c = app.test_client()
    c.environ_base["HTTP_AUTHORIZATION"] = auth_header(app)["Authorization"]
    return c


def upload(client, name, data):
    return client.post("/api/files", data={"file": (io.BytesIO(data), name)}, content_type="multipart/form-data")


def chat(client, message, **extra):
    body = {"message": message, "session_id": "doc-test", "client_now": "2026-10-24T18:12"}
    body.update(extra)
    return client.post("/api/chat", json=body).get_json()


def test_txt_upload_is_indexed_and_listed(client):
    resp = upload(client, "studio_lease.txt", LEASE_TEXT.encode())
    body = resp.get_json()
    assert resp.status_code == 200
    assert body["indexed"] is True and body["document"]["chunks"] >= 1
    files = client.get("/api/documents/list").get_json()["files"]
    assert [f["filename"] for f in files] == ["studio_lease.txt"]  # the index file stays hidden
    assert files[0]["indexed"] is True


def test_pdf_upload_extracts_text_and_answers_with_citation(client):
    pdf = make_pdf(["Night Owl Studios Business Plan", "Expansion: add a recording room for $85,000.",
                    "Equipment: a 24-channel console and microphones."])
    body = upload(client, "business_plan.pdf", pdf).get_json()
    assert body["indexed"] is True
    got = chat(client, "How much will the recording room cost in my business plan?")
    assert got["grounded"] is True
    assert "$85,000" in got["response"]
    assert "business_plan.pdf, p. 1" in got["response"]
    assert got["sources"][0]["filename"] == "business_plan.pdf"


def test_docx_upload_and_doc_workflow_chat(client):
    body = upload(client, "lease.docx", make_docx(LEASE_TEXT.split("\n\n"))).get_json()
    assert body["indexed"] is True
    got = chat(client, "When does the lease end?", workflow="doc_qa", document="lease.docx")
    assert "February 28, 2031" in got["response"]
    assert "lease.docx" in got["response"]
    # and it ends with a next step the concierge can take
    assert "**Next step:**" in got["response"] and got["suggested_action"]["type"] in ("todo", "appointment")


def test_document_question_with_no_match_says_so(client):
    upload(client, "lease.txt", LEASE_TEXT.encode())
    got = chat(client, "What does it say about parking spaces for trucks?", document="lease.txt")
    assert got["grounded"] is True and "couldn't find" in got["response"]


def test_unreadable_file_is_saved_with_friendly_message(client):
    body = upload(client, "scan.pdf", b"%PDF-1.4 not really a pdf").get_json()
    assert body["success"] is True and body["indexed"] is False
    assert body["rag_status"] == "save_only"


def test_doc_workflow_without_uploads_points_to_upload(client):
    got = chat(client, "What does my lease say?", workflow="doc_qa")
    assert "upload" in got["response"].lower()


def test_gemini_answer_is_used_when_configured(client, monkeypatch):
    upload(client, "lease.txt", LEASE_TEXT.encode())
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    seen = {}

    def fake_generate(prompt):
        seen["prompt"] = prompt
        return "Your rent is $6,500 a month (lease.txt, section 1)."

    monkeypatch.setattr("backend.services.doc_qa.generate", fake_generate)
    got = chat(client, "How much is the rent in my lease?")
    assert got["answer_mode"] == "gemini"
    assert "$6,500" in got["response"] and "**Source:** lease.txt" in got["response"]
    assert "Monthly base rent" in seen["prompt"]  # the retrieved excerpt reached the model


def test_gemini_failure_falls_back_to_extractive(client, monkeypatch):
    upload(client, "lease.txt", LEASE_TEXT.encode())
    monkeypatch.setenv("GEMINI_API_KEY", "bad-key")

    def boom(prompt):
        raise RuntimeError("API key not valid")

    monkeypatch.setattr("backend.services.doc_qa.generate", boom)
    got = chat(client, "How much is the rent in my lease?")
    assert got["answer_mode"] == "extractive" and "$6,500" in got["response"]


def test_api_query_falls_back_to_local_index(client):
    upload(client, "lease.txt", LEASE_TEXT.encode())
    res = client.post("/api/query", json={"query": "soundproofing rooms", "top_k": 3}).get_json()
    assert res["results"] and res["results"][0]["metadata"]["filename"] == "lease.txt"


# --- chat actions -----------------------------------------------------------------

def test_chat_proposes_appointment_without_saving(client):
    got = chat(client, "book a band rehearsal Saturday 3pm, 2 hours")
    action = got["proposed_action"]
    assert action == {"type": "appointment", "data": {"title": "Band rehearsal", "start": "2026-10-31T15:00",
                                                      "duration_minutes": 120, "contact": "", "notes": ""}}
    assert "Add to calendar" in got["response"]
    assert client.get("/api/appointments").get_json()["appointments"] == []  # nothing saved until confirmed


def test_chat_proposes_tasks(client):
    got = chat(client, "Help me plan these tasks: order cables, fix the PA in room 2")
    assert [i["title"] for i in got["proposed_action"]["data"]["items"]] == ["Order cables", "Fix the PA in room 2"]
    assert client.get("/api/todos").get_json()["todos"] == []


def test_yes_after_next_step_reoffers_it(client, monkeypatch):
    from backend.services import concierge_actions

    body = {"response": "SBA 7(a) loans fund equipment.", "success": True}
    concierge_actions.add_next_step(body, "loan for recording gear", "funding", "sess-yes")
    assert body["suggested_action"]["type"] == "todo"
    got = chat(client, "yes please", session_id="sess-yes")
    assert got["proposed_action"] == body["suggested_action"]
