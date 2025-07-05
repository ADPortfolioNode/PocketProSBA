import os
import logging
import time
import json
import uuid
from flask import Blueprint, request, jsonify, current_app

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__)

@api_bp.route('/info', methods=['GET'])
def get_system_info():
    """Get system information"""
    try:
        # Get RAG manager instance
        from backend.services.rag import get_rag_manager
        rag_manager = get_rag_manager()
        
        # Get collection stats
        collection_stats = rag_manager.get_collection_stats() if rag_manager.is_available() else {"count": 0}
        
        return jsonify({
            'service': 'PocketPro:SBA Edition',
            'version': '1.0.0',
            'status': 'operational',
            'rag_status': 'available' if rag_manager.is_available() else 'unavailable',
            'vector_store': 'ChromaDB',
            'document_count': collection_stats.get("count", 0)
        })
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return jsonify({
            'service': 'PocketPro:SBA Edition',
            'version': '1.0.0',
            'status': 'operational',
            'rag_status': 'unavailable',
            'error': str(e)
        })

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
        
        # Get concierge instance
        from backend.assistants.concierge import Concierge
        concierge = Concierge()
        
        # Handle message
        response = concierge.handle_message(message, session_id)
        
        return jsonify({
            'response': {
                'text': response.get('text', ''),
                'sources': response.get('sources', []),
                'timestamp': response.get('timestamp')
            }
        })
        
    except Exception as e:
        logger.error(f"Error decomposing task: {str(e)}")
        return jsonify({'error': f'Failed to process message: {str(e)}'}), 500

@api_bp.route('/execute', methods=['POST'])
def execute_step():
    """Execute a decomposed task step"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        task = data.get('task', {})
        step_number = task.get('step_number')
        instruction = task.get('instruction', '')
        agent_type = task.get('suggested_agent_type', 'SearchAgent')
        
        if not instruction:
            return jsonify({'error': 'Instruction is required'}), 400
        
        # Execute based on agent type
        if agent_type == 'SearchAgent':
            from backend.assistants.search import SearchAgent
            agent = SearchAgent()
            result = agent.handle_message(instruction)
        else:
            # Default to concierge
            from backend.assistants.concierge import Concierge
            agent = Concierge()
            result = agent.handle_message(instruction)
        
        return jsonify({
            'step_number': step_number,
            'status': 'completed' if not result.get('error') else 'failed',
            'result': result.get('text', ''),
            'sources': result.get('sources', [])
        })
        
    except Exception as e:
        logger.error(f"Error executing step: {str(e)}")
        return jsonify({'error': f'Failed to execute step: {str(e)}'}), 500

@api_bp.route('/validate', methods=['POST'])
def validate_step():
    """Validate a step result"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        result = data.get('result', '')
        task = data.get('task', {})
        
        # Simple validation for now
        if result:
            return jsonify({
                'status': 'PASS',
                'confidence': 0.9,
                'feedback': 'Step result validated successfully'
            })
        else:
            return jsonify({
                'status': 'FAIL',
                'confidence': 0.2,
                'feedback': 'Step result is empty or invalid'
            })
        
    except Exception as e:
        logger.error(f"Error validating step: {str(e)}")
        return jsonify({'error': f'Failed to validate step: {str(e)}'}), 500

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
        
        # Get RAG manager instance
        from backend.services.rag import get_rag_manager
        rag_manager = get_rag_manager()
        
        # Query documents
        results = rag_manager.query_documents(query, n_results=top_k)
        
        # Format results
        formatted_results = []
        if "documents" in results and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                formatted_results.append({
                    'id': results["ids"][0][i],
                    'content': doc,
                    'metadata': results["metadatas"][0][i],
                    'distance': results["distances"][0][i] if "distances" in results else 0.0,
                    'relevance_score': 1.0 - (results["distances"][0][i] if "distances" in results else 0.0)
                })
        
        return jsonify({
            'success': True,
            'query': query,
            'results': formatted_results,
            'count': len(formatted_results)
        })
        
    except Exception as e:
        logger.error(f"Error querying documents: {str(e)}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@api_bp.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint powered by RAG"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        message = data.get('message', '')
        session_id = data.get('session_id')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get concierge instance
        from backend.assistants.concierge import Concierge
        concierge = Concierge()
        
        # Handle message
        response = concierge.handle_message(message, session_id)
        
        # Emit response through WebSocket
        try:
            from run import socketio
            socketio.emit('chat_response', {
                'text': response.get('text', ''),
                'sources': response.get('sources', []),
                'timestamp': response.get('timestamp')
            })
        except Exception as e:
            logger.error(f"Failed to emit chat response: {str(e)}")
        
        return jsonify({
            'query': message,
            'response': response.get('text', ''),
            'sources': response.get('sources', []),
            'timestamp': response.get('timestamp')
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': f'Chat failed: {str(e)}'}), 500
