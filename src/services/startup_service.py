"""
Startup service for initializing the application and loading default content.
"""
import os
import hashlib
from typing import List, Dict, Any
from src.services.chroma_service import get_chroma_service_instance
from src.services.document_processor import DocumentProcessor
from src.utils.config import config


class StartupService:
    """Service for handling application startup tasks."""
    
    def __init__(self):
        self.chroma_service = get_chroma_service_instance()
        self.document_processor = DocumentProcessor()
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
            "files_loaded": 0,
            "files_skipped": 0,
            "errors": []
        }
        
        try:
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
            
            results["startup_completed"] = True
            print("✅ Application initialization completed")
            
        except Exception as e:
            error_msg = f"Startup initialization failed: {str(e)}"
            print(f"❌ {error_msg}")
            results["errors"].append(error_msg)
            
        return results
    
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


def initialize_app_on_startup() -> Dict[str, Any]:
    """
    Convenience function to initialize the application on startup.
    This should be called when the Flask app starts.
    """
    startup_service = StartupService()
    return startup_service.initialize_application()
