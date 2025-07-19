"""
Tests for the RAG Manager which coordinates different RAG workflows
"""
import pytest
from unittest.mock import MagicMock, patch
import json
import os

# Import the module under test
from rag_manager import RAGManager, get_rag_manager

class TestRAGManager:
    """Tests for the RAG Manager component"""
    
    def test_initialization(self):
        """Test that the RAG Manager initializes correctly"""
        manager = RAGManager()
        assert manager is not None
        assert hasattr(manager, 'chroma_service')
    
    def test_get_singleton_instance(self):
        """Test that get_rag_manager returns a singleton instance"""
        manager1 = get_rag_manager()
        manager2 = get_rag_manager()
        assert manager1 is manager2
        
    @patch('app.services.rag_manager.get_chroma_service_instance')
    def test_query_documents_basic_rag(self, mock_get_chroma):
        """Test the basic RAG workflow"""
        # Setup mock
        mock_chroma = MagicMock()
        mock_get_chroma.return_value = mock_chroma
        
        # Mock chroma service query response
        mock_chroma.query.return_value = {
            "results": [
                {"text": "Document 1 content", "metadata": {"source": "doc1.pdf"}},
                {"text": "Document 2 content", "metadata": {"source": "doc2.pdf"}},
            ]
        }
        
        # Create test instance
        manager = RAGManager()
        
        # Call the method under test
        result = manager.query_documents(
            "test query", 
            workflow="basic",
            n_results=2
        )
        
        # Assert expected behavior
        assert result is not None
        assert "results" in result
        assert len(result["results"]) == 2
        
        # Verify chroma_service was called correctly
        mock_chroma.query.assert_called_once()
    
    @patch('app.services.rag_manager.get_chroma_service_instance')
    def test_query_documents_advanced_rag(self, mock_get_chroma):
        """Test the advanced RAG workflow"""
        # Setup mock
        mock_chroma = MagicMock()
        mock_get_chroma.return_value = mock_chroma
        
        # Mock chroma service query response
        mock_chroma.query.return_value = {
            "results": [
                {"text": "Document 1 content", "metadata": {"source": "doc1.pdf"}},
                {"text": "Document 2 content", "metadata": {"source": "doc2.pdf"}},
                {"text": "Document 3 content", "metadata": {"source": "doc3.pdf"}},
            ]
        }
        
        # Create test instance
        manager = RAGManager()
        
        # Call the method under test
        result = manager.query_documents(
            "test query", 
            workflow="advanced",
            n_results=3
        )
        
        # Assert expected behavior
        assert result is not None
        assert "results" in result
        assert len(result["results"]) == 3
        
        # Advanced RAG should do query expansion and reranking
        # which means multiple calls to the chroma service
        assert mock_chroma.query.call_count >= 1
    
    @patch('app.services.rag_manager.get_chroma_service_instance')
    def test_query_documents_recursive_rag(self, mock_get_chroma):
        """Test the recursive RAG workflow"""
        # Setup mock
        mock_chroma = MagicMock()
        mock_get_chroma.return_value = mock_chroma
        
        # Mock chroma service query response
        mock_chroma.query.return_value = {
            "results": [
                {"text": "Document 1 content", "metadata": {"source": "doc1.pdf"}},
                {"text": "Document 2 content", "metadata": {"source": "doc2.pdf"}},
            ]
        }
        
        # Create test instance
        manager = RAGManager()
        
        # Call the method under test
        result = manager.query_documents(
            "test query with multiple parts", 
            workflow="recursive",
            n_results=2
        )
        
        # Assert expected behavior
        assert result is not None
        assert "results" in result
        
        # Recursive RAG should make multiple queries for each subquery
        assert mock_chroma.query.call_count > 1
    
    @patch('app.services.rag_manager.get_chroma_service_instance')
    def test_query_documents_adaptive_rag(self, mock_get_chroma):
        """Test the adaptive RAG workflow that selects the best approach"""
        # Setup mock
        mock_chroma = MagicMock()
        mock_get_chroma.return_value = mock_chroma
        
        # Mock chroma service query response
        mock_chroma.query.return_value = {
            "results": [
                {"text": "Document 1 content", "metadata": {"source": "doc1.pdf"}},
                {"text": "Document 2 content", "metadata": {"source": "doc2.pdf"}},
            ]
        }
        
        # Create test instance
        manager = RAGManager()
        
        # Call the method under test
        result = manager.query_documents(
            "test query", 
            workflow="adaptive",
            n_results=2
        )
        
        # Assert expected behavior
        assert result is not None
        assert "results" in result
        assert "selected_workflow" in result  # Adaptive should tell us which workflow it selected
        
        # Adaptive RAG should analyze the query and select an appropriate workflow
        assert mock_chroma.query.call_count >= 1
    
    def test_invalid_workflow(self):
        """Test that an invalid workflow name raises an error"""
        manager = RAGManager()
        
        with pytest.raises(ValueError) as excinfo:
            manager.query_documents("test query", workflow="invalid_workflow")
        
        assert "Invalid RAG workflow" in str(excinfo.value)
