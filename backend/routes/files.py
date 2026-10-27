"""
File upload routes for prebuilt RAG SPA.

Prebuilt App.js posts:
  POST {API}/api/files   with FormData field "file"
where API base is often http://localhost:5000/api
→ hits /api/api/files (rewritten to /api/files by middleware).

Fallback path:
  POST /api/documents/upload_and_ingest_document
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from backend.routes._errors import internal_error_message
from backend.app.auth import auth_required

logger = logging.getLogger(__name__)
files_bp = Blueprint("files", __name__)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
ALLOWED_EXTENSIONS = {
    "txt", "md", "markdown", "csv", "json", "log",
    "pdf", "doc", "docx", "rtf", "html", "htm",
}


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _read_text(filepath: str, filename: str) -> str:
    """Extract searchable text from an uploaded file.

    Previously every file was read as UTF-8, so PDF and DOCX uploads were
    ingested into RAG as binary garbage and the concierge could never answer
    questions about them — the text was never actually in the index. Now:
    PDF via pypdf, DOCX via python-docx (both already in requirements),
    plain text/markdown as before. Legacy .doc binaries cannot be extracted
    with the installed libraries and return "" (upload still succeeds, but
    RAG ingest is skipped instead of storing garbage).
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    try:
        if ext == "pdf":
            from pypdf import PdfReader
            reader = PdfReader(filepath)
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        if ext == "docx":
            from docx import Document
            doc = Document(filepath)
            parts = [para.text for para in doc.paragraphs]
            for table in doc.tables:
                for row in table.rows:
                    parts.append(" | ".join(cell.text for cell in row.cells))
            return "\n".join(parts)
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as exc:
        logger.warning("Text extraction failed for %s: %s", filename, exc)
        return ""


def _chunk_text(content: str, size: int = 1200) -> list:
    """Split extracted text into retrievable chunks (was: one whole doc).

    One giant document embeds poorly and rarely surfaces for a specific
    question; ~1200-char paragraph-aware chunks let the concierge find the
    exact passage about, say, a lease term or a loan amount.
    """
    text = (content or "").strip()
    if not text:
        return []
    chunks, current = [], ""
    for para in text.split("\n"):
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) + 1 > size and current:
            chunks.append(current)
            current = para
        else:
            current = f"{current}\n{para}" if current else para
    if current:
        chunks.append(current)
    # A single over-long paragraph still gets hard-split so nothing is lost.
    out = []
    for chunk in chunks:
        while len(chunk) > size:
            out.append(chunk[:size])
            chunk = chunk[size:]
        if chunk:
            out.append(chunk)
    return out


def _estimate_chunks(content: str, size: int) -> int:
    chunks = _chunk_text(content)
    if chunks:
        return len(chunks)
    # binary / unreadable / nothing extractable
    return max(1, (size + 4095) // 4096)


def process_upload():
    """
    Shared upload + optional RAG ingest.
    Returns (json_dict, status_code).
    """
    if "file" not in request.files:
        # also accept common alternate field names
        file = None
        for key in ("document", "upload", "files"):
            if key in request.files:
                file = request.files[key]
                break
        if file is None:
            return {"error": "No file part (expected form field 'file')", "success": False}, 400
    else:
        file = request.files["file"]

    if not file or file.filename == "":
        return {"error": "No selected file", "success": False}, 400

    if not _allowed(file.filename):
        return {
            "error": f"File type not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            "success": False,
        }, 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filename = secure_filename(file.filename)
    if not filename:
        return {"error": "Invalid filename", "success": False}, 400

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    size = os.path.getsize(filepath)
    content = _read_text(filepath, filename)

    rag_status = "not_available"
    doc_id = f"doc_{int(datetime.now(timezone.utc).timestamp())}_{filename}"
    text_chunks = _chunk_text(content)
    chunks = len(text_chunks) if text_chunks else _estimate_chunks(content, size)
    pages = "Unknown"

    # Soft RAG ingest — never fail the upload if Chroma/Gemini is slow or down.
    # Nothing extractable (e.g. legacy .doc binary, scanned image PDF) means
    # save-only: the file is kept and listed, but no garbage is indexed.
    try:
        from backend.services.rag import get_rag_manager
        rag_manager = get_rag_manager()
        if not text_chunks:
            rag_status = "save_only"
        elif rag_manager and rag_manager.is_available():
            failed = False
            for i, chunk in enumerate(text_chunks):
                metadata = {
                    "filename": filename,
                    # basename only: never store/return absolute server paths
                    "filepath": filename,
                    "size": size,
                    "uploaded_at": datetime.now(timezone.utc).isoformat(),
                    "chunk_index": i,
                    "chunk_count": len(text_chunks),
                    "source": "upload",
                }
                # Stable id per chunk: re-uploading replaces, never duplicates.
                result = rag_manager.add_document(
                    chunk, metadata, doc_id=f"doc_{filename}_{i}"
                )
                if isinstance(result, dict) and result.get("error"):
                    logger.warning("RAG ingest soft-fail: %s", result.get("error"))
                    failed = True
                    break
            rag_status = "save_only" if failed else "added"
            doc_id = f"doc_{filename}_0"
        else:
            rag_status = "not_available"
    except Exception as e:
        logger.warning("RAG manager unavailable during upload: %s", e)
        rag_status = "save_only"

    # Prebuilt App.js expects .document with filename (+ optional pages/chunks)
    document = {
        "id": str(doc_id),
        "filename": filename,
        "name": filename,
        "size": size,
        "pages": pages,
        "chunks": chunks,
        "uploadTime": datetime.now(timezone.utc).isoformat(),
        "path": filename,
        "rag_status": rag_status,
    }

    # Always 200 when file is on disk — SPA treats non-2xx as hard failure
    return {
        "success": True,
        "message": "File uploaded successfully",
        "filename": filename,
        "size": size,
        "rag_status": rag_status,
        "document": document,
        # aliases some clients use
        "file": document,
        "result": document,
    }, 200


@files_bp.route("", methods=["POST", "OPTIONS"])
@files_bp.route("/", methods=["POST", "OPTIONS"])
@auth_required
def upload_files_root():
    """POST /api/files"""
    if request.method == "OPTIONS":
        return "", 204
    try:
        body, code = process_upload()
        return jsonify(body), code
    except Exception as e:
        logger.exception("Upload /api/files failed")
        return jsonify({"error": internal_error_message(e), "success": False}), 500


@files_bp.route("/upload", methods=["POST", "OPTIONS"])
@auth_required
def upload_files_upload():
    """POST /api/files/upload"""
    if request.method == "OPTIONS":
        return "", 204
    try:
        body, code = process_upload()
        return jsonify(body), code
    except Exception as e:
        logger.exception("Upload /api/files/upload failed")
        return jsonify({"error": internal_error_message(e), "success": False}), 500
