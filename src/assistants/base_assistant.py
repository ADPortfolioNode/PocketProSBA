"""
Base Assistant class providing common functionality for all assistant types.
"""
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import uuid


class BaseAssistant(ABC):
    """Base class for all assistant types in the WhiteLabelRAG system."""
    
    def __init__(self, name: str):
        self.name = name
        self.status = "idle"
        self.progress = 0
        self.details = "Initialized"
        self.assistant_id = str(uuid.uuid4())
        
    def _update_status(self, status: str, progress: int, details: str):
        """Update assistant status and emit WebSocket event."""
        self.status = status
        self.progress = progress
        self.details = details
        
        # Import here to avoid circular imports
        from flask_socketio import emit
        
        # Emit WebSocket event with status update
        try:
            emit('assistant_status_update', {
                'assistant_id': self.assistant_id,
                'name': self.name,
                'status': status,
                'progress': progress,
                'details': details
            })
        except Exception as e:
            print(f"Warning: Could not emit WebSocket event: {e}")
        
    def report_success(self, text: str, additional_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Report successful completion of task."""
        self._update_status("completed", 100, "Task completed successfully")
        result = {
            "text": text,
            "assistant": self.name,
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
        
        if additional_data:
            result.update(additional_data)
            
        return result
        
    def report_failure(self, error_message: str) -> Dict[str, Any]:
        """Report task failure."""
        self._update_status("failed", 100, error_message)
        return {
            "text": error_message,
            "assistant": self.name,
            "timestamp": datetime.now().isoformat(),
            "error": True,
            "success": False
        }
    
    @abstractmethod
    def handle_message(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Handle incoming message and return response.
        Must be implemented by all assistant subclasses.
        """
        pass
