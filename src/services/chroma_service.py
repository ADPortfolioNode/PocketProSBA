"""
ChromaDB service for vector storage and retrieval.
"""
import chromadb
from chromadb.utils import embedding_functions
import os
from typing import List, Dict, Any, Optional
from src.utils.config import config


class ChromaService:
    """Service for managing ChromaDB operations."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure one ChromaDB instance."""
        if cls._instance is None:
            cls._instance = super(ChromaService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize ChromaDB client and collection."""
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        # Initialize ChromaDB client (new approach for v0.4.22)
        chroma_host = config.CHROMA_HOST
        chroma_port = config.CHROMA_PORT
        
        try:
            # Check if we should use HTTP client (for containerized ChromaDB)
            if chroma_host != 'localhost' or config.FLASK_ENV == 'production':
                # Use HTTP client for containerized deployment
                print(f"Connecting to ChromaDB at {chroma_host}:{chroma_port}")
                # Use the new client initialization approach - no settings needed
                self.client = chromadb.HttpClient(
                    host=chroma_host, 
                    port=chroma_port
                )
            else:
                # Use persistent client for local development
                os.makedirs(config.CHROMA_DB_PATH, exist_ok=True)
                print(f"Using persistent ChromaDB at {config.CHROMA_DB_PATH}")
                self.client = chromadb.PersistentClient(path=config.CHROMA_DB_PATH)
                
            print("ChromaDB client initialized successfully")
        except Exception as e:
            print(f"Error initializing ChromaDB client: {e}")
            raise
        
        # Initialize embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=config.EMBEDDING_MODEL
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=config.CHROMA_COLLECTION_NAME
            )
        except Exception:
            self.collection = self.client.create_collection(
                name=config.CHROMA_COLLECTION_NAME
            )
        
        self._initialized = True
    
    def add_documents(self, 
                     documents: List[str], 
                     metadatas: List[Dict[str, Any]], 
                     ids: List[str]) -> bool:
        """Add documents to the collection."""
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            return True
        except Exception as e:
            print(f"Error adding documents to ChromaDB: {e}")
            return False
    
    def query_documents(self, 
                       query_text: str, 
                       n_results: int = None,
                       where: Optional[Dict] = None) -> Dict[str, Any]:
        """Query documents from the collection."""
        try:
            if n_results is None:
                n_results = config.DEFAULT_TOP_K
            
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where
            )
            
            return {
                "success": True,
                "results": results
            }
        except Exception as e:
            print(f"Error querying ChromaDB: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": {"documents": [[]], "metadatas": [[]], "distances": [[]]}
            }
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            count = self.collection.count()
            return {
                "success": True,
                "document_count": count,
                "collection_name": config.CHROMA_COLLECTION_NAME
            }
        except Exception as e:
            print(f"Error getting collection stats: {e}")
            return {
                "success": False,
                "error": str(e),
                "document_count": 0
            }
    
    def delete_documents(self, ids: List[str]) -> bool:
        """Delete documents from the collection."""
        try:
            self.collection.delete(ids=ids)
            return True
        except Exception as e:
            print(f"Error deleting documents from ChromaDB: {e}")
            return False
    
    def update_documents(self, 
                        ids: List[str], 
                        documents: List[str], 
                        metadatas: List[Dict[str, Any]]) -> bool:
        """Update existing documents in the collection."""
        try:
            self.collection.update(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            return True
        except Exception as e:
            print(f"Error updating documents in ChromaDB: {e}")
            return False


def get_chroma_service_instance() -> ChromaService:
    """Get singleton ChromaDB service instance."""
    return ChromaService()
