"""
Conversation store for managing user sessions and conversation history.
"""
import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Configure logging
logger = logging.getLogger(__name__)

class ConversationStore:
    """Conversation store with Redis persistence for session management."""

    def __init__(self):
        self.conversations = {}  # In-memory fallback
        self.max_conversation_length = int(os.getenv("MAX_CONVERSATION_LENGTH", "50"))
        self.session_timeout_hours = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
        self.session_timeout = timedelta(hours=self.session_timeout_hours)

        # Try to initialize Redis
        self.redis_client = None
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        use_redis = os.getenv("USE_REDIS", "false").lower() == "true"

        if use_redis:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()  # Test connection
                logger.info("✅ Connected to Redis for conversation storage")
            except Exception as e:
                logger.warning(f"Could not connect to Redis: {e}. Using in-memory storage.")
                self.redis_client = None
        else:
            logger.info("Using in-memory conversation storage (Redis disabled)")

    def get_conversation(self, session_id: str) -> Dict[str, Any]:
        """Get or create conversation for session."""
        if self.redis_client:
            return self._get_conversation_redis(session_id)
        else:
            return self._get_conversation_memory(session_id)

    def _get_conversation_redis(self, session_id: str) -> Dict[str, Any]:
        """Get conversation from Redis."""
        try:
            data = self.redis_client.get(f"conversation:{session_id}")
            if data:
                conversation_data = json.loads(data)

                # Check if session has expired
                last_activity = datetime.fromisoformat(
                    conversation_data.get("last_activity", datetime.now().isoformat())
                )
                if datetime.now() - last_activity > self.session_timeout:
                    logger.info(f"Session {session_id} expired, creating new conversation")
                    return self._create_new_conversation(session_id)

                return conversation_data
            else:
                return self._create_new_conversation(session_id)

        except Exception as e:
            logger.error(f"Error retrieving conversation from Redis: {str(e)}")
            return self._get_conversation_memory(session_id)

    def _get_conversation_memory(self, session_id: str) -> Dict[str, Any]:
        """Get conversation from memory."""
        if session_id not in self.conversations:
            self.conversations[session_id] = self._create_new_conversation(session_id)
        return self.conversations[session_id]

    def _create_new_conversation(self, session_id: str) -> Dict[str, Any]:
        """Create a new conversation."""
        return {
            "session_id": session_id,
            "messages": [],
            "user_info": {},
            "conversation_state": "information_gathering",
            "last_activity": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "metadata": {
                "total_messages": 0,
                "assistant_interactions": 0,
                "last_assistant": None
            }
        }

    def save_conversation(self, session_id: str, conversation: Dict[str, Any]) -> bool:
        """Save conversation to storage."""
        try:
            # Update metadata
            conversation["last_activity"] = datetime.now().isoformat()
            conversation["metadata"]["total_messages"] = len(conversation.get("messages", []))

            if self.redis_client:
                return self._save_conversation_redis(session_id, conversation)
            else:
                return self._save_conversation_memory(session_id, conversation)

        except Exception as e:
            logger.error(f"Error saving conversation {session_id}: {str(e)}")
            return False

    def _save_conversation_redis(self, session_id: str, conversation: Dict[str, Any]) -> bool:
        """Save conversation to Redis."""
        try:
            # Set expiration based on session timeout
            expiration_seconds = int(self.session_timeout.total_seconds())

            data = json.dumps(conversation)
            result = self.redis_client.setex(
                f"conversation:{session_id}",
                expiration_seconds,
                data
            )
            return result is True

        except Exception as e:
            logger.error(f"Error saving to Redis: {str(e)}")
            return False

    def _save_conversation_memory(self, session_id: str, conversation: Dict[str, Any]) -> bool:
        """Save conversation to memory."""
        try:
            self.conversations[session_id] = conversation
            return True
        except Exception as e:
            logger.error(f"Error saving to memory: {str(e)}")
            return False

    def add_message(self, session_id: str, role: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """Add a message to the conversation."""
        try:
            conversation = self.get_conversation(session_id)

            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }

            conversation["messages"].append(message)

            # Maintain max conversation length
            if len(conversation["messages"]) > self.max_conversation_length:
                conversation["messages"] = conversation["messages"][-self.max_conversation_length:]

            # Update metadata
            if role == "assistant":
                conversation["metadata"]["assistant_interactions"] += 1
                conversation["metadata"]["last_assistant"] = metadata.get("assistant_type") if metadata else None

            return self.save_conversation(session_id, conversation)

        except Exception as e:
            logger.error(f"Error adding message to conversation {session_id}: {str(e)}")
            return False

    def get_recent_messages(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages from conversation."""
        try:
            conversation = self.get_conversation(session_id)
            messages = conversation.get("messages", [])
            return messages[-limit:] if messages else []
        except Exception as e:
            logger.error(f"Error getting recent messages for {session_id}: {str(e)}")
            return []

    def update_user_info(self, session_id: str, user_info: Dict[str, Any]) -> bool:
        """Update user information for the session."""
        try:
            conversation = self.get_conversation(session_id)
            conversation["user_info"].update(user_info)
            return self.save_conversation(session_id, conversation)
        except Exception as e:
            logger.error(f"Error updating user info for {session_id}: {str(e)}")
            return False

    def update_conversation_state(self, session_id: str, state: str) -> bool:
        """Update conversation state."""
        try:
            conversation = self.get_conversation(session_id)
            conversation["conversation_state"] = state
            return self.save_conversation(session_id, conversation)
        except Exception as e:
            logger.error(f"Error updating conversation state for {session_id}: {str(e)}")
            return False

    def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of the conversation."""
        try:
            conversation = self.get_conversation(session_id)
            messages = conversation.get("messages", [])

            return {
                "session_id": session_id,
                "total_messages": len(messages),
                "assistant_interactions": conversation.get("metadata", {}).get("assistant_interactions", 0),
                "conversation_state": conversation.get("conversation_state", "unknown"),
                "last_activity": conversation.get("last_activity"),
                "created_at": conversation.get("created_at"),
                "user_info": conversation.get("user_info", {}),
                "last_message": messages[-1] if messages else None
            }
        except Exception as e:
            logger.error(f"Error getting conversation summary for {session_id}: {str(e)}")
            return {"error": str(e)}

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions (Redis only)."""
        if not self.redis_client:
            # For in-memory, just return current count
            return len(self.conversations)

        try:
            # Redis handles expiration automatically, but we can count active sessions
            keys = self.redis_client.keys("conversation:*")
            return len(keys) if keys else 0
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {str(e)}")
            return 0

    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        try:
            if self.redis_client:
                keys = self.redis_client.keys("conversation:*")
                session_count = len(keys) if keys else 0
            else:
                session_count = len(self.conversations)

            return {
                "total_sessions": session_count,
                "storage_type": "redis" if self.redis_client else "memory",
                "max_conversation_length": self.max_conversation_length,
                "session_timeout_hours": self.session_timeout_hours
            }
        except Exception as e:
            logger.error(f"Error getting session stats: {str(e)}")
            return {"error": str(e)}


# Global conversation store instance
_conversation_store_instance = None

def get_conversation_store() -> ConversationStore:
    """Get the global conversation store instance."""
    global _conversation_store_instance
    if _conversation_store_instance is None:
        _conversation_store_instance = ConversationStore()
    return _conversation_store_instance

def get_current_session_id() -> str:
    """Generate a new session ID."""
    return str(uuid.uuid4())