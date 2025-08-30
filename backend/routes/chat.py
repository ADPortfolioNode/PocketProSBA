# routes/chat.py
from flask import Blueprint, request, jsonify
import logging
from services.chat_processing_service import process_chat_message, get_conversation_history, clear_conversation

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__)

@chat_bp.route('', methods=['POST'])
def post_message():
    """
    Process a chat message using the Concierge assistant
    
    Expected JSON payload:
    {
        "user_id": 1,
        "message": "Hello, how can I get an SBA loan?",
        "session_id": "optional-session-id"  # For conversation continuity
    }
    """
    try:
        data = request.get_json()
        if not data:
            logger.warning("No JSON data provided for chat message")
            return jsonify({'error': 'No JSON data provided'}), 400

        user_id = data.get('user_id')
        message = data.get('message')
        session_id = data.get('session_id')

        if not user_id:
            logger.warning("User ID is required for chat message")
            return jsonify({'error': 'User ID is required'}), 400
            
        if not message or not message.strip():
            logger.warning("Message content is required for chat message")
            return jsonify({'error': 'Message content is required'}), 400

        # Process the message with Concierge assistant
        response = process_chat_message(user_id, message.strip(), session_id)
        
        # Return the processed response
        return jsonify(response), 200 if response.get('success', True) else 500

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to process chat message'
        }), 500

@chat_bp.route('/history/<session_id>', methods=['GET'])
def get_conversation(session_id):
    """
    Get conversation history for a session
    
    Args:
        session_id: Conversation session identifier
    """
    try:
        history = get_conversation_history(session_id)
        return jsonify({
            'session_id': session_id,
            'messages': history,
            'count': len(history)
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve conversation history',
            'session_id': session_id
        }), 500

@chat_bp.route('/clear/<session_id>', methods=['POST'])
def clear_conversation_endpoint(session_id):
    """
    Clear conversation history for a session
    
    Args:
        session_id: Conversation session identifier
    """
    try:
        success = clear_conversation(session_id)
        return jsonify({
            'success': success,
            'session_id': session_id,
            'message': 'Conversation cleared successfully' if success else 'Session not found'
        }), 200 if success else 404
        
    except Exception as e:
        logger.error(f"Error clearing conversation: {str(e)}")
        return jsonify({
            'error': 'Failed to clear conversation',
            'session_id': session_id
        }), 500

@chat_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for chat service"""
    try:
        from services.chat_processing_service import get_concierge
        concierge = get_concierge()
        return jsonify({
            'status': 'healthy',
            'service': 'chat',
            'concierge_initialized': concierge is not None,
            'active_sessions': len(concierge.conversation_store) if concierge else 0
        }), 200
    except Exception as e:
        logger.error(f"Chat health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'chat',
            'error': str(e)
        }), 500
