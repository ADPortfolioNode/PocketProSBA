from flask import Blueprint, request, jsonify
import logging
import time

logger = logging.getLogger(__name__)
from backend.services.api_service import (
    get_system_info_service,
    decompose_task_service,
    execute_step_service,
    validate_step_service,
    query_documents_service,
)
from backend.services.rag import get_rag_manager

api_bp = Blueprint('api', __name__)


def _get_json_payload():
    """Parse JSON body; return 400 for malformed JSON."""
    data = request.get_json(silent=True)
    if data is not None:
        return data, None
    if request.data:
        return None, (jsonify({'error': 'Bad Request'}), 400)
    return None, (jsonify({'error': 'No JSON data provided'}), 400)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    server_info = {'self': request.host_url.rstrip('/')}
    return jsonify({'status': 'healthy', 'server': server_info}), 200


@api_bp.route('/programs', methods=['GET'])
def list_sba_programs():
    """
    Static SBA program catalog for the SBA Content tab.
    Avoids empty UI when external program APIs are unavailable.
    """
    programs = [
        {
            'id': 'loans',
            'name': 'SBA Loans',
            'description': '7(a), 504, Microloan, and Express financing options',
            'icon': '💰',
        },
        {
            'id': 'contracting',
            'name': 'Government Contracting',
            'description': 'Certifications and support to win federal contracts',
            'icon': '📝',
        },
        {
            'id': 'disaster',
            'name': 'Disaster Assistance',
            'description': 'Recovery loans after declared disasters',
            'icon': '🚨',
        },
        {
            'id': 'counseling',
            'name': 'Counseling & Training',
            'description': 'SBDC, SCORE, WBC, and VBOC mentoring',
            'icon': '👥',
        },
        {
            'id': 'international',
            'name': 'International Trade',
            'description': 'Export financing and market expansion support',
            'icon': '🌎',
        },
        {
            'id': 'innovation',
            'name': 'SBIR/STTR',
            'description': 'R&D grants for innovative small businesses',
            'icon': '💡',
        },
    ]
    return jsonify(programs), 200

@api_bp.route('/chromadb_health', methods=['GET'])
def chromadb_health_check():
    """ChromaDB health check endpoint"""
    server_info = {'self': request.host_url.rstrip('/')}
    try:
        rag_manager = get_rag_manager()
        if rag_manager.is_available():
            return jsonify({
                'status': 'ok',
                'server': server_info,
                'message': 'ChromaDB is available and connected',
                'document_count': rag_manager.get_document_count()
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'server': server_info,
                'message': 'ChromaDB is not available',
                'document_count': 0
            }), 200
    except Exception as e:
        logger.error(f"Error checking ChromaDB health: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to check ChromaDB health: {str(e)}'
        }), 500

@api_bp.route('/info', methods=['GET'])
def get_system_info():
    """Get system information"""
    try:
        info = get_system_info_service()
        info['server'] = {
            'self': request.host_url.rstrip('/'),
            'host': request.host,
            'scheme': request.scheme
        }
        return jsonify(info)
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return jsonify({'error': 'Failed to retrieve system information'}), 500

@api_bp.route('/diagnostics', methods=['GET'])
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

@api_bp.route('/decompose', methods=['POST'])
def decompose_task():
    """Decompose a user task into steps"""
    try:
        data, error = _get_json_payload()
        if error:
            return error

        message = data.get('message', '')
        session_id = data.get('session_id')

        if not message:
            logger.warning("Message is required for decompose task")
            return jsonify({'error': 'Message is required'}), 400

        response = decompose_task_service(message, session_id)
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error decomposing task: {str(e)}")
        return jsonify({'error': f'Failed to process message: {str(e)}'}), 500

@api_bp.route('/execute', methods=['POST'])
def execute_step():
    """Execute a decomposed task step"""
    try:
        data, error = _get_json_payload()
        if error:
            return error

        task = data.get('task', {})
        result = execute_step_service(task)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error executing step: {str(e)}")
        return jsonify({'error': f'Failed to execute step: {str(e)}'}), 500

@api_bp.route('/validate', methods=['POST'])
def validate_step():
    """Validate a step result"""
    try:
        data, error = _get_json_payload()
        if error:
            return error

        result = data.get('result', '')
        task = data.get('task', {})
        validation = validate_step_service(result, task)
        return jsonify(validation)

    except Exception as e:
        logger.error(f"Error validating step: {str(e)}")
        return jsonify({'error': f'Failed to validate step: {str(e)}'}), 500

@api_bp.route('/query', methods=['POST'])
def query_documents():
    """Query documents"""
    try:
        data, error = _get_json_payload()
        if error:
            return error

        query = data.get('query', '')
        top_k = min(int(data.get('top_k', 5)), 20)

        if not query:
            logger.warning("Query is required for querying documents")
            return jsonify({'error': 'Query is required'}), 400

        results = query_documents_service(query, top_k)
        return jsonify(results)

    except Exception as e:
        logger.error(f"Error querying documents: {str(e)}")
        return jsonify({'error': 'Failed to query documents'}), 500
