# routes/chat.py
from flask import Blueprint, request, jsonify
import logging
from backend.services.chat_processing_service import (
    process_chat_message,
    get_conversation_history,
    clear_conversation,
    get_concierge,
)

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

        # Prebuilt App.js (source map line ~127) posts {message, session_id}
        # without user_id — default for anonymous/dev clients to avoid UX hard-fail.
        user_id = data.get('user_id') or data.get('userId') or 1
        # Accept common aliases used by older clients
        message = data.get('message') or data.get('query') or data.get('text') or data.get('input')
        session_id = data.get('session_id') or data.get('sessionId')

        if not message or not str(message).strip():
            logger.warning("Message content is required for chat message")
            return jsonify({'error': 'Message content is required'}), 400

        # Process the message with Concierge assistant (soft-degrade if slow/unavailable)
        try:
            response = process_chat_message(user_id, str(message).strip(), session_id)
        except Exception as proc_err:
            logger.warning("Chat processing soft-fail: %s", proc_err)
            msg = str(message).strip()
            try:
                from backend.services.link_enrichment import enrich_answer_with_links

                degraded_text = enrich_answer_with_links(
                    "I'm your SBA assistant (degraded mode). "
                    f"You asked: “{msg[:240]}”. "
                    "Chat AI is temporarily limited — use the links below to open live SBA resources.",
                    [
                        {'title': 'SBA Loans', 'path': '/api/sba/content/loans'},
                        {'title': 'Start a Business', 'path': '/api/sba/lifecycle/start'},
                    ],
                )
            except Exception:
                degraded_text = (
                    "I'm your SBA assistant (degraded mode).\n\n"
                    "## Links\n"
                    f"- [SBA Programs](/sba)\n"
                    f"- [Browse SBA Loans](/browse#r=%2Fapi%2Fsba%2Fcontent%2Floans&t=SBA%20Loans)\n"
                    f"- [SBA Loans (official)](https://www.sba.gov/funding-programs/loans)"
                )
            response = {
                'success': True,
                'degraded': True,
                'session_id': session_id or 'default',
                'response': degraded_text,
                'answer': degraded_text,
                'message': degraded_text,
                'sources': [
                    {'title': 'SBA Loans', 'path': '/api/sba/content/loans', 'url': 'https://www.sba.gov/funding-programs/loans'},
                    {'title': 'Start a Business', 'path': '/api/sba/lifecycle/start'},
                ],
            }

        if not isinstance(response, dict):
            response = {'success': True, 'response': str(response), 'session_id': session_id or 'default'}
        response.setdefault('success', True)
        response.setdefault('session_id', session_id or 'default')
        # Normalize text fields + ensure clickable markdown links
        try:
            from backend.services.link_enrichment import enrich_answer_with_links

            body = (
                response.get('response')
                or response.get('answer')
                or response.get('message')
                or response.get('text')
                or ''
            )
            body = enrich_answer_with_links(str(body), response.get('sources') or [])
            response['response'] = body
            response['answer'] = body
            response['message'] = body
        except Exception as link_err:
            logger.debug('chat link normalize soft-fail: %s', link_err)
        # Return the processed response
        return jsonify(response), 200 if response.get('success', True) else 500

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        # Soft-degrade: never hard-fail the SPA chat surface
        try:
            from backend.services.link_enrichment import enrich_answer_with_links

            soft = enrich_answer_with_links(
                "Chat is temporarily unavailable. Open SBA resources with the links below.",
                [],
            )
        except Exception:
            soft = (
                "Chat is temporarily unavailable.\n\n"
                "## Links\n"
                "- [SBA Programs](/sba)\n"
                "- [Browse SBA Loans](/browse#r=%2Fapi%2Fsba%2Fcontent%2Floans&t=SBA%20Loans)\n"
                "- [SBA.gov Loans](https://www.sba.gov/funding-programs/loans)"
            )
        return jsonify({
            'success': True,
            'degraded': True,
            'error': 'Internal server error',
            'message': soft,
            'response': soft,
            'answer': soft,
            'session_id': (request.get_json(silent=True) or {}).get('session_id') or 'default',
        }), 200

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
