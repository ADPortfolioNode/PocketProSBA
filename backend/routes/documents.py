from flask import Blueprint, request, jsonify
import os
import logging
from werkzeug.utils import secure_filename
from backend.services.rag import get_rag_manager

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
def upload_file():
    """Upload a document and add it to RAG system"""
    if request.method == 'OPTIONS':
        return '', 204
    try:
        body, code = _upload_and_ingest()
        return jsonify(body), code
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500


@documents_bp.route('/upload_and_ingest_document', methods=['POST', 'OPTIONS'])
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
        return jsonify({'error': str(e), 'success': False}), 500

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
        return jsonify({'error': str(e)}), 500
