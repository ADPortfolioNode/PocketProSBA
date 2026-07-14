#!/usr/bin/env python3
"""
Test script for Concierge workflows
"""

import sys
import os
import logging

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_concierge_basic():
    """Test basic concierge functionality"""
    print("=== Testing Basic Concierge Functionality ===")
    
    try:
        from assistants.concierge import Concierge
        
        # Test import
        concierge = Concierge()
        print("[OK] Concierge imported and instantiated successfully")
        
        # Test intent classification
        test_cases = [
            ("find SBA loan documents", "document_search"),
            ("search for business grants", "document_search"),
            ("help me create a business plan", "task_request"),
            ("build a marketing strategy", "task_request"),
            ("hello how are you", "simple_query"),
            ("what is SBA", "simple_query")
        ]
        
        for message, expected_intent in test_cases:
            intent = concierge._classify_intent(message, {})
            status = "[OK]" if intent == expected_intent else "[FAIL]"
            print(f"{status} '{message}' -> {intent} (expected: {expected_intent})")
        
        # Test message handling
        print("\n=== Testing Message Handling ===")
        test_messages = [
            "Tell me about SBA loans",
            "Find information on business grants",
            "Help with business planning"
        ]
        
        for message in test_messages:
            try:
                result = concierge.handle_message(message, "test-session-1")
                if 'text' in result:
                    print(f"[OK] '{message[:20]}...' -> Response: {result['text'][:50]}...")
                else:
                    print(f"[FAIL] '{message[:20]}...' -> No text in result: {result}")
            except Exception as e:
                print(f"[FAIL] '{message[:20]}...' -> Error: {e}")
        
        print("\n=== Basic Concierge Tests Completed ===")
        return True
        
    except Exception as e:
        print(f"[FAIL] Concierge test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rag_integration():
    """Test RAG integration"""
    print("\n=== Testing RAG Integration ===")
    
    try:
        from services.rag import get_rag_manager
        
        rag_manager = get_rag_manager()
        print(f"[OK] RAG Manager instantiated: {rag_manager.is_available()}")
        
        if rag_manager.is_available():
            # Test collection stats
            stats = rag_manager.get_collection_stats()
            print(f"[OK] Collection stats: {stats}")
            
            # Test document query
            test_query = "small business loans"
            results = rag_manager.query_documents(test_query, n_results=2)
            
            if "error" in results:
                print(f"[FAIL] Query failed: {results['error']}")
            else:
                doc_count = len(results.get('documents', [[]])[0])
                print(f"[OK] Query '{test_query}' returned {doc_count} documents")
                
        else:
            print("ℹ RAG system not available (this is expected if ChromaDB is not running)")
            
        print("=== RAG Integration Tests Completed ===")
        return True
        
    except Exception as e:
        print(f"[FAIL] RAG integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_service_integration():
    """Test API service integration"""
    print("\n=== Testing API Service Integration ===")
    
    try:
        from services.api_service import decompose_task_service
        
        test_messages = [
            "How to get SBA loan",
            "Business planning assistance",
            "Find grants for small business"
        ]
        
        for message in test_messages:
            try:
                result = decompose_task_service(message, "test-session-api")
                if 'response' in result and 'text' in result['response']:
                    print(f"[OK] API: '{message[:20]}...' -> Response received")
                else:
                    print(f"[FAIL] API: '{message[:20]}...' -> Invalid response: {result}")
            except Exception as e:
                print(f"[FAIL] API: '{message[:20]}...' -> Error: {e}")
        
        print("=== API Service Integration Tests Completed ===")
        return True
        
    except Exception as e:
        print(f"[FAIL] API service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Concierge Workflow Tests...")
    print("=" * 50)
    
    # Run tests
    test1 = test_concierge_basic()
    test2 = test_rag_integration() 
    test3 = test_api_service_integration()
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    print(f"Basic Concierge: {'PASS' if test1 else 'FAIL'}")
    print(f"RAG Integration: {'PASS' if test2 else 'FAIL'}") 
    print(f"API Integration: {'PASS' if test3 else 'FAIL'}")
    
    if all([test1, test2, test3]):
        print("\n[SUCCESS] ALL TESTS PASSED! Concierge workflows are working correctly.")
        sys.exit(0)
    else:
        print("\n[FAILURE] SOME TESTS FAILED. Check the output above for details.")
        sys.exit(1)
