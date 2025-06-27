"""
Unit tests for the LLM factory
"""
import pytest
import os
from unittest.mock import patch, MagicMock

from app.services.llm_factory import LLMFactory

class TestLLMFactory:
    """Test the LLM factory module"""
    
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-api-key"})
    def test_get_llm_creates_gemini_model(self):
        """Test that get_llm creates a GeminiModel when API key is set"""
        with patch("app.services.llm_factory.genai") as mock_genai:
            # Configure the mock
            mock_genai.configure.return_value = None
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            # Call the method under test
            llm = LLMFactory.get_llm()
            
            # Assert the Gemini model was configured and created
            mock_genai.configure.assert_called_once_with(api_key="test-api-key")
            mock_genai.GenerativeModel.assert_called_once()
            assert llm is not None
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_llm_raises_error_without_api_key(self):
        """Test that get_llm raises an error when no API key is set"""
        with pytest.raises(ValueError) as excinfo:
            LLMFactory.get_llm()
        
        assert "GEMINI_API_KEY environment variable is required" in str(excinfo.value)
    
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-api-key", "GEMINI_MODEL": "custom-model"})
    def test_get_llm_uses_custom_model(self):
        """Test that get_llm uses a custom model name when specified"""
        with patch("app.services.llm_factory.genai") as mock_genai:
            # Configure the mock
            mock_genai.configure.return_value = None
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            # Call the method under test
            LLMFactory.get_llm()
            
            # Assert the correct model name was used
            mock_genai.GenerativeModel.assert_called_once_with(
                "custom-model", 
                generation_config=pytest.approx({})
            )
    
    @patch.dict(os.environ, {
        "GEMINI_API_KEY": "test-api-key", 
        "TEMPERATURE": "0.7",
        "TOP_P": "0.9",
        "TOP_K": "40",
        "MAX_OUTPUT_TOKENS": "1024"
    })
    def test_get_llm_uses_generation_config(self):
        """Test that get_llm uses generation config from environment variables"""
        with patch("app.services.llm_factory.genai") as mock_genai:
            # Configure the mock
            mock_genai.configure.return_value = None
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            
            # Call the method under test
            LLMFactory.get_llm()
            
            # Assert the correct generation config was used
            mock_genai.GenerativeModel.assert_called_once()
            
            # Get the actual generation_config passed to GenerativeModel
            _, kwargs = mock_genai.GenerativeModel.call_args
            generation_config = kwargs.get('generation_config', {})
            
            # Check that all config values were set correctly
            assert pytest.approx(0.7) == generation_config.get('temperature')
            assert pytest.approx(0.9) == generation_config.get('top_p')
            assert 40 == generation_config.get('top_k')
            assert 1024 == generation_config.get('max_output_tokens')
