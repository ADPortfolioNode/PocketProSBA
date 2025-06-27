"""
Tests for the FunctionAgent
"""
import pytest
from unittest.mock import patch, MagicMock

try:
    from app.services.function_agent import FunctionAgent
except ImportError as e:
    pytest.skip(f"Could not import app.services.function_agent: {e}")

class TestFunctionAgent:
    """Tests for the FunctionAgent"""
    
    def test_initialization(self):
        """Test basic initialization of FunctionAgent."""
        with patch('app.services.function_agent.LLMFactory') as mock_llm_factory:
            with patch('app.services.function_agent.AVAILABLE_FUNCTIONS', {"test_func": lambda: "test"}):
                function_agent = FunctionAgent()
                
                assert function_agent.name == "FunctionAgent"
                assert hasattr(function_agent, "llm")
                assert hasattr(function_agent, "available_functions")
    
    @patch('app.services.function_agent.LLMFactory')
    @patch('app.services.function_agent.AVAILABLE_FUNCTIONS', {"get_time": lambda: "12:00 PM"})
    def test_extract_function_call(self, mock_llm_factory):
        """Test _extract_function_call method."""
        # Setup mocks
        mock_llm = MagicMock()
        mock_llm_factory.get_llm.return_value = mock_llm
        
        # Create function agent
        function_agent = FunctionAgent()
        
        # Mock the LLM response to extract function
        mock_llm.generate_structured_output.return_value = {
            "name": "get_time",
            "parameters": {}
        }
        
        # Test extraction
        result = function_agent._extract_function_call("What time is it?")
        
        # Verify result
        assert result["name"] == "get_time"
        assert "parameters" in result
    
    @patch('app.services.function_agent.LLMFactory')
    @patch('app.services.function_agent.AVAILABLE_FUNCTIONS')
    def test_execute_function(self, mock_available_functions, mock_llm_factory):
        """Test _execute_function method."""
        # Setup mocks
        mock_available_functions.get.return_value = lambda: "12:00 PM"
        
        # Create function agent
        function_agent = FunctionAgent()
        
        # Test execution
        function_call = {"name": "get_time", "parameters": {}}
        result = function_agent._execute_function(function_call)
        
        # Verify result
        assert result == "12:00 PM"
        
        # Verify function was called
        mock_available_functions.get.assert_called_once_with("get_time")
    
    @patch('app.services.function_agent.LLMFactory')
    @patch('app.services.function_agent.AVAILABLE_FUNCTIONS', {"get_time": lambda: "12:00 PM"})
    def test_handle_message_success(self, mock_llm_factory):
        """Test handle_message with a valid function call."""
        # Setup mocks
        mock_llm = MagicMock()
        mock_llm_factory.get_llm.return_value = mock_llm
        
        # Create function agent
        function_agent = FunctionAgent()
        
        # Mock the extract function call method
        with patch.object(function_agent, '_extract_function_call') as mock_extract:
            mock_extract.return_value = {"name": "get_time", "parameters": {}}
            
            # Mock the execute function method
            with patch.object(function_agent, '_execute_function') as mock_execute:
                mock_execute.return_value = "12:00 PM"
                
                # Mock the report success method
                with patch.object(function_agent, 'report_success') as mock_success:
                    mock_success.return_value = {"text": "The current time is 12:00 PM"}
                    
                    # Test handle_message
                    result = function_agent.handle_message("What time is it?")
                    
                    # Verify extract function call was called
                    mock_extract.assert_called_once_with("What time is it?")
                    
                    # Verify execute function was called
                    mock_execute.assert_called_once_with({"name": "get_time", "parameters": {}})
                    
                    # Verify report success was called
                    mock_success.assert_called_once_with("12:00 PM")
                    
                    # Verify result
                    assert result["text"] == "The current time is 12:00 PM"
    
    @patch('app.services.function_agent.LLMFactory')
    @patch('app.services.function_agent.AVAILABLE_FUNCTIONS', {"get_time": lambda: "12:00 PM"})
    def test_handle_message_failure(self, mock_llm_factory):
        """Test handle_message with an invalid function call."""
        # Setup mocks
        mock_llm = MagicMock()
        mock_llm_factory.get_llm.return_value = mock_llm
        
        # Create function agent
        function_agent = FunctionAgent()
        
        # Mock the extract function call method to return None
        with patch.object(function_agent, '_extract_function_call', return_value=None):
            # Mock the report failure method
            with patch.object(function_agent, 'report_failure') as mock_failure:
                mock_failure.return_value = {"text": "No valid function call could be extracted from the request."}
                
                # Test handle_message
                result = function_agent.handle_message("Do something random")
                
                # Verify report failure was called
                mock_failure.assert_called_once()
                
                # Verify result
                assert "No valid function call" in result["text"]
    
    @patch('app.services.function_agent.LLMFactory')
    @patch('app.services.function_agent.AVAILABLE_FUNCTIONS', {"get_time": lambda: "12:00 PM"})
    def test_handle_message_unknown_function(self, mock_llm_factory):
        """Test handle_message with an unknown function."""
        # Setup mocks
        mock_llm = MagicMock()
        mock_llm_factory.get_llm.return_value = mock_llm
        
        # Create function agent
        function_agent = FunctionAgent()
        
        # Mock the extract function call method to return an unknown function
        with patch.object(function_agent, '_extract_function_call') as mock_extract:
            mock_extract.return_value = {"name": "unknown_function", "parameters": {}}
            
            # Mock the report failure method
            with patch.object(function_agent, 'report_failure') as mock_failure:
                mock_failure.return_value = {"text": "No valid function call could be extracted from the request."}
                
                # Test handle_message
                result = function_agent.handle_message("Call the unknown function")
                
                # Verify report failure was called
                mock_failure.assert_called_once()
