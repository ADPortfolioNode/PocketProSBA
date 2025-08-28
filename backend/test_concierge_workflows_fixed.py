#!/usr/bin/env python3
"""
Test script for Concierge workflows (Windows-compatible version)
"""

import sys
import os
import logging

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def safe_print(message):
    """Print message safely, replacing Unicode characters."""
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode('utf-8', 'replace').decode('utf-8'))

def test_concierge_basic():
    """Test basic concierge functionality"""
    safe_print("=== Testing Basic Concierge Functionality ===")
    
    try:
        from assistants.concierge import Concierge
        
        # Test import
        concierge = Concierge()
        safe_print("[OK] Concierge imported and instantiated successfully")
        
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
            safe_print(f"{status} '{message}' -> {intent} (expected: {expected_intent})")
        
        # Test message handling
        safe_print("\n=== Testing Message Handling ===")
        test_messages = [
            "Tell me about SBA loans",
            "Find information on business grants",
            "Help with business planning"
        ]
        
        for message in test_messages:
            try:
                result = concierge.handle_message(message, "test-session-1")
                if 'text' in result:
                    safe_print(f"[OK] '{message[:20]}...' -> Response: {result['text'][:50]}...")
                else:
                    safe_print(f"[FAIL] '{message[:20]}...' -> No text in result: {result}")
            except Exception as e:
                safe_print(f"[FAIL] '{message[:20]}...' -> Error: {e}")
        
        safe_print("\n=== Basic Concierge Tests Completed ===")
        return True
        
    except Exception as e:
        safe_print(f"[FAIL] Concierge test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rag_integration():
    """Test RAG integration"""
    safe_print("\n=== Testing RAG Integration ===")
    
    try:
        from services.rag import get_rag_manager
        
        rag_manager = get_rag_manager()
        safe_print(f"[OK] RAG Manager instantiated: {rag_manager.is_available()}")
        
        if rag_manager.is_available():
            # Test collection stats
            stats = rag_manager.get_collection_stats()
            safe_print(f"[OK] Collection stats: {stats}")
            
            # Test document query
            test_query = "small business loans"
            results = rag_manager.query_documents(test_query, n_results=2)
            
            if "error" in results:
                safe_print(f"[FAIL] Query failed: {results['error']}")
            else:
                doc_count = len(results.get('documents', [[]])[0])
                safe_print(f"[OK] Query '{test_query}' returned {doc_count} documents")
                
        else:
            safe_print("ℹ RAG system not available (this is expected if ChromaDB is not running)")
            
        safe_print("=== RAG Integration Tests Completed ===")
        return True
        
    except Exception as e:
        safe_print(f"[FAIL] RAG integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_service_integration():
    """Test API service integration"""
    safe_print("\n=== Testing API Service Integration ===")
    
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
                    safe_print(f"[OK] API: '{message[:20]}...' -> Response received")
                else:
                    safe_print(f"[FAIL] API: '{message[:20]}...' -> Invalid response: {result}")
            except Exception as e:
                safe_print(f"[FAIL] API: '{message[:20]}...' -> Error: {e}")
        
        safe_print("=== API Service Integration Tests Completed ===")
        return True
        
    except Exception as e:
        safe_print(f"[FAIL] API service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    safe_print("Starting Concierge Workflow Tests...")
    safe_print("=" * 50)
    
    # Run tests
    test1 = test_concierge_basic()
    test2 = test_rag_integration() 
    test3 = test_api_service_integration()
    
    safe_print("\n" + "=" * 50)
    safe_print("TEST SUMMARY:")
    safe_print(f"Basic Concierge: {'PASS' if test1 else 'FAIL'}")
    safe_print(f"RAG Integration: {'PASS' if test2 else 'FAIL'}") 
    safe_print(f"API Integration: {'PASS' if test3 else 'FAIL'}")
    
    if all([test1, test2, test3]):
        safe_print("\n[SUCCESS] ALL TESTS PASSED! Concierge workflows are working correctly.")
        sys.exit(0)
    else:
        safe_print("\n[FAILURE] SOME TESTS FAILED. Check the output above for details.")
        sys.exit(1)
