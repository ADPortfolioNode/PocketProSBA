from flask import Blueprint, request, jsonify
from backend.services.api_service import (
    get_system_info_service,
    decompose_task_service,
    execute_step_service,
    validate_step_service,
    query_documents_service,
)

api_bp = Blueprint('api', __name__)

@api_bp.route('/info', methods=['GET'])
def get_system_info():
    """Get system information"""
    try:
        info = get_system_info_service()
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/decompose', methods=['POST'])
def decompose_task():
    """Decompose a user task into steps"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        message = data.get('message', '')
        session_id = data.get('session_id')

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        response = decompose_task_service(message, session_id)
        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/execute', methods=['POST'])
def execute_step():
    """Execute a decomposed task step"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        task = data.get('task', {})
        result = execute_step_service(task)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/validate', methods=['POST'])
def validate_step():
    """Validate a step result"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        result = data.get('result', '')
        task = data.get('task', {})
        validation = validate_step_service(result, task)
        return jsonify(validation)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/query', methods=['POST'])
def query_documents():
    """Query documents"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        query = data.get('query', '')
        top_k = min(int(data.get('top_k', 5)), 20)

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        results = query_documents_service(query, top_k)
        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


