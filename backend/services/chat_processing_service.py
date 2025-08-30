"""
Chat Processing Service
Handles integration between chat routes and Concierge assistant
"""
import logging
import uuid
from datetime import datetime
from assistants.concierge import Concierge

logger = logging.getLogger(__name__)

# Global concierge instance for the application
_concierge_instance = None

def get_concierge():
    """Get or create the Concierge assistant instance"""
    global _concierge_instance
    if _concierge_instance is None:
        try:
            _concierge_instance = Concierge()
            logger.info("Concierge assistant initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Concierge assistant: {str(e)}")
            raise
    return _concierge_instance

def process_chat_message(user_id, message, session_id=None):
    """
    Process a chat message using the Concierge assistant
    
    Args:
        user_id: User identifier
        message: User message content
        session_id: Optional session ID for conversation continuity
    
    Returns:
        dict: Response containing assistant reply and metadata
    """
    try:
        concierge = get_concierge()
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"Created new session: {session_id}")
        
        # Process the message with Concierge assistant
        result = concierge.handle_message(message, session_id=session_id)
        
        # Format response for frontend
        response = {
            "success": result.get("success", True),
            "response": result.get("text", ""),
            "sources": result.get("sources", []),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "additional_data": result.get("additional_data", {})
        }
        
        logger.info(f"Processed message for session {session_id}: {len(message)} chars -> {len(response['response'])} chars response")
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        
        # Fallback response
        return {
            "success": False,
            "response": "I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
            "sources": [],
            "session_id": session_id or str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

def get_conversation_history(session_id):
    """
    Get conversation history for a session
    
    Args:
        session_id: Session identifier
    
    Returns:
        list: Conversation messages with metadata
    """
    try:
        concierge = get_concierge()
        
        if session_id in concierge.conversation_store:
            conversation = concierge.conversation_store[session_id]
            return conversation.get("messages", [])
        else:
            return []
            
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}")
        return []

def clear_conversation(session_id):
    """
    Clear conversation history for a session
    
    Args:
        session_id: Session identifier
    
    Returns:
        bool: Success status
    """
    try:
        concierge = get_concierge()
        
        if session_id in concierge.conversation_store:
            del concierge.conversation_store[session_id]
            logger.info(f"Cleared conversation for session: {session_id}")
            return True
        else:
            logger.warning(f"Session not found for clearing: {session_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error clearing conversation: {str(e)}")
        return False
