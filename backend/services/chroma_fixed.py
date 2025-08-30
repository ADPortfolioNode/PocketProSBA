import os
import logging
import time
import uuid
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

class ChromaService:
    """Service for interacting with ChromaDB"""
    
    def __init__(self, host=None, port=None):
        # Read from environment variables or use defaults
        self.host = host or os.environ.get("CHROMADB_HOST", "localhost")
        self.port = port or int(os.environ.get("CHROMADB_PORT", "8000"))
        self.client = None
        self.embedding_function = None
        self.collections = {}
        self.initialized = False
        
        # Initialize ChromaDB client with HTTP client for remote connection
        self.initialize()
    
    def initialize(self):
        """Initialize ChromaDB client and embedding function"""
        try:
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=Settings(
                    chroma_client_auth_provider="chromadb.auth.token.TokenAuthClientProvider",
                    chroma_client_auth_credentials="admin",
                    anonymized_telemetry=False
                )
            )
            
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            
            self._initialize_collections()
            
            self.initialized = True
            logger.info(f"✅ ChromaDB initialized successfully at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"❌ ChromaDB initialization failed: {str(e)}")
            self.initialized = False
            return False
    
    def _initialize_collections(self):
        """Initialize standard collections"""
        try:
            self.collections["documents"] = self._get_or_create_collection("documents")
            self.collections["steps"] = self._get_or_create_collection("steps")
            logger.info(f"✅ ChromaDB collections initialized")
            return True
        except Exception as e:
            logger.error(f"❌ ChromaDB collections initialization failed: {str(e)}")
            return False
    
    def _get_or_create_collection(self, name):
        """Get or create a collection"""
        try:
            return self.client.get_or_create_collection(
                name=name,
                embedding_function=self.embedding_function,
                metadata={"description": f"Collection for {name}"}
            )
        except Exception as e:
            logger.error(f"❌ Failed to get or create collection {name}: {str(e)}")
            raise
    
    def is_available(self):
        """Check if ChromaDB is available"""
        if not self.initialized or not self.client:
            return False
        
        try:
            self.client.list_collections()
            return True
        except Exception as e:
            logger.error(f"❌ ChromaDB availability check failed: {str(e)}")
            return False
    
    def add_documents(self, texts, metadatas=None, ids=None):
        """Add documents to the documents collection"""
        if not self.initialized or "documents" not in self.collections:
            return {"error": "ChromaDB not initialized"}
        
        try:
            if not ids:
                ids = [str(uuid.uuid4()) for _ in range(len(texts))]
            
            self.collections["documents"].add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            return {
                "success": True,
                "count": len(texts),
                "ids": ids
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to add documents: {str(e)}")
            return {"error": str(e)}
    
    def query_documents(self, query_text, n_results=5):
        """Query documents collection"""
        if not self.initialized or "documents" not in self.collections:
            return {"error": "ChromaDB not initialized"}
        
        try:
            results = self.collections["documents"].query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to query documents: {str(e)}")
            return {"error": str(e)}
    
    def add_step(self, step_id, text, metadata=None):
        """Add a step to the steps collection"""
        if not self.initialized or "steps" not in self.collections:
            return {"error": "ChromaDB not initialized"}
        
        try:
            self.collections["steps"].add(
                documents=[text],
                metadatas=[metadata or {}],
                ids=[step_id]
            )
            
            return {
                "success": True,
                "id": step_id
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to add step: {str(e)}")
            return {"error": str(e)}
    
    def get_collection_stats(self, collection_name="documents"):
        """Get collection statistics"""
        if not self.initialized or collection_name not in self.collections:
            return {"error": f"Collection {collection_name} not initialized"}
        
        try:
            collection = self.collections[collection_name]
            count = collection.count()
            return {
                "name": collection_name,
                "count": count,
                "available": True
            }
        except Exception as e:
            logger.error(f"❌ Failed to get collection stats: {str(e)}")
            return {
                "name": collection_name,
                "count": 0,
                "available": False,
                "error": str(e)
            }
    
    def delete_document(self, doc_id):
        """Delete a document from the documents collection"""
        if not self.initialized or "documents" not in self.collections:
            return {"error": "ChromaDB not initialized"}
        
        try:
            self.collections["documents"].delete(ids=[doc_id])
            return {
                "success": True,
                "id": doc_id
            }
        except Exception as e:
            logger.error(f"❌ Failed to delete document: {str(e)}")
            return {"error": str(e)}
