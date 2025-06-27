import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

"""
Tests for RAG workflows in WhiteLabelRAG
These tests verify that the different RAG strategies work correctly
"""
import pytest
from unittest.mock import patch, MagicMock
import numpy as np

from app.services.rag_manager import RAGManager, get_sba_service_instance
from app.services.chroma_service import get_chroma_service_instance

@pytest.fixture(autouse=True)
def reset_rag_manager_singleton():
    RAGManager._reset_instance()
    yield

class TestRAGWorkflows:
    """Test suite for RAG workflows"""
    
    @pytest.fixture
    def mock_chroma_service(self):
        """Mock the ChromaDB service"""
        mock_service = MagicMock()
        
        # Setup query results
        mock_service.query.return_value = {
            "results": [
                {
                    "text": "Climate change is affecting global temperatures.",
                    "metadata": {"source": "climate_doc.pdf", "page": 1}
                },
                {
                    "text": "Rising sea levels are a consequence of global warming.",
                    "metadata": {"source": "climate_doc.pdf", "page": 2}
                },
                {
                    "text": "Renewable energy can help mitigate climate change.",
                    "metadata": {"source": "energy_doc.pdf", "page": 5}
                }
            ]
        }
        
        return mock_service
    
    @pytest.fixture
    def mock_sba_service(self):
        """Mock the SBA (Sentence-BERT Agent) service"""
        mock_service = MagicMock()
        
        # Setup embedding function to return random vectors
        def mock_get_embeddings(text):
            # Return deterministic "random" embeddings based on text length
            np.random.seed(len(text))
            return np.random.rand(384)  # 384 dimensions for MiniLM
            
        mock_service.get_embeddings.side_effect = mock_get_embeddings
        
        return mock_service
    
    @pytest.fixture
    def mock_llm(self):
        """Mock the LLM"""
        mock_llm = MagicMock()
        
        # Setup generate_text to return a canned response
        mock_llm.generate_text.return_value = "This is a response about climate change and its effects."
        
        return mock_llm
    
    @patch('app.services.rag_manager.get_chroma_service_instance')
    @patch('app.services.rag_manager.get_sba_service_instance')
    @patch('app.services.rag_manager.LLMFactory')
    def test_basic_rag_workflow(self, mock_llm_factory, mock_get_sba, mock_get_chroma, 
                               mock_chroma_service, mock_sba_service, mock_llm):
        RAGManager._reset_instance()
        # Setup mocks
        mock_get_chroma.return_value = mock_chroma_service
        mock_get_sba.return_value = mock_sba_service
        mock_llm_factory.get_llm.return_value = mock_llm
        
        # Create RAG manager
        rag_manager = RAGManager()
        
        # Execute basic RAG workflow
        query = "Tell me about climate change"
        result = rag_manager.basic_rag_workflow(query)
        
        # Verify the workflow executed correctly
        assert mock_chroma_service.query.called
        assert mock_llm.generate_text.called
        assert isinstance(result, dict)
        assert "text" in result
        assert len(result["text"]) > 0
        assert "sources" in result
    
    @patch('app.services.rag_manager.get_chroma_service_instance')
    @patch('app.services.rag_manager.get_sba_service_instance')
    @patch('app.services.rag_manager.LLMFactory')
    def test_advanced_rag_workflow(self, mock_llm_factory, mock_get_sba, mock_get_chroma, 
                                 mock_chroma_service, mock_sba_service, mock_llm):
        RAGManager._reset_instance()
        # Setup mocks
        mock_get_chroma.return_value = mock_chroma_service
        mock_get_sba.return_value = mock_sba_service
        mock_llm_factory.get_llm.return_value = mock_llm
        
        # Create RAG manager
        rag_manager = RAGManager()
        
        # Execute advanced RAG workflow
        query = "What are the consequences of climate change?"
        result = rag_manager.advanced_rag_workflow(query)
        
        # Verify the workflow executed correctly
        assert mock_chroma_service.query.called
        assert mock_llm.generate_text.called
        assert isinstance(result, dict)
        assert "text" in result
        assert len(result["text"]) > 0
        assert "sources" in result
    
    @patch('app.services.rag_manager.get_chroma_service_instance')
    @patch('app.services.rag_manager.get_sba_service_instance')
    @patch('app.services.rag_manager.LLMFactory')
    def test_recursive_rag_workflow(self, mock_llm_factory, mock_get_sba, mock_get_chroma, 
                                  mock_chroma_service, mock_sba_service, mock_llm):
        RAGManager._reset_instance()
        # Setup mocks
        mock_get_chroma.return_value = mock_chroma_service
        mock_get_sba.return_value = mock_sba_service
        mock_llm_factory.get_llm.return_value = mock_llm
        
        # For recursive RAG, we need the LLM to "plan" the response
        mock_llm.generate_text.side_effect = [
            # First call: Planning response
            """{
                "components": [
                    {"id": "1", "title": "Temperature increase", "search_query": "climate change temperature"},
                    {"id": "2", "title": "Sea level rise", "search_query": "climate change sea level"},
                    {"id": "3", "title": "Mitigation", "search_query": "climate change mitigation"}
                ]
            }""",
            # Second call: Final response
            "Climate change causes rising temperatures, sea level rise, and can be mitigated with renewable energy."
        ]
        
        # Create RAG manager
        rag_manager = RAGManager()
        
        # Execute recursive RAG workflow
        query = "Explain climate change causes, effects, and solutions"
        result = rag_manager.recursive_rag_workflow(query)
        
        # Verify the workflow executed correctly
        assert mock_chroma_service.query.call_count >= 3  # At least one per component
        assert mock_llm.generate_text.call_count >= 2  # At least once for planning, once for final
        assert isinstance(result, dict)
        assert "text" in result
        assert len(result["text"]) > 0
        assert "sources" in result
    
    @patch('app.services.rag_manager.get_chroma_service_instance')
    @patch('app.services.rag_manager.get_sba_service_instance')
    @patch('app.services.rag_manager.LLMFactory')
    def test_adaptive_rag_workflow(self, mock_llm_factory, mock_get_sba, mock_get_chroma, 
                                 mock_chroma_service, mock_sba_service, mock_llm):
        RAGManager._reset_instance()
        # Setup mocks
        mock_get_chroma.return_value = mock_chroma_service
        mock_get_sba.return_value = mock_sba_service
        mock_llm_factory.get_llm.return_value = mock_llm
        
        # For adaptive RAG, we need the LLM to analyze the query
        mock_llm.generate_text.side_effect = [
            # First call: Query analysis
            """{
                "analysis": {
                    "complexity": "high",
                    "query_type": "multi_part",
                    "suggested_workflow": "recursive"
                }
            }""",
            # Second call: Final response
            "Climate change is a complex issue with multiple facets."
        ]
        
        # Create RAG manager
        rag_manager = RAGManager()
        
        # Execute adaptive RAG workflow
        query = "Compare climate change causes, effects on sea levels, and renewable energy solutions"
        result = rag_manager.adaptive_rag_workflow(query)
        
        # Verify the workflow executed correctly
        assert mock_llm.generate_text.call_count >= 2  # At least once for analysis, once for final
        assert isinstance(result, dict)
        assert "text" in result
        assert len(result["text"]) > 0
        assert "sources" in result
        assert "workflow" in result  # Should indicate which workflow was chosen
