import os
import logging
import time
import json
from datetime import datetime
from flask_socketio import emit

# Configure logging
logger = logging.getLogger(__name__)

class BaseAssistant:
    """Base class for all assistants in the system"""
    
    def __init__(self, name):
        """Initialize the assistant with a name"""
        self.name = name
        self.status = "idle"
        self.progress = 0
        self.details = "Initialized"
        
    def _update_status(self, status, progress, details):
        """Update the assistant's status and emit a WebSocket event"""
        self.status = status
        self.progress = progress
        self.details = details
        
        # Emit WebSocket event with status update
        try:
            from run import socketio
            socketio.emit('assistant_status', {
                'assistant': self.name,
                'status': status,
                'progress': progress,
                'details': details,
                'timestamp': datetime.now().isoformat()
            })
            logger.debug(f"Status update emitted for {self.name}: {status} ({progress}%)")
        except Exception as e:
            logger.error(f"Failed to emit status update: {str(e)}")
    
    def report_success(self, text, sources=None, additional_data=None):
        """Report successful task completion"""
        self._update_status("completed", 100, "Task completed successfully")
        
        result = {
            "text": text,
            "assistant": self.name,
            "timestamp": datetime.now().isoformat()
        }
        
        if sources:
            result["sources"] = sources
            
        if additional_data:
            result.update(additional_data)
            
        return result
    
    def report_failure(self, error_message):
        """Report task failure"""
        self._update_status("failed", 100, error_message)
        
        return {
            "text": error_message,
            "assistant": self.name,
            "timestamp": datetime.now().isoformat(),
            "error": True
        }
    
    def handle_message(self, message):
        """Handle a message (to be implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement handle_message")
