import os
import logging
import time
import json
from datetime import datetime
from flask_socketio import emit

# Configure logging
logger = logging.getLogger(__name__)


from .search_module import SearchModule

class BaseAssistant:
    """Base class for all assistants in the system, with optional search capabilities."""
    def __init__(self, name, enable_search=True):
        self.name = name
        self.status = "idle"
        self.progress = 0
        self.details = "Initialized"
        self.search_module = None
        
        if enable_search:
            try:
                self.search_module = SearchModule()
            except ValueError as e:
                logger.warning(f"Search module disabled: {e}")
                self.search_module = None
            except Exception as e:
                logger.error(f"Failed to initialize search module: {e}")
                self.search_module = None

    def search(self, query, num_results=5):
        if self.search_module:
            return self.search_module.search(query, num_results=num_results)
        raise NotImplementedError("Search capability not enabled for this assistant.")

    def _update_status(self, status, progress, details):
        self.status = status
        self.progress = progress
        self.details = details
        try:
            # Try to import socketio from app (works when app is running)
            from app import socketio
            socketio.emit('assistant_status', {
                'assistant': self.name,
                'status': status,
                'progress': progress,
                'details': details,
                'timestamp': datetime.now().isoformat()
            })
            logger.debug(f"Status update emitted for {self.name}: {status} ({progress}%)")
        except ImportError:
            # SocketIO not available (normal during testing)
            logger.debug(f"Status update: {self.name} - {status} ({progress}%) - {details}")
        except Exception as e:
            logger.warning(f"Failed to emit status update: {str(e)}")
    
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
