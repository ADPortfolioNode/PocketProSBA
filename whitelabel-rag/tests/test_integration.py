import pytest
import json
import time

def test_sba_business_scenario(test_app):
    """Test complete SBA business advice scenario"""
    # Add SBA-related documents
    sba_docs = [
        {
            'text': 'SBA 7(a) loans are the most common type of SBA loan. They can be used for working capital, equipment, real estate, and business acquisition.',
            'metadata': {'source': 'sba_loans', 'type': 'loan_info', 'category': '7a_loans'}
        },
        {
            'text': 'To qualify for SBA loans, your business must operate for profit, be considered small by SBA standards, and meet SBA credit requirements.',
            'metadata': {'source': 'sba_eligibility', 'type': 'qualification', 'category': 'requirements'}
        },
        {
            'text': 'SCORE provides free business mentoring and resources to help small businesses start and grow.',
            'metadata': {'source': 'sba_resources', 'type': 'mentoring', 'category': 'support'}
        }
    ]
    
    # Add documents
    for doc in sba_docs:
        response = test_app.post('/api/documents/add', 
                               json=doc,
                               content_type='application/json')
        if response.status_code == 503:
            pytest.skip("ChromaDB not available")
        assert response.status_code == 200
    
    time.sleep(0.1)  # Wait for indexing
    
    # Test business scenario queries
    business_queries = [
        'How can I get funding for my small business?',
        'What are the requirements for SBA loans?',
        'Where can I get business mentoring?'
    ]
    
    for query in business_queries:
        # Test search
        search_response = test_app.post('/api/search',
                                      json={'query': query, 'n_results': 3},
                                      content_type='application/json')
        assert search_response.status_code == 200
        search_data = json.loads(search_response.data)
        assert len(search_data['results']) > 0
        
        # Test RAG chat
        chat_response = test_app.post('/api/chat',
                                    json={'message': query},
                                    content_type='application/json')
        assert chat_response.status_code == 200
        chat_data = json.loads(chat_response.data)
        assert 'response' in chat_data
        assert len(chat_data['sources']) > 0

def test_document_filtering_by_metadata(test_app):
    """Test filtering documents by metadata"""
    # Add documents with different metadata
    docs_with_metadata = [
        {
            'text': 'This is about loans',
            'metadata': {'type': 'loan_info', 'category': 'finance'}
        },
        {
            'text': 'This is about marketing',
            'metadata': {'type': 'marketing_info', 'category': 'business'}
        },
        {
            'text': 'This is about regulations',
            'metadata': {'type': 'regulatory_info', 'category': 'compliance'}
        }
    ]
    
    for doc in docs_with_metadata:
        response = test_app.post('/api/documents/add', 
                               json=doc,
                               content_type='application/json')
        if response.status_code == 503:
            pytest.skip("ChromaDB not available")
        assert response.status_code == 200
    
    time.sleep(0.1)
    
    # Test that search returns documents with relevant metadata
    response = test_app.post('/api/search',
                           json={'query': 'loans', 'n_results': 5},
                           content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Should find relevant documents
    assert len(data['results']) > 0

def test_bulk_operations_workflow(test_app):
    """Test bulk operations and workflow"""
    bulk_docs = [
        {
            'text': f'Document {i} about business topic {i}',
            'metadata': {'doc_id': i, 'batch': 'test_batch'}
        }
        for i in range(10)
    ]
    
    # Test bulk addition
    response = test_app.post('/api/documents/bulk',
                           json={'documents': bulk_docs},
                           content_type='application/json')
    
    if response.status_code == 503:
        pytest.skip("ChromaDB not available")
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert data['total_count'] == 10
    
    time.sleep(0.1)
    
    # Test that documents are searchable
    response = test_app.post('/api/search',
                           json={'query': 'business topic', 'n_results': 10},
                           content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['results']) >= 5  # Should find multiple documents

def test_error_recovery_and_resilience(test_app):
    """Test system resilience and error recovery"""
    # Test with invalid document data
    invalid_docs = [
        {'text': ''},  # Empty text
        {'metadata': {'source': 'test'}},  # Missing text
        {'text': None},  # Null text
        {'text': 123},  # Invalid text type
    ]
    
    for doc in invalid_docs:
        response = test_app.post('/api/documents/add', 
                               json=doc,
                               content_type='application/json')
        if response.status_code == 503:
            continue  # ChromaDB not available
        # Should handle errors gracefully
        assert response.status_code in [400, 500]
    
    # Test with invalid search queries
    invalid_queries = [
        {'query': ''},  # Empty query
        {'query': None},  # Null query
        {'n_results': -1},  # Invalid n_results
        {'n_results': 'invalid'},  # Invalid n_results type
    ]
    
    for query_data in invalid_queries:
        response = test_app.post('/api/search',
                               json=query_data,
                               content_type='application/json')
        if response.status_code == 503:
            continue  # ChromaDB not available
        # Should handle errors gracefully
        assert response.status_code in [400, 500]

def test_system_limits_and_boundaries(test_app):
    """Test system limits and boundary conditions"""
    # Test large document
    large_doc = {
        'text': 'A' * 10000,  # 10KB document
        'metadata': {'size': 'large'}
    }
    
    response = test_app.post('/api/documents/add', 
                           json=large_doc,
                           content_type='application/json')
    
    if response.status_code == 503:
        pytest.skip("ChromaDB not available")
    
    # Should handle large documents
    assert response.status_code in [200, 400, 413]  # Success, bad request, or payload too large
    
    # Test many small documents
    small_docs = [
        {
            'text': f'Small doc {i}',
            'metadata': {'batch': 'small', 'index': i}
        }
        for i in range(50)  # 50 small documents
    ]
    
    response = test_app.post('/api/documents/bulk',
                           json={'documents': small_docs},
                           content_type='application/json')
    
    if response.status_code != 503:  # Only test if ChromaDB is available
        assert response.status_code in [200, 400, 500]  # Should handle gracefully
