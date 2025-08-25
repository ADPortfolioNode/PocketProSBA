import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from config import TestConfig

class TestAPIComprehensive:
    """Comprehensive test suite for API endpoints"""

    @pytest.fixture
    def app(self):
        """Create test app with test configuration"""
        app = create_app(TestConfig)
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/api/health')
        assert response.status_code == 200
        assert response.json['status'] == 'healthy'

    def test_get_system_info(self, client):
        """Test system info endpoint"""
        response = client.get('/api/info')
        assert response.status_code == 200
        assert 'service' in response.json
        assert 'version' in response.json
        assert 'status' in response.json

    def test_decompose_task_success(self, client):
        """Test successful task decomposition"""
        with patch('services.api_service.decompose_task_service') as mock_service:
            mock_service.return_value = {'response': 'test response'}
            
            response = client.post('/api/decompose', json={
                'message': 'test message',
                'session_id': 'test_session'
            })
            
            assert response.status_code == 200
            assert response.json['response'] == 'test response'

    def test_decompose_task_no_message(self, client):
        """Test task decomposition without message"""
        response = client.post('/api/decompose', json={'session_id': 'test_session'})
        assert response.status_code == 400
        assert response.json['error'] == 'Message is required'

    def test_decompose_task_no_data(self, client):
        """Test task decomposition without data"""
        response = client.post('/api/decompose')
        assert response.status_code == 400
        assert response.json['error'] == 'No JSON data provided'

    def test_execute_step_success(self, client):
        """Test successful step execution"""
        with patch('services.api_service.execute_step_service') as mock_service:
            mock_service.return_value = {'result': 'test result'}
            
            response = client.post('/api/execute', json={'task': {'step': 'test'}})
            
            assert response.status_code == 200
            assert response.json['result'] == 'test result'

    def test_execute_step_no_data(self, client):
        """Test step execution without data"""
        response = client.post('/api/execute', json={})
        assert response.status_code == 400
        assert response.json['error'] == 'No JSON data provided'

    def test_validate_step_success(self, client):
        """Test successful step validation"""
        with patch('services.api_service.validate_step_service') as mock_service:
            mock_service.return_value = {'validation': 'test validation'}
            
            response = client.post('/api/validate', json={
                'result': 'test result',
                'task': {'step': 'test'}
            })
            
            assert response.status_code == 200
            assert response.json['validation'] == 'test validation'

    def test_validate_step_no_data(self, client):
        """Test step validation without data"""
        response = client.post('/api/validate', json={})
        assert response.status_code == 400
        assert response.json['error'] == 'No JSON data provided'

    def test_query_documents_success(self, client):
        """Test successful document query"""
        with patch('services.api_service.query_documents_service') as mock_service:
            mock_service.return_value = {'results': ['doc1', 'doc2']}
            
            response = client.post('/api/query', json={'query': 'test query'})
            
            assert response.status_code == 200
            assert 'results' in response.json

    def test_query_documents_no_query(self, client):
        """Test document query without query"""
        response = client.post('/api/query', json={})
        assert response.status_code == 400
        assert response.json['error'] == 'Query is required'

    def test_query_documents_with_top_k(self, client):
        """Test document query with top_k parameter"""
        with patch('services.api_service.query_documents_service') as mock_service:
            mock_service.return_value = {'results': ['doc1', 'doc2']}
            
            response = client.post('/api/query', json={
                'query': 'test query',
                'top_k': 3
            })
            
            assert response.status_code == 200
            assert 'results' in response.json

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get('/')
        assert response.status_code == 200
        assert response.json['service'] == 'PocketPro SBA'
        assert response.json['status'] == 'running'

    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.get('/api/health')
        assert 'Access-Control-Allow-Origin' in response.headers

    def test_error_handling_404(self, client):
        """Test 404 error handling"""
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404
        assert 'error' in response.json

    def test_error_handling_500(self, client):
        """Test 500 error handling"""
        with patch('services.api_service.get_system_info_service') as mock_service:
            mock_service.side_effect = Exception('Test error')
            
            response = client.get('/api/info')
            assert response.status_code == 500
            assert 'error' in response.json
