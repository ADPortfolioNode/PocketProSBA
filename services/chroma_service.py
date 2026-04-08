"""
ChromaDB service implementation for PocketPro SBA RAG system.
"""
print("Importing chroma_service")
import os
import time
import logging
from typing import Dict, List, Optional, Union, Any

# Lazy import chromadb components to avoid import-time failures when onnxruntime is unavailable.
QueryResult = Any
GetResult = Any
Settings = None
HttpClient = None
embedding_functions = None
chromadb = None
_GENAI_AVAILABLE = False

try:
    import google.generativeai as genai
    _GENAI_AVAILABLE = True
except Exception:
    genai = None

try:
    import chromadb
    from chromadb.api.types import QueryResult, GetResult
    from chromadb.config import Settings
    from chromadb import HttpClient
    from chromadb.utils import embedding_functions
except Exception as exc:
    chromadb = None
    Settings = None
    HttpClient = None
    embedding_functions = None
    _CHROMADB_IMPORT_ERROR = exc

try:
    from chromadb.utils.embedding_functions import GoogleGenerativeAIEmbeddingFunction
except Exception:
    # chromadb package may not include GoogleGenerativeAIEmbeddingFunction in older/newer releases.
    # Fall back to a simple local embedding implementation to keep the service running.
    GoogleGenerativeAIEmbeddingFunction = None
    try:
        from simple_vector_store import SimpleEmbeddingFunction
    except Exception:
        SimpleEmbeddingFunction = None

# from chromadb.api.models.Collection import Collection
try:
    from chromadb.errors import ChromaDBConnectionError, ChromaDBError, ChromaDBOperationError
except Exception:
    # Different chromadb versions expose different error names; provide safe aliases
    class ChromaDBConnectionError(Exception):
        pass

    class ChromaDBError(Exception):
        pass

    class ChromaDBOperationError(Exception):
        pass

print("ChromaDB imports completed")
# from utils.error_handling import (
#     with_error_handling,
#     rate_limit,
#     validate_input,
#     ChromaDBError as CustomChromaDBError,
#     ValidationError
# )

logger = logging.getLogger(__name__)

# Error mapping for ChromaDB operations
# CHROMA_ERROR_MAP = {
#     ChromaDBConnectionError: CustomChromaDBError,
#     ChromaDBError: CustomChromaDBError,
#     ValueError: ValidationError,
# }

