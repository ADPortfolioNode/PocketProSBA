import os
import logging
import time
import json
import re
from functools import lru_cache

# Configure logging
logger = logging.getLogger(__name__)

# Global RAG manager instance
_rag_manager_instance = None

# Import Gemini RAG service
try:
    from backend.gemini_rag_service import gemini_rag_service
    GEMINI_AVAILABLE = True
    logger.info("✅ Gemini RAG service imported successfully")
except ImportError as e:
    logger.warning(f"❌ Failed to import Gemini RAG service: {str(e)}")
    GEMINI_AVAILABLE = False
    gemini_rag_service = None

class RAGManager:
    """
    Retrieval-Augmented Generation (RAG) Manager
    
    Coordinates document storage, retrieval, and generation for RAG workflows.
    """
    
    def __init__(self, chroma_service=None):
        """Initialize the RAG Manager"""
        self.chroma_service = chroma_service
        self.available = False
        
        # Initialize RAG system
        if chroma_service:
            self.available = self._initialize_rag_system()
    
    def _initialize_rag_system(self):
        """Initialize the RAG system"""
        try:
            # Check if ChromaDB service is available
            if not self.chroma_service.is_available():
                logger.error("ChromaDB service is not available")
                return False
            
            # Check if collections are initialized
            documents_stats = self.chroma_service.get_collection_stats("documents")
            
            if "error" in documents_stats:
                logger.error(f"Error getting documents collection stats: {documents_stats['error']}")
                return False
            
            logger.info(f"✅ RAG system initialized successfully")
            logger.info(f"✅ Documents collection: {documents_stats.get('count', 0)} documents")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ RAG system initialization failed: {str(e)}")
            return False
    
    def is_available(self):
        """Check if RAG system is available"""
        return self.available and self.chroma_service and self.chroma_service.is_available()
    
    def add_document(self, text, metadata=None):
        """Add a document to the RAG system"""
        if not self.is_available():
            return {"error": "RAG system not available"}
        
        try:
            result = self.chroma_service.add_documents([text], [metadata or {}])
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to add document: {str(e)}")
            return {"error": str(e)}
    
    def query_documents(self, query_text, n_results=5):
        """Query documents for RAG"""
        if not self.is_available():
            return {"error": "RAG system not available"}
        
        try:
            results = self.chroma_service.query_documents(query_text, n_results=n_results)
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to query documents: {str(e)}")
            return {"error": str(e)}
    
    def get_collection_stats(self):
        """Get collection statistics"""
        if not self.is_available():
            return {"error": "RAG system not available"}
        
        try:
            return self.chroma_service.get_collection_stats("documents")
            
        except Exception as e:
            logger.error(f"❌ Failed to get collection stats: {str(e)}")
            return {"error": str(e)}

@lru_cache(maxsize=1)
def get_rag_manager():
    """Get the global RAG manager instance"""
    global _rag_manager_instance
    
    if _rag_manager_instance is None:
        try:
            from services.chroma_fixed import ChromaService
            
            # Initialize ChromaDB service
            chroma_host = os.environ.get('CHROMADB_HOST', 'localhost')
            chroma_port = int(os.environ.get('CHROMADB_PORT', 8000))
            
            logger.info(f"🔌 Connecting to ChromaDB at {chroma_host}:{chroma_port}")
            chroma_service = ChromaService(host=chroma_host, port=chroma_port)
            
            # Initialize RAG manager
            _rag_manager_instance = RAGManager(chroma_service=chroma_service)
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG manager: {str(e)}")
            _rag_manager_instance = RAGManager()
    
    return _rag_manager_instance
