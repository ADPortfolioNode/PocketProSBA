import pytest
import json
import time
from unittest.mock import patch, MagicMock

def test_health_check(test_app):
    """Test health check endpoint"""
    response = test_app.get('/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'PocketPro SBA'

def test_system_info(test_app):
    """Test system info endpoint"""
    response = test_app.get('/api/info')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['service'] == 'PocketPro SBA'
    assert data['version'] == '1.0.0'
    assert 'chromadb_status' in data

def test_available_models(test_app):
    """Test available models endpoint"""
    response = test_app.get('/api/models')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'models' in data
    assert isinstance(data['models'], list)

def test_document_addition_success(test_app, sample_documents):
    """Test successful document addition"""
    doc = sample_documents[0]
    
    response = test_app.post('/api/documents/add', 
                           json=doc,
                           content_type='application/json')
    
    if response.status_code == 503:
        # ChromaDB not available - skip test
        pytest.skip("ChromaDB not available")
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'document_id' in data
    assert data['message'] == 'Document added successfully'

def test_document_addition_missing_text(test_app):
    """Test document addition with missing text"""
    response = test_app.post('/api/documents/add', 
                           json={'metadata': {'source': 'test'}},
                           content_type='application/json')
    
    if response.status_code == 503:
        pytest.skip("ChromaDB not available")
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'required' in data['error'].lower()

def test_semantic_search_success(test_app, sample_documents, sample_queries):
    """Test successful semantic search"""
    # First add a document
    doc = sample_documents[0]
    add_response = test_app.post('/api/documents/add', 
                               json=doc,
                               content_type='application/json')
    
    if add_response.status_code == 503:
        pytest.skip("ChromaDB not available")
    
    # Wait a moment for indexing
    time.sleep(0.1)
    
    # Now search
    query = sample_queries[0]
    search_response = test_app.post('/api/search',
                                  json={'query': query, 'n_results': 3},
                                  content_type='application/json')
    
    assert search_response.status_code == 200
    data = json.loads(search_response.data)
    assert 'query' in data
    assert 'results' in data
    assert 'count' in data
    assert isinstance(data['results'], list)

def test_rag_chat_success(test_app, sample_documents, sample_queries):
    """Test successful RAG chat"""
    # First add a document
    doc = sample_documents[0]
    add_response = test_app.post('/api/documents/add', 
                               json=doc,
                               content_type='application/json')
    
    if add_response.status_code == 503:
        pytest.skip("ChromaDB not available")
    
    # Wait a moment for indexing
    time.sleep(0.1)
    
    # Now chat
    query = sample_queries[0]
    chat_response = test_app.post('/api/chat',
                                json={'message': query},
                                content_type='application/json')
    
    assert chat_response.status_code == 200
    data = json.loads(chat_response.data)
    assert 'query' in data
    assert 'response' in data
    assert 'sources' in data
    assert isinstance(data['sources'], list)

def test_rag_end_to_end_workflow(test_app, sample_documents, sample_queries):
    """Test complete RAG workflow"""
    # Step 1: Add documents
    for doc in sample_documents:
        response = test_app.post('/api/documents/add', 
                               json=doc,
                               content_type='application/json')
        if response.status_code == 503:
            pytest.skip("ChromaDB not available")
        assert response.status_code == 200
    
    # Wait for indexing
    time.sleep(0.2)
    
    # Step 2: Verify documents are stored
    response = test_app.get('/api/documents')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['count'] >= len(sample_documents)
    
    # Step 3: Test search functionality
    for query in sample_queries:
        response = test_app.post('/api/search',
                               json={'query': query, 'n_results': 3},
                               content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'results' in data
    
    # Step 4: Test RAG chat
    for query in sample_queries:
        response = test_app.post('/api/chat',
                               json={'message': query},
                               content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'response' in data
        assert 'sources' in data

def test_embedding_function_functionality():
    """Test the custom embedding function"""
    from app import SimpleEmbeddingFunction
    
    embedding_func = SimpleEmbeddingFunction()
    
    # Test with sample texts
    texts = ["Hello world", "This is a test", "ChromaDB embedding test"]
    embeddings = embedding_func(texts)
    
    assert len(embeddings) == len(texts)
    assert all(len(emb) == 384 for emb in embeddings)
    assert all(isinstance(val, float) for emb in embeddings for val in emb)

def test_chromadb_unavailable_responses(test_app):
    """Test responses when ChromaDB is unavailable"""
    with patch('app.collection', None):
        # Test document addition
        response = test_app.post('/api/documents/add', 
                               json={'text': 'test'},
                               content_type='application/json')
        assert response.status_code == 503
        
        # Test search
        response = test_app.post('/api/search',
                               json={'query': 'test'},
                               content_type='application/json')
        assert response.status_code == 503
        
        # Test chat
        response = test_app.post('/api/chat',
                               json={'message': 'test'},
                               content_type='application/json')
        assert response.status_code == 503
    assert 'total_count' in data

def test_get_all_documents(test_app, sample_documents):
    """Test retrieving all documents"""
    # First add a document
    doc = sample_documents[0]
    add_response = test_app.post('/api/documents/add', 
                               json=doc,
                               content_type='application/json')
    
    if add_response.status_code == 503:
        pytest.skip("ChromaDB not available")
    
    # Get all documents
    response = test_app.get('/api/documents')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'documents' in data
    assert 'count' in data
    assert isinstance(data['documents'], list)

def test_search_filters(test_app):
    """Test search filters endpoint"""
    response = test_app.get('/api/search/filters')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'filters' in data
    assert 'document_types' in data
    assert isinstance(data['filters'], list)
    assert isinstance(data['document_types'], list)

def test_assistants_endpoint(test_app):
    """Test assistants endpoint"""
    response = test_app.get('/api/assistants')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'assistants' in data
    assert isinstance(data['assistants'], list)

def test_startup_endpoint(test_app):
    """Test startup endpoint"""
    response = test_app.get('/startup')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'ready' in data
    assert 'chromadb_available' in data
    assert 'service' in data

def test_chromadb_unavailable_responses(test_app):
    """Test responses when ChromaDB is unavailable"""
    with patch('app.collection', None):
        # Test document addition
        response = test_app.post('/api/documents/add', 
                               json={'text': 'test'},
                               content_type='application/json')
        assert response.status_code == 503
        
        # Test search
        response = test_app.post('/api/search',
                               json={'query': 'test'},
                               content_type='application/json')
        assert response.status_code == 503
        
        # Test chat
        response = test_app.post('/api/chat',
                               json={'message': 'test'},
                               content_type='application/json')
        assert response.status_code == 503

def test_embedding_function_functionality():
    """Test the custom embedding function"""
    from app import SimpleEmbeddingFunction
    
    embedding_func = SimpleEmbeddingFunction()
    
    # Test with sample texts
    texts = ["Hello world", "This is a test", "ChromaDB embedding test"]
    embeddings = embedding_func(texts)
    
    assert len(embeddings) == len(texts)
    assert all(len(emb) == 384 for emb in embeddings)
    assert all(isinstance(val, float) for emb in embeddings for val in emb)

def test_rag_end_to_end_workflow(test_app, sample_documents, sample_queries):
    """Test complete RAG workflow"""
    # Step 1: Add documents
    for doc in sample_documents:
        response = test_app.post('/api/documents/add', 
                               json=doc,
                               content_type='application/json')
        if response.status_code == 503:
            pytest.skip("ChromaDB not available")
        assert response.status_code == 200
    
    # Wait for indexing
    time.sleep(0.2)
    
    # Step 2: Verify documents are stored
    response = test_app.get('/api/documents')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['count'] >= len(sample_documents)
    
    # Step 3: Test search functionality
    for query in sample_queries:
        response = test_app.post('/api/search',
                               json={'query': query, 'n_results': 3},
                               content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'results' in data
    
    # Step 4: Test RAG chat
    for query in sample_queries:
        response = test_app.post('/api/chat',
                               json={'message': query},
                               content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'response' in data
        assert 'sources' in data
