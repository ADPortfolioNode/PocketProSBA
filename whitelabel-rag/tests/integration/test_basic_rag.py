"""
Integration tests for the Basic RAG workflow
"""
import pytest
import json
import os
from io import BytesIO
from unittest.mock import patch, MagicMock

class TestBasicRAG:
    """Integration tests for the basic RAG workflow"""
    
    def test_basic_rag_query_flow(self, client, mock_chroma_service, mock_llm):
        """Test the complete flow of a basic RAG query"""
        # Setup mock responses
        mock_chroma_service.query.return_value = {
            "results": [
                {"text": "Climate change is a global issue affecting various regions.", 
                 "metadata": {"source": "climate_doc.pdf", "page": 1}},
                {"text": "Rising temperatures lead to sea level rise and extreme weather.", 
                 "metadata": {"source": "climate_doc.pdf", "page": 2}},
            ]
        }
        
        mock_llm.generate_text.return_value = "Climate change is causing global warming and sea level rise."
        
        # Execute the query
        response = client.post(
            '/api/query',
            json={"query": "What is climate change?", "workflow": "basic", "top_k": 2}
        )
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "results" in data
        assert "response" in data
        assert len(data["results"]) == 2
        assert "Climate change is causing" in data["response"]
        
        # Verify that the chroma service was called
        mock_chroma_service.query.assert_called_once()
    
    def test_document_upload_and_query(self, client, temp_pdf, mock_chroma_service, mock_llm):
        """Test uploading a document and then querying it with basic RAG"""
        # Set up mock responses for document processing
        mock_chroma_service.add_documents.return_value = {"success": True, "count": 5}
        
        # Upload a test document
        with open(temp_pdf, 'rb') as f:
            pdf_content = f.read()
            
        upload_data = {
            'file': (BytesIO(pdf_content), 'test_document.pdf', 'application/pdf')
        }
        
        upload_response = client.post(
            '/api/documents/upload_and_ingest_document',
            data=upload_data,
            content_type='multipart/form-data'
        )
        
        assert upload_response.status_code == 200
        upload_result = json.loads(upload_response.data)
        assert upload_result["success"] is True
        
        # Set up mock for query
        mock_chroma_service.query.return_value = {
            "results": [
                {"text": "This is test content from the uploaded document.", 
                 "metadata": {"source": "test_document.pdf", "page": 1}}
            ]
        }
        
        mock_llm.generate_text.return_value = "The document discusses test content."
        
        # Query the uploaded document
        query_response = client.post(
            '/api/query',
            json={"query": "What is in the document?", "workflow": "basic", "top_k": 1}
        )
        
        # Verify query response
        assert query_response.status_code == 200
        query_data = json.loads(query_response.data)
        assert "results" in query_data
        assert "response" in query_data
        assert len(query_data["results"]) == 1
        assert "test content" in query_data["results"][0]["text"]
        assert "document discusses" in query_data["response"]
