"""
Startup service for initializing the application and loading default content.
"""
import os
import hashlib
from typing import List, Dict, Any
from src.services.chroma_service import get_chroma_service_instance
from src.services.document_processor import DocumentProcessor
from src.services.model_discovery import get_model_discovery_service
from src.utils.config import config


class StartupService:
    """Service for handling application startup tasks."""
    
    def __init__(self):
        self.chroma_service = get_chroma_service_instance()
        self.document_processor = DocumentProcessor()
        self.model_discovery = get_model_discovery_service()
        self.uploads_dir = config.UPLOAD_FOLDER
        
    def initialize_application(self) -> Dict[str, Any]:
        """
        Initialize the application on startup.
        Returns status information about the initialization.
        """
        print("🚀 Initializing PocketPro:SBA Edition...")
        
        results = {
            "startup_completed": False,
            "chromadb_status": "unknown",
            "model_discovery_status": "unknown",
            "available_models": [],
            "selected_model": None,
            "files_loaded": 0,
            "files_skipped": 0,
            "errors": []
        }
        
        try:
            # Initialize model discovery first
            model_results = self._initialize_model_discovery()
            results.update(model_results)
            
            # Check ChromaDB status
            if hasattr(self.chroma_service, '_chroma_available') and self.chroma_service._chroma_available:
                results["chromadb_status"] = "available"
                print("✓ ChromaDB is available")
                
                # Load files from uploads directory
                upload_results = self._load_default_files()
                results.update(upload_results)
                
            else:
                results["chromadb_status"] = "unavailable"
                print("⚠️  ChromaDB is not available - skipping file loading")
                results["errors"].append("ChromaDB not available")
            
            # Initialize RAG operations
            rag_results = self.initialize_rag_operations()
            results["rag_status"] = rag_results["rag_status"]
            results["rag_errors"] = rag_results["errors"]
            
            results["startup_completed"] = True
            print("✅ Application initialization completed")
            
        except Exception as e:
            error_msg = f"Startup initialization failed: {str(e)}"
            print(f"❌ {error_msg}")
            results["errors"].append(error_msg)
            
        return results
    
    def _initialize_model_discovery(self) -> Dict[str, Any]:
        """
        Initialize model discovery and select best available model.
        Returns model discovery status information.
        """
        model_results = {
            "model_discovery_status": "unknown",
            "available_models": [],
            "selected_model": None
        }
        
        try:
            print("🔍 Discovering available models...")
            
            # Force refresh to get latest available models
            available_models = self.model_discovery.discover_available_models(force_refresh=True)
            
            if available_models:
                model_results["model_discovery_status"] = "success"
                model_results["available_models"] = [model["name"] for model in available_models]
                
                # Get the best model for general use
                best_model = self.model_discovery.get_best_model("general")
                model_results["selected_model"] = best_model
                
                print(f"✓ Found {len(available_models)} available models")
                print(f"✓ Selected best model: {best_model}")
                
                # Update config with the selected model (for this session)
                config.LLM_MODEL = best_model
                
            else:
                model_results["model_discovery_status"] = "no_models_found"
                print("⚠️  No available models found - using fallback")
                model_results["errors"] = ["No available models found"]
                
        except Exception as e:
            model_results["model_discovery_status"] = "error"
            model_results["errors"] = [f"Model discovery error: {str(e)}"]
            print(f"❌ Error during model discovery: {e}")
            
        return model_results
    
    def _load_default_files(self) -> Dict[str, Any]:
        """
        Load files from the uploads directory that aren't already in ChromaDB.
        Returns information about the loading process.
        """
        results = {
            "files_loaded": 0,
            "files_skipped": 0,
            "files_processed": [],
            "errors": []
        }
        
        if not os.path.exists(self.uploads_dir):
            print(f"📁 Uploads directory '{self.uploads_dir}' does not exist - creating it")
            os.makedirs(self.uploads_dir, exist_ok=True)
            return results
        
        # Get list of files in uploads directory
        upload_files = self._get_upload_files()
        
        if not upload_files:
            print("📁 No files found in uploads directory")
            return results
        
        print(f"📁 Found {len(upload_files)} files in uploads directory")
        
        # Get existing documents from ChromaDB to avoid duplicates
        existing_docs = self._get_existing_document_hashes()
        
        for file_path in upload_files:
            try:
                file_hash = self._calculate_file_hash(file_path)
                filename = os.path.basename(file_path)
                
                if file_hash in existing_docs:
                    print(f"⏭️  Skipping '{filename}' - already in database")
                    results["files_skipped"] += 1
                    results["files_processed"].append({
                        "filename": filename,
                        "status": "skipped",
                        "reason": "already_exists"
                    })
                    continue
                
                # Process and add the file
                success = self._process_and_add_file(file_path, file_hash)
                
                if success:
                    print(f"✅ Loaded '{filename}' into database")
                    results["files_loaded"] += 1
                    results["files_processed"].append({
                        "filename": filename,
                        "status": "loaded",
                        "hash": file_hash
                    })
                else:
                    print(f"❌ Failed to load '{filename}'")
                    results["files_processed"].append({
                        "filename": filename,
                        "status": "failed"
                    })
                    
            except Exception as e:
                error_msg = f"Error processing file '{filename}': {str(e)}"
                print(f"❌ {error_msg}")
                results["errors"].append(error_msg)
                results["files_processed"].append({
                    "filename": filename,
                    "status": "error",
                    "error": str(e)
                })
        
        return results
    
    def _get_upload_files(self) -> List[str]:
        """Get list of supported files in the uploads directory."""
        supported_extensions = {'.txt', '.md', '.pdf', '.docx', '.doc'}
        files = []
        
        for filename in os.listdir(self.uploads_dir):
            file_path = os.path.join(self.uploads_dir, filename)
            
            # Skip directories and hidden files
            if os.path.isdir(file_path) or filename.startswith('.'):
                continue
                
            # Check file extension
            _, ext = os.path.splitext(filename.lower())
            if ext in supported_extensions:
                files.append(file_path)
        
        return files
    
    def _get_existing_document_hashes(self) -> set:
        """Get hashes of existing documents in ChromaDB."""
        existing_hashes = set()
        
        try:
            # Query all documents to get their metadata
            if hasattr(self.chroma_service, 'collection') and self.chroma_service.collection:
                # Get all documents (ChromaDB doesn't have a "get all" method, so we use a broad query)
                results = self.chroma_service.collection.get()
                
                if results and 'metadatas' in results:
                    for metadata in results['metadatas']:
                        if metadata and 'file_hash' in metadata:
                            existing_hashes.add(metadata['file_hash'])
                            
        except Exception as e:
            print(f"⚠️  Warning: Could not retrieve existing document hashes: {e}")
        
        return existing_hashes
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
                
        return sha256_hash.hexdigest()
    
    def _process_and_add_file(self, file_path: str, file_hash: str) -> bool:
        """
        Process a file and add it to ChromaDB.
        Returns True if successful, False otherwise.
        """
        try:
            filename = os.path.basename(file_path)
            
            # Process the document
            with open(file_path, 'rb') as file:
                file_content = file.read()
            
            chunks = self.document_processor.process_document(file_content, filename)
            
            if not chunks:
                print(f"⚠️  No content extracted from '{filename}'")
                return False
            
            # Prepare data for ChromaDB
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{file_hash}_{i}"
                
                documents.append(chunk['content'])
                metadatas.append({
                    'filename': filename,
                    'file_hash': file_hash,
                    'chunk_index': i,
                    'chunk_type': chunk.get('type', 'content'),
                    'source': 'startup_upload',
                    'file_path': file_path
                })
                ids.append(chunk_id)
            
            # Add to ChromaDB
            result = self.chroma_service.add_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            return result.get('success', False)
            
        except Exception as e:
            print(f"❌ Error processing file '{filename}': {e}")
            return False
    
    def initialize_rag_operations(self) -> Dict[str, Any]:
        """
        Initialize and validate all RAG operations.
        Returns comprehensive status of RAG capabilities.
        """
        rag_results = {
            "rag_status": "unknown",
            "document_operations": {},
            "query_operations": {},
            "embedding_operations": {},
            "collection_info": {},
            "supported_operations": [],
            "errors": []
        }
        
        try:
            print("🔧 Initializing RAG operations...")
            
            # Test document CRUD operations
            doc_ops = self._test_document_operations()
            rag_results["document_operations"] = doc_ops
            
            # Test query operations
            query_ops = self._test_query_operations()
            rag_results["query_operations"] = query_ops
            
            # Test embedding operations
            embed_ops = self._test_embedding_operations()
            rag_results["embedding_operations"] = embed_ops
            
            # Get collection information
            collection_info = self._get_collection_information()
            rag_results["collection_info"] = collection_info
            
            # Determine supported operations
            supported_ops = self._determine_supported_operations(doc_ops, query_ops, embed_ops)
            rag_results["supported_operations"] = supported_ops
            
            # Overall RAG status
            if doc_ops.get("success") and query_ops.get("success"):
                rag_results["rag_status"] = "fully_operational"
                print("✅ RAG operations fully operational")
            elif doc_ops.get("success") or query_ops.get("success"):
                rag_results["rag_status"] = "partially_operational" 
                print("⚠️  RAG operations partially operational")
            else:
                rag_results["rag_status"] = "unavailable"
                print("❌ RAG operations unavailable")
                
        except Exception as e:
            rag_results["rag_status"] = "error"
            rag_results["errors"].append(f"RAG initialization error: {str(e)}")
            print(f"❌ Error initializing RAG operations: {e}")
            
        return rag_results
    
    def _test_document_operations(self) -> Dict[str, Any]:
        """Test all document CRUD operations."""
        test_results = {
            "success": False,
            "operations": {
                "add": False,
                "query": False,
                "update": False,
                "delete": False,
                "list": False
            },
            "errors": []
        }
        
        try:
            # Test document addition
            test_doc_id = "test_doc_startup_validation"
            test_content = "This is a test document for RAG validation during startup."
            test_metadata = {
                "filename": "test_validation.txt",
                "type": "test",
                "created_at": "startup_test"
            }
            
            # Test ADD operation
            try:
                add_result = self.chroma_service.add_documents(
                    documents=[test_content],
                    metadatas=[test_metadata],
                    ids=[test_doc_id]
                )
                test_results["operations"]["add"] = add_result.get("success", False)
            except Exception as e:
                test_results["errors"].append(f"Add operation failed: {str(e)}")
            
            # Test QUERY operation
            try:
                query_result = self.chroma_service.query_documents(
                    query_text="test document validation",
                    n_results=1
                )
                test_results["operations"]["query"] = query_result.get("success", False)
            except Exception as e:
                test_results["errors"].append(f"Query operation failed: {str(e)}")
            
            # Test LIST operation (get collection stats)
            try:
                stats_result = self.chroma_service.get_collection_stats()
                test_results["operations"]["list"] = stats_result.get("success", False)
            except Exception as e:
                test_results["errors"].append(f"List operation failed: {str(e)}")
            
            # Test UPDATE operation
            try:
                updated_content = "This is an updated test document."
                updated_metadata = {**test_metadata, "updated": True}
                update_result = self.chroma_service.update_documents(
                    ids=[test_doc_id],
                    documents=[updated_content],
                    metadatas=[updated_metadata]
                )
                test_results["operations"]["update"] = update_result
            except Exception as e:
                test_results["errors"].append(f"Update operation failed: {str(e)}")
            
            # Test DELETE operation (cleanup test document)
            try:
                delete_result = self.chroma_service.delete_documents(ids=[test_doc_id])
                test_results["operations"]["delete"] = delete_result
            except Exception as e:
                test_results["errors"].append(f"Delete operation failed: {str(e)}")
            
            # Overall success if basic operations work
            test_results["success"] = (
                test_results["operations"]["add"] and 
                test_results["operations"]["query"] and
                test_results["operations"]["list"]
            )
            
        except Exception as e:
            test_results["errors"].append(f"Document operations test failed: {str(e)}")
        
        return test_results
    
    def _test_query_operations(self) -> Dict[str, Any]:
        """Test various query operations and capabilities."""
        query_results = {
            "success": False,
            "capabilities": {
                "semantic_search": False,
                "filtered_search": False,
                "similarity_scoring": False,
                "multi_result": False
            },
            "performance": {},
            "errors": []
        }
        
        try:
            # Test basic semantic search
            try:
                basic_query = self.chroma_service.query_documents(
                    query_text="document content information",
                    n_results=3
                )
                query_results["capabilities"]["semantic_search"] = basic_query.get("success", False)
                
                if basic_query.get("success"):
                    results = basic_query.get("results", {})
                    documents = results.get("documents", [[]])
                    distances = results.get("distances", [[]])
                    
                    query_results["capabilities"]["multi_result"] = len(documents[0]) > 0
                    query_results["capabilities"]["similarity_scoring"] = len(distances[0]) > 0
                    
            except Exception as e:
                query_results["errors"].append(f"Semantic search test failed: {str(e)}")
            
            # Test filtered search (if documents exist)
            try:
                stats = self.chroma_service.get_collection_stats()
                if stats.get("success") and stats.get("document_count", 0) > 0:
                    filtered_query = self.chroma_service.query_documents(
                        query_text="content",
                        n_results=2,
                        where={"source": {"$ne": "nonexistent"}}
                    )
                    query_results["capabilities"]["filtered_search"] = filtered_query.get("success", False)
            except Exception as e:
                query_results["errors"].append(f"Filtered search test failed: {str(e)}")
            
            query_results["success"] = query_results["capabilities"]["semantic_search"]
            
        except Exception as e:
            query_results["errors"].append(f"Query operations test failed: {str(e)}")
        
        return query_results
    
    def _test_embedding_operations(self) -> Dict[str, Any]:
        """Test embedding-related operations."""
        embed_results = {
            "success": False,
            "embedding_info": {},
            "compatibility": False,
            "errors": []
        }
        
        try:
            # Get embedding information
            embed_info = self.chroma_service.get_embedding_info()
            embed_results["embedding_info"] = embed_info
            
            # Test embedding compatibility
            compatibility = self.chroma_service._ensure_embedding_compatibility()
            embed_results["compatibility"] = compatibility
            
            embed_results["success"] = embed_info.get("compatible", False)
            
        except Exception as e:
            embed_results["errors"].append(f"Embedding operations test failed: {str(e)}")
        
        return embed_results
    
    def _get_collection_information(self) -> Dict[str, Any]:
        """Get comprehensive collection information."""
        collection_info = {
            "exists": False,
            "stats": {},
            "configuration": {},
            "errors": []
        }
        
        try:
            # Check if collection exists and get stats
            stats = self.chroma_service.get_collection_stats()
            collection_info["stats"] = stats
            collection_info["exists"] = stats.get("success", False)
            
            # Get configuration information
            if hasattr(self.chroma_service, 'collection') and self.chroma_service.collection:
                collection_info["configuration"] = {
                    "name": getattr(self.chroma_service.collection, 'name', 'unknown'),
                    "embedding_function": str(type(self.chroma_service.embedding_function)) if self.chroma_service.embedding_function else "default"
                }
            
        except Exception as e:
            collection_info["errors"].append(f"Collection info error: {str(e)}")
        
        return collection_info
    
    def _determine_supported_operations(self, doc_ops: Dict, query_ops: Dict, embed_ops: Dict) -> List[str]:
        """Determine which RAG operations are supported based on test results."""
        supported = []
        
        if doc_ops.get("success"):
            if doc_ops["operations"].get("add"):
                supported.append("document_upload")
            if doc_ops["operations"].get("delete"):
                supported.append("document_deletion")
            if doc_ops["operations"].get("update"):
                supported.append("document_update")
            if doc_ops["operations"].get("list"):
                supported.append("document_listing")
        
        if query_ops.get("success"):
            if query_ops["capabilities"].get("semantic_search"):
                supported.append("semantic_search")
            if query_ops["capabilities"].get("filtered_search"):
                supported.append("filtered_search")
            if query_ops["capabilities"].get("similarity_scoring"):
                supported.append("relevance_scoring")
        
        if embed_ops.get("success"):
            supported.append("embedding_operations")
        
        return supported

def initialize_app_on_startup() -> Dict[str, Any]:
    """
    Convenience function to initialize the application on startup.
    This should be called when the Flask app starts.
    """
    startup_service = StartupService()
    return startup_service.initialize_application()
