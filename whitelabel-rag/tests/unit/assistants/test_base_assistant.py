"""
Tests for the BaseAssistant class
"""
import pytest
from unittest.mock import patch, MagicMock

try:
    from app.services.base_assistant import BaseAssistant
except ImportError as e:
    pytest.skip(f"Could not import app.services.base_assistant: {e}")

class TestBaseAssistant:
    """Tests for BaseAssistant class"""
    
    def test_initialization(self):
        """Test basic initialization of BaseAssistant."""
        assistant = BaseAssistant("TestAssistant")
        assert assistant.name == "TestAssistant"
        assert assistant.status == "idle"
        assert assistant.progress == 0
        assert hasattr(assistant, "details")
    
    @patch('app.services.base_assistant.socketio')
    def test_update_status(self, mock_socketio):
        """Test that _update_status emits an event."""
        assistant = BaseAssistant("TestAssistant")
        assistant._update_status("running", 50, "Processing request")
        
        # Check status was updated
        assert assistant.status == "running"
        assert assistant.progress == 50
        assert assistant.details == "Processing request"
        
        # Check event was emitted
        mock_socketio.emit.assert_called_once()
        call_args = mock_socketio.emit.call_args[0]
        assert call_args[0] == 'assistant_status_update'
        assert 'name' in call_args[1]
        assert call_args[1]['name'] == 'TestAssistant'
        assert call_args[1]['status'] == 'running'
        assert call_args[1]['progress'] == 50
    
    def test_report_success(self):
        """Test report_success method."""
        with patch.object(BaseAssistant, '_update_status') as mock_update:
            assistant = BaseAssistant("TestAssistant")
            result = assistant.report_success("Test response", {"additional": "data"})
            
            # Check _update_status was called correctly
            mock_update.assert_called_once_with("completed", 100, "Task completed successfully")
            
            # Check result structure
            assert result["text"] == "Test response"
            assert result["assistant"] == "TestAssistant"
            assert "timestamp" in result
            assert result["additional"] == "data"
    
    def test_report_failure(self):
        """Test report_failure method."""
        with patch.object(BaseAssistant, '_update_status') as mock_update:
            assistant = BaseAssistant("TestAssistant")
            result = assistant.report_failure("Error message")
            
            # Check _update_status was called correctly
            mock_update.assert_called_once_with("failed", 100, "Error message")
            
            # Check result structure
            assert result["text"] == "Error message"
            assert result["assistant"] == "TestAssistant"
            assert "timestamp" in result
            assert result["error"] is True
