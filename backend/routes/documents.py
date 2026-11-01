from flask import Blueprint, request, jsonify
import os
import logging
from werkzeug.utils import secure_filename
from backend.services.rag import get_rag_manager
from backend.routes._errors import internal_error_message
from backend.app.auth import auth_required

logger = logging.getLogger(__name__)
documents_bp = Blueprint('documents', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'md'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _upload_and_ingest():
    """Shared upload used by /upload and legacy /upload_and_ingest_document."""
    from backend.routes.files import process_upload
    return process_upload()


@documents_bp.route('/upload', methods=['POST', 'OPTIONS'])
@auth_required
def upload_file():
    """Upload a document and add it to RAG system"""
    if request.method == 'OPTIONS':
        return '', 204
    try:
        body, code = _upload_and_ingest()
        return jsonify(body), code
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({'error': internal_error_message(e), 'success': False}), 500


@documents_bp.route('/upload_and_ingest_document', methods=['POST', 'OPTIONS'])
@auth_required
def upload_and_ingest_document():
    """
    Prebuilt RAG SPA fallback:
      POST /api/documents/upload_and_ingest_document
    (often via double-prefix /api/api/documents/... rewritten to /api/documents/...)
    """
    if request.method == 'OPTIONS':
        return '', 204
    try:
        body, code = _upload_and_ingest()
        return jsonify(body), code
    except Exception as e:
        logger.error(f"Error upload_and_ingest: {str(e)}")
        return jsonify({'error': internal_error_message(e), 'success': False}), 500

def _upload_folder():
    """Folder uploads are saved to: the same one process_upload() writes
    (routes/files.py, honours the UPLOAD_FOLDER env var), so the Docs tab lists
    what was actually uploaded."""
    try:
        from backend.routes import files as files_routes
        return files_routes.UPLOAD_FOLDER
    except Exception:  # pragma: no cover - files blueprint unavailable
        return os.environ.get('UPLOAD_FOLDER', UPLOAD_FOLDER)


@documents_bp.route('/list', methods=['GET'])
@auth_required
def list_files():
    """List uploaded files"""
    try:
        folder = _upload_folder()
        if not os.path.exists(folder):
            return jsonify({'files': []}), 200

        files = []
        for filename in sorted(os.listdir(folder)):
            filepath = os.path.join(folder, filename)
            if os.path.isfile(filepath):
                files.append({
                    'filename': filename,
                    'size': os.path.getsize(filepath),
                    'modified': os.path.getmtime(filepath)
                })

        return jsonify({'files': files}), 200

    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return jsonify({'error': internal_error_message(e)}), 500

# Cap viewer text so one huge file cannot blow up the response or the modal.
MAX_VIEW_TEXT = 200000


@documents_bp.route('/view/<path:filename>', methods=['GET'])
@auth_required
def view_file(filename):
    """Return an uploaded file for in-app inspection.

    Uses the same extraction path as upload (routes/files._read_text: PDF via
    pypdf, DOCX via python-docx, plain text otherwise), so the viewer shows
    exactly what the app already extracted for RAG. Types with no extractable
    text (e.g. legacy .doc binaries) return extractable=false and no invented
    content -- the frontend shows an honest "preview not available" state.
    """
    try:
        safe = secure_filename(filename)
        if not safe or safe != filename or '/' in filename or '\\' in filename:
            return jsonify({'error': 'File not found'}), 404
        folder = _upload_folder()
        filepath = os.path.join(folder, safe)
        if not os.path.isfile(filepath):
            return jsonify({'error': 'File not found'}), 404
        from backend.routes.files import _read_text
        text = _read_text(filepath, safe) or ''
        # Legacy .doc binaries cannot be extracted with the installed
        # libraries (files._read_text would only decode them as
        # replacement characters): report honestly instead of showing garbage.
        ext_first = safe.rsplit('.', 1)[-1].lower() if '.' in safe else ''
        if ext_first == 'doc':
            text = ''
        extractable = bool(text.strip())
        truncated = len(text) > MAX_VIEW_TEXT
        if truncated:
            text = text[:MAX_VIEW_TEXT]
        ext = safe.rsplit('.', 1)[-1].lower() if '.' in safe else ''
        return jsonify({
            'filename': safe,
            'size': os.path.getsize(filepath),
            'modified': os.path.getmtime(filepath),
            'type': ext,
            'extractable': extractable,
            'truncated': truncated,
            'text': text if extractable else '',
        }), 200

    except Exception as e:
        logger.error(f"Error viewing file: {str(e)}")
        return jsonify({'error': internal_error_message(e)}), 500
