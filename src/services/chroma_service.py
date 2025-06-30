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
        
        self.client = None
        self.collection = None
        self.embedding_function = None
        self._chroma_available = False
        
        chroma_host = config.CHROMA_HOST
        chroma_port = config.CHROMA_PORT
        
        print(f"INFO: Attempting to connect to ChromaDB at http://{chroma_host}:{chroma_port}")

        try:
            # For ChromaDB >= 0.5.0, HttpClient is the standard way to connect to a remote server.
            # The host is determined by the CHROMA_HOST env var, which is 'chromadb' in docker-compose.
            self.client = chromadb.HttpClient(
                host=chroma_host,
                port=chroma_port,
                # Adding headers can sometimes help, though not strictly required by default.
                # headers={"Content-Type": "application/json"} 
            )
            
            # A more robust check than just heartbeat
            self.client.list_collections()
            print("INFO: ✓ ChromaDB connection successful. Client is functional.")
            self._chroma_available = True
            
        except Exception as e:
            print(f"ERROR: Failed to connect to ChromaDB: {e}")
            print("WARN: ChromaDB will not be available. Continuing without vector storage.")
            self.client = None
            self._chroma_available = False
        
        # Only initialize embedding function and collection if client is available
        if self.client is not None:
            try:
                # Get or create collection with conditional embedding
                collection_kwargs = {"name": config.CHROMA_COLLECTION_NAME}
                
                # Setup embedding function consistently
                self.embedding_function = None
                openai_api_key = os.getenv('OPENAI_API_KEY')
                
                try:
                    # First try to get existing collection
                    self.collection = self.client.get_collection(
                        name=config.CHROMA_COLLECTION_NAME
                    )
                    print(f"Retrieved existing collection '{config.CHROMA_COLLECTION_NAME}'")
                    
                    # Get the existing collection's embedding function for consistency
                    # Note: ChromaDB 0.5.15 doesn't expose embedding function details,
                    # so we'll use no custom embedding to ensure compatibility
                    print("Using collection's existing embedding configuration")
                    
                except Exception:
                    # Create new collection - only use OpenAI if available
                    collection_kwargs = {"name": config.CHROMA_COLLECTION_NAME}
                    
                    if openai_api_key:
                        print("OpenAI API key found - creating collection with OpenAI embeddings")
                        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                            api_key=openai_api_key,
                            model_name="text-embedding-ada-002"
                        )
                        collection_kwargs["embedding_function"] = self.embedding_function
                    else:
                        print("No OpenAI API key - creating collection with default embeddings")
                    
                    self.collection = self.client.create_collection(**collection_kwargs)
                    print(f"Created new collection '{config.CHROMA_COLLECTION_NAME}'")
                
                self._chroma_available = True
                print(f"ChromaDB collection '{config.CHROMA_COLLECTION_NAME}' ready")
                
            except Exception as e:
                print(f"Error setting up ChromaDB collection: {e}")
                self._chroma_available = False
        else:
            self._chroma_available = False
            self.collection = None
            self.embedding_function = None
        
        self._initialized = True
    
    def add_documents(self, 
                     documents: List[str], 
                     metadatas: List[Dict[str, Any]], 
                     ids: List[str]) -> Dict[str, Any]:
        """Add documents to the collection."""
        if not getattr(self, '_chroma_available', False) or self.collection is None:
            print("ChromaDB not available - skipping document addition")
            return {
                "success": False,
                "error": "ChromaDB not available or collection not initialized",
                "count": 0
            }
            
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"Successfully added {len(documents)} documents to ChromaDB")
            return {
                "success": True,
                "count": len(documents),
                "message": f"Added {len(documents)} documents"
            }
        except Exception as e:
            print(f"Error adding documents to ChromaDB: {e}")
            return {
                "success": False,
                "error": str(e),
                "count": 0
            }
    
    def query_documents(self, 
                       query_text: str, 
                       n_results: Optional[int] = None,
                       where: Optional[Dict] = None) -> Dict[str, Any]:
        """Query documents from the collection."""
        if not getattr(self, '_chroma_available', False) or self.collection is None:
            print("ChromaDB not available - returning empty results")
            return {
                "success": False,
                "error": "ChromaDB not available",
                "results": {"documents": [[]], "metadatas": [[]], "distances": [[]]}
            }
            
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
        if not getattr(self, '_chroma_available', False) or self.collection is None:
            return {
                "success": False,
                "error": "ChromaDB not available",
                "document_count": 0
            }
            
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
        if not getattr(self, '_chroma_available', False) or self.collection is None:
            print("ChromaDB not available - skipping document deletion")
            return False
            
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
        if not getattr(self, '_chroma_available', False) or self.collection is None:
            print("ChromaDB not available - skipping document update")
            return False
            
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
    
    def get_collection(self):
        """Get the ChromaDB collection."""
        if not getattr(self, '_chroma_available', False) or self.collection is None:
            raise RuntimeError("ChromaDB not available or collection not initialized")
        return self.collection
    
    def test_connection(self) -> Dict[str, Any]:
        """Test ChromaDB connection and return status."""
        try:
            if not hasattr(self, 'client') or self.client is None:
                return {
                    "success": False,
                    "error": "ChromaDB client not initialized",
                    "available": False
                }
            
            # Test heartbeat
            heartbeat = self.client.heartbeat()
            
            # Test collection access
            if hasattr(self, 'collection') and self.collection:
                collection_count = self.collection.count()
                return {
                    "success": True,
                    "available": True,
                    "heartbeat": heartbeat,
                    "collection_count": collection_count,
                    "collection_name": config.CHROMA_COLLECTION_NAME
                }
            else:
                return {
                    "success": True,
                    "available": True,
                    "heartbeat": heartbeat,
                    "collection_count": 0,
                    "collection_name": config.CHROMA_COLLECTION_NAME,
                    "note": "Collection not initialized"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "available": False
            }
    
    def _ensure_embedding_compatibility(self) -> bool:
        """
        Ensure embedding compatibility for existing collections.
        Returns True if embeddings are compatible, False otherwise.
        """
        if not self.collection:
            return False
            
        try:
            # For existing collections, we can't easily detect the embedding function
            # ChromaDB 0.5.15 doesn't expose this information directly
            # So we'll use a defensive approach: always use the collection as-is
            # and let ChromaDB handle embedding consistency internally
            
            # Test if we can perform basic operations
            current_count = self.collection.count()
            print(f"Collection has {current_count} documents, embeddings appear compatible")
            return True
            
        except Exception as e:
            print(f"Embedding compatibility check failed: {e}")
            return False
    
    def get_embedding_info(self) -> Dict[str, Any]:
        """Get information about the current embedding configuration."""
        return {
            "has_custom_embedding": self.embedding_function is not None,
            "embedding_type": "OpenAI" if self.embedding_function else "ChromaDB Default",
            "collection_exists": self.collection is not None,
            "compatible": self._ensure_embedding_compatibility()
        }


def get_chroma_service_instance() -> ChromaService:
    """Get singleton ChromaDB service instance."""
    return ChromaService()
