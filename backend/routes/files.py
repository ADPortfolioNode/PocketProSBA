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
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return f"Uploaded file: {filename}"


def _estimate_chunks(content: str, size: int) -> int:
    if content and not content.startswith("Uploaded file:"):
        # rough chunk estimate ~800 chars
        return max(1, (len(content) + 799) // 800)
    # binary / unreadable
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
    chunks = _estimate_chunks(content, size)
    pages = "Unknown"

    # Soft RAG ingest — never fail the upload if Chroma/Gemini is slow or down
    try:
        from backend.services.rag import get_rag_manager
        rag_manager = get_rag_manager()
        if rag_manager and rag_manager.is_available():
            metadata = {
                "filename": filename,
                "filepath": filepath,
                "size": size,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            }
            result = rag_manager.add_document(content, metadata)
            if isinstance(result, dict) and result.get("error"):
                logger.warning("RAG ingest soft-fail: %s", result.get("error"))
                rag_status = "save_only"
            else:
                rag_status = "added"
                if isinstance(result, dict) and result.get("ids"):
                    ids = result["ids"]
                    doc_id = ids[0] if isinstance(ids, list) and ids else ids
                elif isinstance(result, dict) and result.get("id"):
                    doc_id = result["id"]
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
        "path": filepath,
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
def upload_files_root():
    """POST /api/files"""
    if request.method == "OPTIONS":
        return "", 204
    try:
        body, code = process_upload()
        return jsonify(body), code
    except Exception as e:
        logger.exception("Upload /api/files failed")
        return jsonify({"error": str(e), "success": False}), 500


@files_bp.route("/upload", methods=["POST", "OPTIONS"])
def upload_files_upload():
    """POST /api/files/upload"""
    if request.method == "OPTIONS":
        return "", 204
    try:
        body, code = process_upload()
        return jsonify(body), code
    except Exception as e:
        logger.exception("Upload /api/files/upload failed")
        return jsonify({"error": str(e), "success": False}), 500
