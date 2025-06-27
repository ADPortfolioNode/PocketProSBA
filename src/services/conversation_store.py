"""
Conversation store for managing user sessions and conversation history.
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from src.utils.config import config


class ConversationStore:
    """In-memory conversation store with optional Redis backend."""
    
    def __init__(self):
        self.conversations = {}  # In-memory fallback
        self.max_conversation_length = 20  # Maximum messages per conversation
        self.session_timeout = timedelta(hours=24)  # Session timeout
        
        # Try to initialize Redis if configured
        self.redis_client = None
        if config.USE_REDIS:
            try:
                import redis
                self.redis_client = redis.from_url(config.REDIS_URL)
                self.redis_client.ping()  # Test connection
                print("Connected to Redis for session storage")
            except Exception as e:
                print(f"Could not connect to Redis: {e}. Using in-memory storage.")
                self.redis_client = None
    
    def get_conversation(self, session_id: str) -> 'Conversation':
        """Get or create conversation for session."""
        if self.redis_client:
            return self._get_conversation_redis(session_id)
        else:
            return self._get_conversation_memory(session_id)
    
    def _get_conversation_redis(self, session_id: str) -> 'Conversation':
        """Get conversation from Redis."""
        try:
            data = self.redis_client.get(f"conversation:{session_id}")
            if data:
                conversation_data = json.loads(data)
                conversation = Conversation(session_id, self)
                conversation.messages = conversation_data.get("messages", [])
                conversation.user_info = conversation_data.get("user_info", {})
                conversation.conversation_state = conversation_data.get("conversation_state", "active")
                conversation.last_activity = datetime.fromisoformat(
                    conversation_data.get("last_activity", datetime.now().isoformat())
                )
                return conversation
        except Exception as e:
            print(f"Error loading conversation from Redis: {e}")
        
        # Fallback to new conversation
        return Conversation(session_id, self)
    
    def _get_conversation_memory(self, session_id: str) -> 'Conversation':
        """Get conversation from memory."""
        if session_id not in self.conversations:
            self.conversations[session_id] = Conversation(session_id, self)
        
        conversation = self.conversations[session_id]
        
        # Check if conversation has expired
        if datetime.now() - conversation.last_activity > self.session_timeout:
            # Reset expired conversation
            conversation = Conversation(session_id, self)
            self.conversations[session_id] = conversation
        
        return conversation
    
    def save_conversation(self, conversation: 'Conversation'):
        """Save conversation to storage."""
        if self.redis_client:
            self._save_conversation_redis(conversation)
        else:
            self._save_conversation_memory(conversation)
    
    def _save_conversation_redis(self, conversation: 'Conversation'):
        """Save conversation to Redis."""
        try:
            conversation_data = {
                "messages": conversation.messages,
                "user_info": conversation.user_info,
                "conversation_state": conversation.conversation_state,
                "last_activity": conversation.last_activity.isoformat()
            }
            
            self.redis_client.setex(
                f"conversation:{conversation.session_id}",
                timedelta(hours=24),  # TTL
                json.dumps(conversation_data)
            )
        except Exception as e:
            print(f"Error saving conversation to Redis: {e}")
    
    def _save_conversation_memory(self, conversation: 'Conversation'):
        """Save conversation to memory (already saved by reference)."""
        pass  # In-memory conversations are already saved by reference


class Conversation:
    """Individual conversation instance."""
    
    def __init__(self, session_id: str, store: ConversationStore):
        self.session_id = session_id
        self.store = store
        self.messages: List[Dict[str, Any]] = []
        self.user_info: Dict[str, Any] = {}
        self.conversation_state = "active"
        self.last_activity = datetime.now()
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add message to conversation."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.messages.append(message)
        self.last_activity = datetime.now()
        
        # Trim conversation if too long
        if len(self.messages) > self.store.max_conversation_length:
            self.messages = self.messages[-self.store.max_conversation_length:]
        
        # Save to store
        self.store.save_conversation(self)
    
    def get_recent_messages(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages from conversation."""
        return self.messages[-count:] if count > 0 else self.messages
    
    def get_context_string(self, max_messages: int = 8) -> str:
        """Get conversation context as formatted string."""
        recent_messages = self.get_recent_messages(max_messages)
        
        context_parts = []
        for msg in recent_messages:
            role = msg["role"].upper()
            content = msg["content"]
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    def clear(self):
        """Clear conversation history."""
        self.messages = []
        self.conversation_state = "active"
        self.last_activity = datetime.now()
        self.store.save_conversation(self)


# Global conversation store instance
_conversation_store_instance = None

def get_conversation_store() -> ConversationStore:
    """Get singleton conversation store instance."""
    global _conversation_store_instance
    if _conversation_store_instance is None:
        _conversation_store_instance = ConversationStore()
    return _conversation_store_instance


def get_current_session_id() -> str:
    """Get current session ID (simplified for this implementation)."""
    # In a real implementation, this would come from Flask session or JWT token
    # For now, we'll use a simple approach
    try:
        from flask import session, request
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        return session['session_id']
    except:
        # Fallback for testing or non-Flask contexts
        return "default_session"
