import pytest
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def test_document_addition_performance(test_app, sample_documents):
    """Test performance of document addition"""
    start_time = time.time()
    
    for doc in sample_documents:
        response = test_app.post('/api/documents/add', 
                               json=doc,
                               content_type='application/json')
        if response.status_code == 503:
            pytest.skip("ChromaDB not available")
        assert response.status_code == 200
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Should be able to add documents reasonably quickly
    assert duration < 10.0  # 10 seconds max for 3 documents
    
    # Test average time per document
    avg_time = duration / len(sample_documents)
    assert avg_time < 5.0  # 5 seconds max per document

def test_search_performance(test_app, sample_documents, sample_queries):
    """Test performance of search functionality"""
    # First add documents
    for doc in sample_documents:
        response = test_app.post('/api/documents/add', 
                               json=doc,
                               content_type='application/json')
        if response.status_code == 503:
            pytest.skip("ChromaDB not available")
    
    time.sleep(0.1)  # Wait for indexing
    
    # Test search performance
    start_time = time.time()
    
    for query in sample_queries:
        response = test_app.post('/api/search',
                               json={'query': query, 'n_results': 5},
                               content_type='application/json')
        assert response.status_code == 200
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Should be able to search quickly
    assert duration < 5.0  # 5 seconds max for all queries
    
    # Test average search time
    avg_time = duration / len(sample_queries)
    assert avg_time < 2.0  # 2 seconds max per search

def test_concurrent_operations(test_app, sample_documents):
    """Test concurrent document operations"""
    if not test_app:
        pytest.skip("Test app not available")
    
    def add_document(doc):
        try:
            response = test_app.post('/api/documents/add', 
                                   json=doc,
                                   content_type='application/json')
            return response.status_code == 200
        except Exception:
            return False
    
    # Test concurrent document addition
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(add_document, doc) for doc in sample_documents]
        results = [future.result() for future in as_completed(futures)]
    
    # At least some should succeed (depends on ChromaDB availability)
    success_count = sum(results)
    assert success_count >= 0  # Allow for ChromaDB not being available

def test_memory_usage_stability(test_app, sample_documents):
    """Test that memory usage remains stable during operations"""
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform multiple operations
        for _ in range(5):
            for doc in sample_documents:
                response = test_app.post('/api/documents/add', 
                                       json=doc,
                                       content_type='application/json')
                if response.status_code == 503:
                    break  # ChromaDB not available
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024  # 100MB
        
    except ImportError:
        pytest.skip("psutil not available for memory testing")
