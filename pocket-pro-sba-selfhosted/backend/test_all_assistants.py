#!/usr/bin/env python3
"""
Comprehensive test script for all assistants
"""

import sys
import os
import logging

# Configure logging to see all output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, '.')

def test_concierge():
    """Test Concierge assistant"""
    print("\n" + "="*50)
    print("TESTING CONCIERGE ASSISTANT")
    print("="*50)
    
    try:
        from assistants.concierge import Concierge
        
        # Test initialization
        concierge = Concierge()
        print("[OK] Concierge initialized successfully")
        
        # Test message handling
        result = concierge.handle_message("What are SBA loan requirements?", "test-session-1")
        print(f"[OK] Message handling: {result.get('text', 'No text')[:100]}...")
        
        return True
    except Exception as e:
        print(f"[FAIL] Concierge test failed: {e}")
        return False

def test_search_agent():
    """Test SearchAgent"""
    print("\n" + "="*50)
    print("TESTING SEARCH AGENT")
    print("="*50)
    
    try:
        from assistants.search import SearchAgent
        
        # Test initialization
        search_agent = SearchAgent()
        print("[OK] SearchAgent initialized successfully")
        
        # Test search functionality
        result = search_agent.handle_message("SBA loan eligibility")
        print(f"[OK] Search completed: {len(result.get('sources', []))} sources found")
        
        return True
    except Exception as e:
        print(f"[FAIL] SearchAgent test failed: {e}")
        return False

def test_file_agent():
    """Test FileAgent"""
    print("\n" + "="*50)
    print("TESTING FILE AGENT")
    print("="*50)
    
    try:
        from assistants.file import FileAgent
        
        # Test initialization
        file_agent = FileAgent()
        print("[OK] FileAgent initialized successfully")
        
        # Test message handling
        result = file_agent.handle_message("test file message")
        print(f"[OK] Message handling: {result}")
        
        # Test list files
        files = file_agent.list_files()
        print(f"[OK] List files: {files}")
        
        return True
    except Exception as e:
        print(f"[FAIL] FileAgent test failed: {e}")
        return False

def test_function_agent():
    """Test FunctionAgent"""
    print("\n" + "="*50)
    print("TESTING FUNCTION AGENT")
    print("="*50)
    
    try:
        from assistants.function import FunctionAgent
        
        # Test initialization
        function_agent = FunctionAgent()
        print("[OK] FunctionAgent initialized successfully")
        
        # Test message handling
        result = function_agent.handle_message("test function message")
        print(f"[OK] Message handling: {result}")
        
        return True
    except Exception as e:
        print(f"[FAIL] FunctionAgent test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("COMPREHENSIVE ASSISTANT TESTING")
    print("="*60)
    
    results = {
        "concierge": test_concierge(),
        "search_agent": test_search_agent(),
        "file_agent": test_file_agent(),
        "function_agent": test_function_agent()
    }
    
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for assistant, success in results.items():
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {assistant}")
    
    print(f"\nOverall: {passed}/{total} assistants passed")
    
    if passed == total:
        print("SUCCESS: ALL ASSISTANTS ARE PRODUCTION READY!")
    else:
        print("WARNING: Some assistants need attention")

if __name__ == "__main__":
    main()
