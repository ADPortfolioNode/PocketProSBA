#!/usr/bin/env python3
"""
Test script for SearchAssistant functionality
"""

import sys
import os
sys.path.insert(0, '.')

print("=== Testing SearchAssistant ===")

try:
    from assistants.search import SearchAgent
    
    # Test initialization
    print("1. Testing SearchAgent initialization...")
    sa = SearchAgent()
    print("   ✅ SearchAgent instantiated successfully")
    
    # Test search functionality
    print("\n2. Testing search functionality...")
    test_query = "SBA loan eligibility requirements"
    result = sa.handle_message(test_query)
    
    print(f"   ✅ Search completed for: '{test_query}'")
    print(f"   Response text length: {len(result.get('text', ''))} characters")
    print(f"   Sources found: {len(result.get('sources', []))}")
    
    if result.get('sources'):
        print(f"   First source title: {result['sources'][0].get('title', 'N/A')}")
    
    print("\n3. Testing error handling...")
    # Test with empty query
    empty_result = sa.handle_message("")
    print(f"   ✅ Empty query handled: {'text' in empty_result}")
    
    print("\n=== SearchAssistant Test Completed Successfully ===")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
