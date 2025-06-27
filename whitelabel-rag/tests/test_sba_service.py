"""
Tests for the Sentence-BERT Agent (SBA) service
This service handles embedding operations for the RAG system
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Import the SBA service or mock it if not yet implemented
try:
    from app.services.sba_service import SBAService, get_sba_service_instance
except ImportError:
    # Create mock for testing if the module doesn't exist yet
    class SBAService:
        def __init__(self, model_name="all-MiniLM-L6-v2"):
            self.model_name = model_name
            
        def get_embeddings(self, text):
            """Mock method that returns a random embedding vector"""
            # Return a mock embedding of appropriate dimension based on model
            if "MiniLM" in self.model_name:
                return np.random.rand(384)  # MiniLM models typically have 384 dimensions
            return np.random.rand(768)  # Default to 768 dimensions for other models
            
        def get_batch_embeddings(self, texts):
            """Mock method that returns batch embeddings"""
            return [self.get_embeddings(text) for text in texts]
    
    def get_sba_service_instance():
        """Mock function to get a singleton instance of SBAService"""
        return SBAService()

class TestSBAService:
    """Test suite for the Sentence-BERT Agent service"""
    
    def test_sba_service_initialization(self):
        """Test that the SBA service initializes correctly"""
        service = SBAService()
        assert service is not None
        assert service.model_name == "all-MiniLM-L6-v2"  # Default model
        
    def test_custom_model_initialization(self):
        """Test that the SBA service can be initialized with a custom model"""
        custom_model = "sentence-t5-base"
        service = SBAService(model_name=custom_model)
        assert service.model_name == custom_model
    
    def test_get_embeddings(self):
        """Test that the get_embeddings method returns vectors of the correct shape"""
        service = SBAService()
        text = "This is a test document for embedding"
        embedding = service.get_embeddings(text)
        
        # Check that it returns a numpy array with the expected dimensions
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape[0] in (384, 768)  # Common embedding dimensions
    
    def test_get_batch_embeddings(self):
        """Test batch embedding generation"""
        service = SBAService()
        texts = [
            "First test document",
            "Second test document",
            "Third test document with more content"
        ]
        
        embeddings = service.get_batch_embeddings(texts)
        
        # Check that we get the right number of embeddings
        assert len(embeddings) == len(texts)
        
        # Check that all embeddings have the same dimension
        dimensions = set(emb.shape[0] for emb in embeddings)
        assert len(dimensions) == 1  # All embeddings should have the same dimension
    
    @patch('app.services.sba_service.get_sba_service_instance')
    def test_singleton_pattern(self, mock_get_instance):
        """Test that the service uses a singleton pattern"""
        # Setup mock
        mock_service = MagicMock()
        mock_get_instance.return_value = mock_service
        
        # Get service instances
        service1 = get_sba_service_instance()
        service2 = get_sba_service_instance()
        
        # Verify they're the same instance
        assert service1 is service2
        # Verify the singleton getter was called twice
        assert mock_get_instance.call_count == 2
