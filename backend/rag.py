import logging
from services.chroma import ChromaService
from gemini_rag_service import EnhancedGeminiRAGService

logger = logging.getLogger(__name__)

class RAGManager:
    """Manages the RAG system, including ChromaDB and Gemini RAG service."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RAGManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, chroma_service: ChromaService = None):
        if self._initialized:
            return

        self.chroma_service = chroma_service
        self.gemini_rag_service = EnhancedGeminiRAGService()
        self.is_ready = False
        self._initialized = True
        self.initialize_rag_system()

    def initialize_rag_system(self):
        logger.info("Initializing RAG system...")
        if not self.chroma_service:
            self.chroma_service = ChromaService()

        if not self.chroma_service.is_available():
            logger.error("ChromaDB service is not available. RAG system cannot be initialized.")
            self.is_ready = False
            return

        if not self.gemini_rag_service.initialize_full_service():
            logger.error("Gemini RAG service failed to initialize. RAG system cannot be initialized.")
            self.is_ready = False
            return

        self.is_ready = True
        logger.info("RAG system initialized successfully.")

    def is_available(self) -> bool:
        return self.is_ready and self.chroma_service.is_available() and self.gemini_rag_service.is_initialized

    def get_document_count(self) -> int:
        if self.is_available():
            return self.gemini_rag_service.get_service_status().get("document_count", 0)
        return 0

    def query_documents(self, query: str, n_results: int = 5):
        if not self.is_available():
            return {"error": "RAG system not available"}
        return self.gemini_rag_service.query_sba_loans(query)

    def get_collection_stats(self):
        if self.is_available():
            return self.chroma_service.get_collection_stats()
        return {"count": 0}

_rag_manager_instance = None

def get_rag_manager() -> RAGManager:
    global _rag_manager_instance
    if _rag_manager_instance is None:
        _rag_manager_instance = RAGManager()
    return _rag_manager_instance
