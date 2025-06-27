"""
Document processing service for handling various file formats.
"""
import os
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
import PyPDF2
import docx
import markdown
from src.utils.config import config
from src.services.chroma_service import get_chroma_service_instance


class DocumentProcessor:
    """Service for processing and chunking documents."""
    
    def __init__(self):
        self.chroma_service = get_chroma_service_instance()
        self.supported_extensions = config.ALLOWED_EXTENSIONS
    
    def process_file(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Process a file and add it to the vector database."""
        try:
            # Extract text from file
            text_content = self._extract_text(file_path, filename)
            
            if not text_content:
                return {
                    "success": False,
                    "error": "Could not extract text from file"
                }
            
            # Create chunks
            chunks = self._create_chunks(text_content)
            
            # Prepare metadata
            metadatas = []
            ids = []
            documents = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{filename}_{i}_{str(uuid.uuid4())[:8]}"
                metadata = {
                    "source": filename,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "file_type": self._get_file_extension(filename),
                    "file_path": file_path
                }
                
                ids.append(chunk_id)
                metadatas.append(metadata)
                documents.append(chunk)
            
            # Add to ChromaDB
            success = self.chroma_service.add_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            if success:
                return {
                    "success": True,
                    "message": f"Successfully processed {filename}",
                    "chunks_created": len(chunks),
                    "filename": filename
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to add documents to vector database"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error processing file: {str(e)}"
            }
    
    def _extract_text(self, file_path: str, filename: str) -> str:
        """Extract text content from various file formats."""
        file_ext = self._get_file_extension(filename).lower()
        
        try:
            if file_ext == 'txt':
                return self._extract_text_from_txt(file_path)
            elif file_ext == 'pdf':
                return self._extract_text_from_pdf(file_path)
            elif file_ext == 'docx':
                return self._extract_text_from_docx(file_path)
            elif file_ext == 'md':
                return self._extract_text_from_markdown(file_path)
            else:
                raise ValueError(f"Unsupported file extension: {file_ext}")
        
        except Exception as e:
            print(f"Error extracting text from {filename}: {e}")
            return ""
    
    def _extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def _extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def _extract_text_from_markdown(self, file_path: str) -> str:
        """Extract text from Markdown file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            md_content = file.read()
        
        # Convert markdown to HTML then extract text
        html_content = markdown.markdown(md_content)
        # Remove HTML tags (simple approach)
        import re
        text = re.sub(r'<[^>]+>', '', html_content)
        return text
    
    def _create_chunks(self, text: str) -> List[str]:
        """Split text into chunks for processing."""
        # Simple chunking by sentences and character count
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size, save current chunk
            if len(current_chunk) + len(sentence) > config.CHUNK_SIZE:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += ". " + sentence
                else:
                    current_chunk = sentence
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename."""
        return Path(filename).suffix[1:] if '.' in filename else ""
    
    def is_supported_file(self, filename: str) -> bool:
        """Check if file type is supported."""
        extension = self._get_file_extension(filename).lower()
        return extension in self.supported_extensions
