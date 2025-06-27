"""
Integration tests for document ingestion
Tests the complete flow from upload to storage in ChromaDB
"""
import pytest
import os
import json
from io import BytesIO

class TestDocumentIngestion:
    """Test document ingestion flow"""
    
    def test_upload_and_ingest_document(self, client, temp_pdf, mock_chroma_service):
        """Test the complete document upload and ingestion process"""
        # Create a file-like object for the test PDF
        with open(temp_pdf, 'rb') as f:
            pdf_content = f.read()
            
        data = {
            'file': (BytesIO(pdf_content), 'test_document.pdf', 'application/pdf')
        }
        
        # Test upload
        response = client.post(
            '/api/documents/upload_and_ingest_document',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        json_data = json.loads(response.data)
        assert "success" in json_data
        assert json_data["success"] is True
        
        # Verify ChromaDB service was called
        assert mock_chroma_service.add_documents.called or mock_chroma_service.store_document_embedding.called
    
    def test_invalid_file_type_rejection(self, client):
        """Test that invalid file types are rejected"""
        data = {
            'file': (BytesIO(b'invalid file content'), 'test.xyz', 'application/octet-stream')
        }
        
        response = client.post(
            '/api/documents/upload_and_ingest_document',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        json_data = json.loads(response.data)
        assert "error" in json_data
        assert "unsupported file type" in json_data["error"].lower()
    
    def test_empty_file_rejection(self, client):
        """Test that empty files are rejected"""
        data = {
            'file': (BytesIO(b''), 'empty.pdf', 'application/pdf')
        }
        
        response = client.post(
            '/api/documents/upload_and_ingest_document',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        json_data = json.loads(response.data)
        assert "error" in json_data
        assert "file is empty" in json_data["error"].lower()
