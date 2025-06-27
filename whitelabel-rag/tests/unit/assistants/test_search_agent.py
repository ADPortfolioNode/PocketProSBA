"""
Tests for the SearchAgent
"""
import pytest
from unittest.mock import patch, MagicMock

try:
    from app.services.search_agent import SearchAgent
except ImportError as e:
    pytest.skip(f"Could not import app.services.search_agent: {e}")

class TestSearchAgent:
    """Tests for the SearchAgent"""
    
    def test_initialization(self):
        """Test basic initialization of SearchAgent."""
        with patch('app.services.search_agent.get_chroma_service_instance') as mock_chroma:
            with patch('app.services.search_agent.get_rag_manager') as mock_rag:
                with patch('app.services.search_agent.LLMFactory') as mock_llm_factory:
                    search_agent = SearchAgent()
                    
                    assert search_agent.name == "SearchAgent"
                    assert hasattr(search_agent, "chroma_service")
                    assert hasattr(search_agent, "rag_manager")
                    assert hasattr(search_agent, "llm")
    
    @patch('app.services.search_agent.get_chroma_service_instance')
    @patch('app.services.search_agent.get_rag_manager')
    @patch('app.services.search_agent.LLMFactory')
    def test_handle_message(self, mock_llm_factory, mock_rag, mock_chroma):
        """Test handle_message with a search query."""
        # Setup mocks
        mock_rag_instance = MagicMock()
        mock_rag.return_value = mock_rag_instance
        
        # Mock query results
        mock_results = {
            "results": [
                {"content": "Climate change info 1", "metadata": {"source": "doc1.pdf"}},
                {"content": "Climate change info 2", "metadata": {"source": "doc2.pdf"}}
            ]
        }
        mock_rag_instance.query_documents.return_value = mock_results
        
        # Collection stats
        mock_rag_instance.get_collection_stats.return_value = {
            "documents_count": 10,
            "steps_count": 5
        }
        
        # Create the search agent
        search_agent = SearchAgent()
        
        # Mock the _update_status method
        with patch.object(search_agent, '_update_status') as mock_update:
            # Mock the format results method
            with patch.object(search_agent, '_format_advanced_results') as mock_format:
                mock_format.return_value = "Formatted search results about climate change."
                
                # Test handle_message
                result = search_agent.handle_message("Find information about climate change")
                
                # Verify _update_status was called
                mock_update.assert_called()
                
                # Verify rag_manager.query_documents was called
                mock_rag_instance.query_documents.assert_called_once_with(
                    "Find information about climate change", n_results=5
                )
                
                # Verify results were formatted
                mock_format.assert_called_once_with(mock_results.get("results", []))
                
                # Verify result
                assert result["text"] == "Formatted search results about climate change."
                assert result["assistant"] == "SearchAgent"
    
    @patch('app.services.search_agent.get_chroma_service_instance')
    @patch('app.services.search_agent.get_rag_manager')
    @patch('app.services.search_agent.LLMFactory')
    def test_format_advanced_results(self, mock_llm_factory, mock_rag, mock_chroma):
        """Test _format_advanced_results method."""
        # Create the search agent
        search_agent = SearchAgent()
        
        # Test with empty results
        empty_result = search_agent._format_advanced_results([])
        assert "I couldn't find" in empty_result
        
        # Test with actual results
        results = [
            {"content": "Climate change info 1", "metadata": {"source": "doc1.pdf"}},
            {"content": "Climate change info 2", "metadata": {"source": "doc2.pdf"}}
        ]
        
        formatted_result = search_agent._format_advanced_results(results)
        
        # Result should include content from both documents
        assert "Climate change info 1" in formatted_result
        assert "Climate change info 2" in formatted_result
        
        # Result should include source attributions
        assert "doc1.pdf" in formatted_result
        assert "doc2.pdf" in formatted_result
