from flask import Blueprint, request, jsonify
import logging
from backend.services.api_service import (
    decompose_task_service,
    execute_step_service,
    validate_step_service,
    query_documents_service,
)
from backend.services.rag import get_rag_manager
from backend.enhanced_gemini_rag_service import enhanced_rag_service

logger = logging.getLogger(__name__)
rag_bp = Blueprint('rag', __name__)

@rag_bp.route('/health', methods=['GET'])
def rag_health():
    """RAG service health check"""
    try:
        rag_manager = get_rag_manager()
        if rag_manager.is_available():
            stats = rag_manager.get_collection_stats()
            document_count = stats.get('count', 0) if isinstance(stats, dict) else 0
            return jsonify({
                'status': 'ok',
                'message': 'RAG system is available and connected',
                'document_count': document_count
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'RAG system is not available'
            }), 503
    except Exception as e:
        logger.error(f"Error checking RAG health: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to check RAG health: {str(e)}'
        }), 500

@rag_bp.route('/decompose', methods=['POST'])
def decompose_task():
    """Decompose a user task into steps"""
    try:
        data = request.get_json()
        if not data:
            logger.warning("No JSON data provided for decompose task")
            return jsonify({'error': 'No JSON data provided'}), 400

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

@rag_bp.route('/execute', methods=['POST'])
def execute_step():
    """Execute a decomposed task step"""
    try:
        data = request.get_json()
        if not data:
            logger.warning("No JSON data provided for execute step")
            return jsonify({'error': 'No JSON data provided'}), 400

        task = data.get('task', {})
        result = execute_step_service(task)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error executing step: {str(e)}")
        return jsonify({'error': f'Failed to execute step: {str(e)}'}), 500

@rag_bp.route('/validate', methods=['POST'])
def validate_step():
    """Validate a step result"""
    try:
        data = request.get_json()
        if not data:
            logger.warning("No JSON data provided for validate step")
            return jsonify({'error': 'No JSON data provided'}), 400

        result = data.get('result', '')
        task = data.get('task', {})
        validation = validate_step_service(result, task)
        return jsonify(validation)

    except Exception as e:
        logger.error(f"Error validating step: {str(e)}")
        return jsonify({'error': f'Failed to validate step: {str(e)}'}), 500

@rag_bp.route('/query', methods=['POST'])
def query_documents():
    """Query documents"""
    try:
        data = request.get_json()
        if not data:
            logger.warning("No JSON data provided for query documents")
            return jsonify({'error': 'No JSON data provided'}), 400

        query = data.get('query', '')
        top_k = min(int(data.get('top_k', 5)), 20)

        if not query:
            logger.warning("Query is required for querying documents")
            return jsonify({'error': 'Query is required'}), 400

        # Use enhanced Gemini RAG service if available and initialized
        if enhanced_rag_service.is_initialized:
            results = enhanced_rag_service.search_documents(query, limit=top_k)
            return jsonify({
                'success': True,
                'query': query,
                'results': results,
                'count': len(results)
            })
        else:
            results = query_documents_service(query, top_k)
            return jsonify(results)

    except Exception as e:
        logger.error(f"Error querying documents: {str(e)}")
        return jsonify({'error': 'Failed to query documents'}), 500

@rag_bp.route('/sba-query', methods=['POST'])
def query_sba_documents():
    """Query SBA documents using Gemini RAG"""
    try:
        data = request.get_json()
        if not data:
            logger.warning("No JSON data provided for SBA query")
            return jsonify({'error': 'No JSON data provided'}), 400

        query = data.get('query', '')

        if not query:
            logger.warning("Query is required for SBA query")
            return jsonify({'error': 'Query is required'}), 400

        # Use enhanced Gemini RAG service for SBA queries
        if enhanced_rag_service.is_initialized:
            result = enhanced_rag_service.query_sba_loans(query)
            return jsonify(result)
        else:
            return jsonify({
                'error': 'Gemini RAG service not available',
                'answer': 'SBA query service is currently unavailable. Please try again later.'
            }), 503

    except Exception as e:
        logger.error(f"Error querying SBA documents: {str(e)}")
        return jsonify({'error': 'Failed to query SBA documents'}), 500

@rag_bp.route('/sba-overview', methods=['GET'])
def get_sba_overview():
    """Get SBA loan information overview"""
    try:
        if enhanced_rag_service.is_initialized:
            overview = enhanced_rag_service.get_sba_overview()
            return jsonify(overview)
        else:
            return jsonify({
                'error': 'Gemini RAG service not available',
                'message': 'SBA overview service is currently unavailable.'
            }), 503

    except Exception as e:
        logger.error(f"Error getting SBA overview: {str(e)}")
        return jsonify({'error': 'Failed to get SBA overview'}), 500
