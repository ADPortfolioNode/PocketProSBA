"""
Integration tests for the API endpoints
"""
import pytest
import json
from io import BytesIO
from fastapi.testclient import TestClient
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    client = TestClient(app)
    yield client

class TestAPI:
    """Integration tests for the API endpoints"""
    
    def test_health_endpoint(self, client):
        """Test that the health endpoint returns 200 OK"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'online'
        assert 'services' in data
    
    def test_api_health_endpoint(self, client):
        """Test that the API health endpoint returns 200 OK"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'online'
    
    def test_files_listing(self, client):
        """Test listing files endpoint"""
        response = client.get('/api/files')
        assert response.status_code == 200
        data = response.json()
        assert 'files' in data
        assert isinstance(data['files'], list)
    
    def test_decompose_endpoint(self, client, mock_llm, monkeypatch):
        """Test the decompose endpoint"""
        # Reset ChromaService singleton
        from app.services.chroma_service import _chroma_service_instance
        _chroma_service_instance = None
        
        # Configure mock LLM response
        mock_llm.generate_text.return_value = json.dumps({
            "steps": [
                {
                    "step_number": 1,
                    "instruction": "Search for information",
                    "suggested_agent_type": "SearchAgent"
                }
            ]
        })
        
        response = client.post(
            '/api/decompose',
            json={"message": "Test query"}
        )
        
        assert response.status_code == 200
        assert "steps" in response.json()
    
    def test_file_upload(self, client, temp_pdf, mock_chroma_service):
        """Test file upload endpoint"""
        # Read the test PDF file
        with open(temp_pdf, 'rb') as f:
            pdf_content = f.read()
        
        # Create a file-like object for the test PDF
        data = {
            'file': ('test_document.pdf', BytesIO(pdf_content), 'application/pdf')
        }
        
        # Submit the file
        response = client.post(
            '/api/files',
            files=data
        )
        
        # Check the response
        assert response.status_code == 200
        result = response.json()
        assert 'filename' in result
        assert result['filename'] == 'test_document.pdf'
    
    def test_query_endpoint(self, client, mock_chroma_service, mock_llm):
        """Test the query endpoint"""
        # Setup mock responses
        mock_chroma_service.query.return_value = {
            "results": [
                {"text": "Test content about climate change", 
                 "metadata": {"source": "test_doc.pdf"}}
            ]
        }
        
        mock_llm.generate_text.return_value = "Climate change refers to long-term shifts in temperatures and weather patterns."
        
        # Test the query endpoint
        response = client.post(
            '/api/query',
            json={"query": "What is climate change?", "top_k": 1}
        )
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 1
        assert "response" in data
        assert "climate change" in data["response"].lower()
