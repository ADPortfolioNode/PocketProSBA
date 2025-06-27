"""
Tests for the configuration module
"""
import pytest
import os
from unittest.mock import patch

class TestConfig:
    """Tests for configuration loading and handling"""
    
    def test_environment_variables(self):
        """Test that environment variables are properly loaded"""
        assert os.environ.get('GEMINI_API_KEY') is not None
    
    def test_app_directories_exist(self):
        """Test that required directories exist"""
        assert os.path.exists('uploads')
        assert os.path.exists('chromadb_data')
        assert os.path.exists('logs')
    
    @patch.dict(os.environ, {"CHROMA_DB_PATH": "test_chromadb_data"})
    def test_config_override(self):
        """Test that environment variables can override defaults"""
        from app.services.chroma_service import ChromaService
        
        service = ChromaService()
        assert service.persist_directory == "test_chromadb_data"
    
    def test_default_config(self):
        """Test default configuration values"""
        from app.services.chroma_service import ChromaService
        
        service = ChromaService()
        assert service.persist_directory == os.environ.get('CHROMA_DB_PATH', 'chromadb_data')
