"""
FileAgent - Specialized assistant for file operations and document management.
"""
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from src.assistants.base_assistant import BaseAssistant
from src.services.document_processor import DocumentProcessor
from src.utils.config import config


class FileAgent(BaseAssistant):
    """Specialized assistant for file processing and document management."""
    
    def __init__(self):
        super().__init__("FileAgent")
        self.document_processor = DocumentProcessor()
        self.uploads_path = os.path.abspath(config.UPLOAD_FOLDER)
        
        # Ensure uploads directory exists
        os.makedirs(self.uploads_path, exist_ok=True)
        
        # System prompt for file operations
        self.system_prompt = """You are a file processing specialist that handles document uploads and information extraction.
        You can process various file formats including PDF, DOCX, TXT, and Markdown files.
        You help users understand what files are available and their contents."""
    
    def handle_message(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Handle file-related requests."""
        try:
            message_lower = message.lower()
            
            # Check if it's a file listing request
            if any(word in message_lower for word in ["list", "show", "what"]) and "file" in message_lower:
                return self._list_files()
            
            # Check if it's a file processing request
            if context and "file_path" in context:
                file_path = context["file_path"]
                filename = context.get("filename", os.path.basename(file_path))
                return self._process_file(file_path, filename)
            
            # Check for file-related information request
            file_path = self._extract_file_path_from_message(message)
            if file_path:
                return self._get_file_info(file_path)
            
            # Default response for unclear requests
            return self._help_message()
            
        except Exception as e:
            return self.report_failure(f"Error processing file request: {str(e)}")
    
    def _list_files(self) -> Dict[str, Any]:
        """List all files in the uploads directory."""
        try:
            self._update_status("running", 20, "Scanning uploads directory...")
            
            if not os.path.exists(self.uploads_path):
                return self.report_success(
                    text="No files have been uploaded yet. The uploads directory is empty.",
                    additional_data={"files": []}
                )
            
            files = []
            for filename in os.listdir(self.uploads_path):
                file_path = os.path.join(self.uploads_path, filename)
                if os.path.isfile(file_path):
                    file_info = self._get_file_metadata(file_path, filename)
                    files.append(file_info)
            
            if not files:
                response_text = "The uploads directory exists but contains no files."
            else:
                response_text = f"Found {len(files)} file(s) in the uploads directory:\n\n"
                for file_info in files:
                    size_mb = file_info["size_bytes"] / (1024 * 1024)
                    response_text += f"• **{file_info['name']}** ({size_mb:.2f} MB)\n"
                    response_text += f"  Type: {file_info['type']}, Modified: {file_info['modified']}\n\n"
            
            return self.report_success(
                text=response_text,
                additional_data={"files": files}
            )
            
        except Exception as e:
            return self.report_failure(f"Error listing files: {str(e)}")
    
    def _process_file(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Process a file and add it to the vector database."""
        try:
            self._update_status("running", 10, f"Processing file: {filename}")
            
            # Check if file exists
            if not os.path.exists(file_path):
                return self.report_failure(f"File not found: {filename}")
            
            # Check if file type is supported
            if not self.document_processor.is_supported_file(filename):
                supported_types = ", ".join(config.ALLOWED_EXTENSIONS)
                return self.report_failure(
                    f"Unsupported file type. Supported types: {supported_types}"
                )
            
            self._update_status("running", 30, "Extracting text content...")
            
            # Process the file
            result = self.document_processor.process_file(file_path, filename)
            
            if result.get("success", False):
                chunks_created = result.get("chunks_created", 0)
                response_text = f"Successfully processed **{filename}**!\n\n"
                response_text += f"• Created {chunks_created} text chunks\n"
                response_text += f"• Added to document search index\n"
                response_text += f"• You can now search for information from this document"
                
                return self.report_success(
                    text=response_text,
                    additional_data=result
                )
            else:
                return self.report_failure(
                    f"Failed to process {filename}: {result.get('error', 'Unknown error')}"
                )
                
        except Exception as e:
            return self.report_failure(f"Error processing file {filename}: {str(e)}")
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a specific file."""
        try:
            filename = os.path.basename(file_path)
            full_path = os.path.join(self.uploads_path, filename)
            
            if not os.path.exists(full_path):
                return self.report_failure(f"File not found: {filename}")
            
            file_info = self._get_file_metadata(full_path, filename)
            
            response_text = f"**File Information: {filename}**\n\n"
            response_text += f"• **Size:** {file_info['size_bytes'] / (1024 * 1024):.2f} MB\n"
            response_text += f"• **Type:** {file_info['type']}\n"
            response_text += f"• **Modified:** {file_info['modified']}\n"
            response_text += f"• **Supported:** {'Yes' if file_info['supported'] else 'No'}\n"
            
            if file_info['supported']:
                response_text += f"\nThis file can be processed and added to the document search index."
            else:
                supported_types = ", ".join(config.ALLOWED_EXTENSIONS)
                response_text += f"\nThis file type is not supported. Supported types: {supported_types}"
            
            return self.report_success(
                text=response_text,
                additional_data={"file_info": file_info}
            )
            
        except Exception as e:
            return self.report_failure(f"Error getting file info: {str(e)}")
    
    def _get_file_metadata(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Get metadata for a file."""
        stat = os.stat(file_path)
        file_ext = Path(filename).suffix[1:].lower() if '.' in filename else ""
        
        return {
            "name": filename,
            "path": file_path,
            "size_bytes": stat.st_size,
            "modified": str(os.path.getmtime(file_path)),
            "type": file_ext,
            "supported": file_ext in config.ALLOWED_EXTENSIONS
        }
    
    def _extract_file_path_from_message(self, message: str) -> Optional[str]:
        """Try to extract a file path or filename from the message."""
        # Simple implementation - look for common file extensions
        import re
        
        # Look for filenames with common extensions
        pattern = r'\b[\w\-\.]+\.(?:pdf|docx?|txt|md|csv)\b'
        matches = re.findall(pattern, message, re.IGNORECASE)
        
        if matches:
            # Return the first match
            return matches[0]
        
        return None
    
    def _help_message(self) -> Dict[str, Any]:
        """Return help message for file operations."""
        help_text = """I can help you with file operations! Here's what I can do:

**Available Commands:**
• "List files" or "Show files" - Display all uploaded files
• "Process [filename]" - Process a specific file for search
• "File info [filename]" - Get information about a file

**Supported File Types:**
""" + ", ".join(f"*.{ext}" for ext in config.ALLOWED_EXTENSIONS) + f"""

**Upload Directory:** {self.uploads_path}

What would you like me to help you with?"""
        
        return self.report_success(text=help_text)


# Factory function for creating FileAgent instances
def create_file_agent() -> FileAgent:
    """Create a new FileAgent assistant instance."""
    return FileAgent()