class ChromaService:
    """ChromaDB service for document and step embeddings."""

    def __init__(self):
        """Initialize ChromaDB service with proper configuration."""
        self.host = os.environ.get('CHROMA_HOST', 'chromadb')
        self.port = int(os.environ.get('CHROMA_PORT', 8000))
        self.persist_directory = os.environ.get('CHROMA_PERSIST_DIR', '/chroma/chroma')
        
        # Configure ChromaDB client with optimized settings
        self.client = None
        max_retries = 10
        retry_delay = 5  # seconds

        if chromadb is not None and HttpClient is not None:
            try:
                self.client = HttpClient(host=self.host, port=self.port)
                self.client.heartbeat()
                logger.info("Successfully connected to ChromaDB")
            except Exception as e:
                logger.warning(f"Failed to connect to ChromaDB: {str(e)}")
                self.client = None
        else:
            logger.warning(f"Chromadb not available: {_CHROMADB_IMPORT_ERROR}")

        # Use Google's Generative AI embedding function when available, otherwise use a simple fallback
        if GoogleGenerativeAIEmbeddingFunction is not None:
            try:
                self.embedding_function = GoogleGenerativeAIEmbeddingFunction()
            except Exception:
                self.embedding_function = SimpleEmbeddingFunction() if SimpleEmbeddingFunction is not None else None
        else:
            self.embedding_function = SimpleEmbeddingFunction() if SimpleEmbeddingFunction is not None else None

        # Initialize collections if client is available
        if self.client:
            try:
                self._initialize_collections()
            except Exception as e:
                logger.warning(f"Failed to initialize collections: {str(e)}")
                self.docs_collection = None
                self.steps_collection = None

    def _initialize_collections(self) -> None:
        """Initialize required collections."""
        try:
            # Create or get collections
            self.docs_collection = self.client.get_or_create_collection(
                name="pocketpro_docs",
                metadata={"description": "Main document collection for PocketPro SBA"},
                embedding_function=self.embedding_function
            )
            
            self.steps_collection = self.client.get_or_create_collection(
                name="pocketpro_steps",
                metadata={"description": "Task execution steps collection"},
                embedding_function=self.embedding_function
            )
            
            logger.info("✅ ChromaDB collections initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB collections: {e}")
            raise

    # @with_error_handling(error_map=CHROMA_ERROR_MAP, max_retries=3)
    # @rate_limit(max_calls=50, time_window=60)  # 50 calls per minute
    def add_document(self, doc_id: str, text: str, metadata: dict = None) -> str:
        """
        Add a document to the ChromaDB store with retries and rate limiting.
        
        Args:
            doc_id: Unique identifier for the document
            text: Document content
            metadata: Optional document metadata
            
        Returns:
            Document ID if successful
            
        Raises:
            Exception: If ChromaDB operation fails
            ValueError: If input validation fails
        """
        # Input validation
        if not doc_id or not isinstance(doc_id, str):
            raise ValueError("Document ID must be a non-empty string")
        if not text or not isinstance(text, str):
            raise ValueError("Document text must be a non-empty string")
        if metadata is not None and not isinstance(metadata, dict):
            raise ValueError("Metadata must be a dictionary")

        # Check if ChromaDB is available
        if not self.client or not self.docs_collection:
            logger.warning("ChromaDB not available, document not actually stored")
            return doc_id

        # Add or update document
        self.docs_collection.upsert(
            ids=[doc_id],
            documents=[text],
            metadatas=[metadata or {}]
        )
        return doc_id

    # @with_error_handling(error_map=CHROMA_ERROR_MAP, max_retries=3)
    # @rate_limit(max_calls=100, time_window=60)  # 100 searches per minute
    def search_documents(self, query: str, n_results: int = 5) -> dict:
        """
        Search for similar documents with retries and rate limiting.
        
        Args:
            query: Search query text
            n_results: Number of results to return (max 20)
            
        Returns:
            Dictionary containing search results
            
        Raises:
            CustomChromaDBError: If ChromaDB operation fails
            ValidationError: If input validation fails
            RateLimitError: If rate limit is exceeded
        """
        # Input validation
        if not query or not isinstance(query, str):
            raise ValidationError("Query must be a non-empty string")
        if not isinstance(n_results, int) or n_results < 1:
            raise ValidationError("n_results must be a positive integer")
        # Limit maximum results
        n_results = min(n_results, 20)

        # Check if ChromaDB is available
        if not self.client or not self.docs_collection:
            logger.warning("ChromaDB not available, returning empty search results")
            return {"results": {"documents": [], "ids": [], "metadatas": [], "distances": []}}

        # Execute search
        results = self.docs_collection.query(
            query_texts=[query],
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        return results

    # @with_error_handling(error_map=CHROMA_ERROR_MAP, max_retries=3)
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the store with retries.
        
        Args:
            doc_id: ID of document to delete
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            CustomChromaDBError: If ChromaDB operation fails
            ValidationError: If input validation fails
        """
        # Input validation
        if not doc_id or not isinstance(doc_id, str):
            raise ValidationError("Document ID must be a non-empty string")

        self.docs_collection.delete(ids=[doc_id])
        return True

    # @with_error_handling(error_map=CHROMA_ERROR_MAP, max_retries=3)
    # @rate_limit(max_calls=100, time_window=60)  # 100 step operations per minute
    def store_step_embedding(self, step_id: str, text: str, metadata: dict = None) -> str:
        """
        Store a task execution step embedding with retries and rate limiting.
        
        Args:
            step_id: Unique identifier for the step
            text: Step content or description
            metadata: Optional step metadata
            
        Returns:
            Step ID if successful
            
        Raises:
            CustomChromaDBError: If ChromaDB operation fails
            ValidationError: If input validation fails
            RateLimitError: If rate limit is exceeded
        """
        # Input validation
        if not step_id or not isinstance(step_id, str):
            raise ValidationError("Step ID must be a non-empty string")
        if not text or not isinstance(text, str):
            raise ValidationError("Step text must be a non-empty string")
        if metadata is not None and not isinstance(metadata, dict):
            raise ValidationError("Metadata must be a dictionary")

        self.steps_collection.upsert(
            ids=[step_id],
            documents=[text],
            metadatas=[metadata or {}]
        )
        return step_id

    # @with_error_handling(error_map=CHROMA_ERROR_MAP, max_retries=3)
    # @rate_limit(max_calls=100, time_window=60)  # 100 searches per minute
    def search_similar_steps(self, query: str, n_results: int = 3) -> dict:
        """
        Search for similar task execution steps with retries and rate limiting.
        
        Args:
            query: Search query text
            n_results: Number of results to return (max 10)
            
        Returns:
            Dictionary containing search results
            
        Raises:
            CustomChromaDBError: If ChromaDB operation fails
            ValidationError: If input validation fails
            RateLimitError: If rate limit is exceeded
        """
        # Input validation
        if not query or not isinstance(query, str):
            raise ValidationError("Query must be a non-empty string")
        if not isinstance(n_results, int) or n_results < 1:
            raise ValidationError("n_results must be a positive integer")
        # Limit maximum results
        n_results = min(n_results, 10)

        results = self.steps_collection.query(
            query_texts=[query],
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        return results

    def get_collection_stats(self) -> dict:
        """Get statistics about the collections."""
        try:
            if not self.client or not self.docs_collection or not self.steps_collection:
                # Return mock stats if ChromaDB is not available
                return {
                    'total_documents': 0,
                    'total_steps': 0,
                    'collections': {
                        'documents': {
                            'name': 'pocketpro_docs',
                            'count': 0
                        },
                        'steps': {
                            'name': 'pocketpro_steps',
                            'count': 0
                        }
                    }
                }
            
            docs_count = self.docs_collection.count()
            steps_count = self.steps_collection.count()
            
            return {
                'total_documents': docs_count,
                'total_steps': steps_count,
                'collections': {
                    'documents': {
                        'name': 'pocketpro_docs',
                        'count': docs_count
                    },
                    'steps': {
                        'name': 'pocketpro_steps',
                        'count': steps_count
                    }
                }
            }
        except Exception as e:
            logger.error(f"❌ Failed to get collection stats: {e}")
            raise

    def health_check(self) -> dict:
        """Check the health of ChromaDB service."""
        try:
            # Perform a simple query to test functionality
            self.docs_collection.query(
                query_texts=["test"],
                n_results=1
            )
            
            stats = self.get_collection_stats()
            
            return {
                'status': 'healthy',
                'collections': stats['collections'],
                'connection': {
                    'host': self.host,
                    'port': self.port
                },
                'timestamp': int(time.time())
            }
        except Exception as e:
            logger.error(f"❌ ChromaDB health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': int(time.time())
            }

# Create a singleton instance
_instance = None

class MockChromaService:
    """Mock ChromaDB service for when ChromaDB is not available."""
    
    def __init__(self):
        self.available = False
    
    def search_documents(self, query: str, n_results: int = 5) -> dict:
        return {"results": {"documents": [[]], "ids": [[]], "metadatas": [[]], "distances": [[]]}}
    
    def add_document(self, doc_id: str, text: str, metadata: dict = None) -> str:
        """Mock add document method."""
        return doc_id
    
    def delete_document(self, doc_id: str) -> bool:
        return True
    
    def store_step_embedding(self, step_id: str, text: str, metadata: dict = None) -> str:
        return step_id
    
    def search_similar_steps(self, query: str, n_results: int = 3) -> dict:
        return {"results": {"documents": [], "ids": [], "metadatas": [], "distances": []}}
    
    def get_collection_stats(self) -> dict:
        """Get mock statistics about the collections."""
        return {
            'total_documents': 0,
            'total_steps': 0,
            'collections': {
                'documents': {
                    'name': 'pocketpro_docs',
                    'count': 0
                },
                'steps': {
                    'name': 'pocketpro_steps',
                    'count': 0
                }
            }
        }

def get_chroma_service() -> ChromaService:
    """Get or create ChromaService singleton instance."""
    global _instance
    if _instance is None:
        try:
            _instance = ChromaService()
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB service: {e}")
            # Return a mock service that indicates ChromaDB is not available
            _instance = MockChromaService()
    return _instance