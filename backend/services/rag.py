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
    
    def get_document_count(self):
        """Get document count"""
        if not self.initialized:
            return 0
        
        stats = self.chroma_service.get_collection_stats("documents")
        return stats.get("count", 0)
    
    def get_collection_stats(self):
        """Get collection statistics"""
        if not self.initialized:
            return {"documents": {"count": 0, "available": False}}
        
        return {
            "documents": self.chroma_service.get_collection_stats("documents"),
            "steps": self.chroma_service.get_collection_stats("steps")
        }
    
    def query_documents(self, query_text, top_k=5):
        """Query documents"""
        if not self.initialized:
            return []
        
        query_result = self.chroma_service.query_documents(
            query_text=query_text,
            n_results=top_k
        )
        
        if "error" in query_result:
            logger.error(f"❌ Document query failed: {query_result['error']}")
            return []
        
        # Format results
        formatted_results = []
        
        if query_result.get("documents") and query_result["documents"][0]:
            for i, doc in enumerate(query_result["documents"][0]):
                formatted_results.append({
                    "id": query_result["ids"][0][i],
                    "content": doc,
                    "metadata": query_result["metadatas"][0][i],
                    "distance": query_result["distances"][0][i],
                    "relevance_score": 1 - query_result["distances"][0][i]
                })
        
        return formatted_results
    
    def store_document(self, content, metadata=None):
        """Store document embedding"""
        if not self.initialized:
            return {"error": "RAG system not initialized"}
        
        doc_id = f"doc_{int(time.time() * 1000)}"
        
        if not metadata:
            metadata = {}
        
        # Add timestamp to metadata
        metadata.update({
            "added_at": int(time.time()),
            "content_length": len(content),
            "source": "api_upload"
        })
        
        add_result = self.chroma_service.add_documents(
            texts=[content],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        if "error" in add_result:
            logger.error(f"❌ Document storage failed: {add_result['error']}")
            return {"error": add_result["error"]}
        
        return {
            "success": True,
            "id": doc_id
        }
    
    def store_step_embedding(self, step_id, embedding, metadata=None):
        """Store step embedding"""
        if not self.initialized:
            return {"error": "RAG system not initialized"}
        
        if not metadata:
            metadata = {}
        
        # Add timestamp to metadata
        metadata.update({
            "added_at": int(time.time()),
            "type": "step_embedding"
        })
        
        # Convert embedding to text for storage
        text = f"Step: {metadata.get('description', 'No description')}"
        
        add_result = self.chroma_service.add_step(
            step_id=step_id,
            text=text,
            metadata=metadata
        )
        
        if "error" in add_result:
            logger.error(f"❌ Step embedding storage failed: {add_result['error']}")
            return {"error": add_result["error"]}
        
        return {
            "success": True,
            "id": step_id
        }
    
    def ingest_document(self, filepath):
        """Ingest document from file"""
        if not self.initialized:
            return {"error": "RAG system not initialized"}
        
        try:
            # Extract text from file
            text = self._extract_text_from_file(filepath)
            
            if not text:
                return {"error": "Failed to extract text from document"}
            
            # Generate document ID
            doc_id = f"doc_{os.path.basename(filepath)}_{int(time.time())}"
            
            # Create metadata
            metadata = {
                "source": os.path.basename(filepath),
                "filepath": filepath,
                "added_at": int(time.time()),
                "content_length": len(text)
            }
            
            # Chunk text
            chunks = self._chunk_text(text)
            
            # Store chunks
            chunk_ids = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_index": i,
                    "document_id": doc_id,
                    "total_chunks": len(chunks)
                })
                
                add_result = self.chroma_service.add_documents(
                    texts=[chunk],
                    metadatas=[chunk_metadata],
                    ids=[chunk_id]
                )
                
                if "error" in add_result:
                    logger.error(f"❌ Chunk storage failed: {add_result['error']}")
                else:
                    chunk_ids.append(chunk_id)
            
            return {
                "success": True,
                "document_id": doc_id,
                "chunks": len(chunk_ids),
                "chunk_ids": chunk_ids
            }
            
        except Exception as e:
            logger.error(f"❌ Document ingestion failed: {str(e)}")
            return {"error": str(e)}
    
    def _extract_text_from_file(self, filepath):
        """Extract text from file"""
        try:
            # Simple text extraction based on file extension
            _, ext = os.path.splitext(filepath)
            ext = ext.lower()
            
            if ext == '.txt':
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
            
            # Add support for other file types as needed
            # This is a simplified implementation
            
            return f"Text content from {filepath}"
            
        except Exception as e:
            logger.error(f"❌ Text extraction failed: {str(e)}")
            return None
    
    def _chunk_text(self, text, chunk_size=500, overlap=50):
        """Split text into chunks"""
        # Simple chunking by sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence.split())
            
            if current_size + sentence_size > chunk_size and current_chunk:
                # Store current chunk
                chunks.append(' '.join(current_chunk))
                
                # Keep overlap
                overlap_sentences = current_chunk[-3:] if len(current_chunk) > 3 else current_chunk
                current_chunk = overlap_sentences
                current_size = sum(len(s.split()) for s in overlap_sentences)
            
            current_chunk.append(sentence)
            current_size += sentence_size
        
        # Add the last chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
