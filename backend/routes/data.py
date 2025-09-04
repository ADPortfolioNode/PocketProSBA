from flask import Blueprint, request, jsonify
import logging
import os
import time
from werkzeug.utils import secure_filename
from services.api_service import get_system_info_service
from services.rag import get_rag_manager
from config import Config

logger = logging.getLogger(__name__)
data_bp = Blueprint('data', __name__)

UPLOAD_FOLDER = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@data_bp.route('/info', methods=['GET'])
def get_system_info():
    """Get system information"""
    try:
        info = get_system_info_service()
        return jsonify(info)
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return jsonify({'error': 'Failed to retrieve system information'}), 500

@data_bp.route('/diagnostics', methods=['GET'])
def get_diagnostics():
    """Get diagnostics information"""
    try:
        diagnostics_info = {
            'status': 'operational',
            'message': 'All systems functional',
            'timestamp': time.time()
        }
        return jsonify(diagnostics_info), 200
    except Exception as e:
        logger.error(f"Error getting diagnostics: {str(e)}")
        return jsonify({'error': 'Failed to retrieve diagnostics'}), 500

@data_bp.route('/documents/upload', methods=['POST'])
def upload_file():
    """Upload a document and add it to RAG system"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)

            # Ensure upload directory exists
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            # Save the file
            file.save(filepath)

            # Read file content (for now, assume text files)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # For binary files, just store filename
                content = f"File: {filename}"

            # Add to RAG system
            rag_manager = get_rag_manager()
            if rag_manager.is_available():
                metadata = {
                    'filename': filename,
                    'filepath': filepath,
                    'size': os.path.getsize(filepath)
                }
                result = rag_manager.add_document(content, metadata)
                if 'error' in result:
                    logger.error(f"Failed to add document to RAG: {result['error']}")
                    return jsonify({'error': f"File saved but failed to add to RAG: {result['error']}"}), 500
            else:
                logger.warning("RAG system not available, file saved but not indexed")

            return jsonify({
                'message': 'File uploaded successfully',
                'filename': filename,
                'size': os.path.getsize(filepath),
                'rag_status': 'added' if rag_manager.is_available() else 'not_available'
            }), 200

        return jsonify({'error': 'File type not allowed'}), 400

    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@data_bp.route('/documents/list', methods=['GET'])
def list_files():
    """List uploaded files"""
    try:
        if not os.path.exists(UPLOAD_FOLDER):
            return jsonify({'files': []}), 200

        files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
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
