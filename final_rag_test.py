#!/usr/bin/env python3
"""
Final RAG Operations Test - Comprehensive verification
"""

import sys
import os
import requests
import json
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_DOCUMENT = "uploads/test_rag_document.txt"

def test_api_connectivity():
    """Test basic API connectivity."""
    print("🔗 Testing API Connectivity...")
    try:
        response = requests.get(f"{BASE_URL}/api/info", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Connected - {data.get('app_name', 'Unknown')}")
            print(f"📊 Document Count: {data.get('documents_count', 0)}")
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

def test_document_upload():
    """Test document upload functionality."""
    print("\n📤 Testing Document Upload...")
    
    if not os.path.exists(TEST_DOCUMENT):
        print(f"❌ Test document not found: {TEST_DOCUMENT}")
        return False
    
    try:
        with open(TEST_DOCUMENT, 'rb') as f:
            files = {'file': (TEST_DOCUMENT, f, 'text/plain')}
            response = requests.post(
                f"{BASE_URL}/api/documents/upload_and_ingest_document",
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Upload Success: {data.get('message', 'No message')}")
            return True
        else:
            print(f"❌ Upload Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Upload Error: {e}")
        return False

def test_chromadb_debug():
    """Test ChromaDB debug endpoint."""
    print("\n🔍 Testing ChromaDB Connection...")
    try:
        response = requests.get(f"{BASE_URL}/api/debug/chromadb", timeout=10)
        if response.status_code == 200:
            data = response.json()
            connection_test = data.get('connection_test', {})
            collection_stats = data.get('collection_stats', {})
            
            print(f"✅ ChromaDB Debug Response:")
            print(f"   Connection Available: {connection_test.get('available', False)}")
            print(f"   Collection Count: {connection_test.get('collection_count', 0)}")
            print(f"   Has Client: {data.get('has_client', False)}")
            print(f"   Has Collection: {data.get('has_collection', False)}")
            return connection_test.get('available', False)
        else:
            print(f"❌ Debug Endpoint Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Debug Error: {e}")
        return False

def test_rag_query():
    """Test RAG query functionality."""
    print("\n❓ Testing RAG Query...")
    try:
        query_data = {"query": "What is PocketPro SBA Edition?"}
        response = requests.post(
            f"{BASE_URL}/api/query",
            json=query_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            success = data.get('success', False)
            if success:
                results = data.get('results', {})
                documents = results.get('documents', [[]])
                print(f"✅ Query Success: Found {len(documents[0]) if documents and documents[0] else 0} documents")
                return True
            else:
                error = data.get('error', 'Unknown error')
                print(f"❌ Query Failed: {error}")
                return False
        else:
            print(f"❌ Query Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Query Error: {e}")
        return False

def test_concierge_greeting():
    """Test concierge greeting functionality."""
    print("\n👋 Testing Concierge Greeting...")
    try:
        response = requests.get(f"{BASE_URL}/api/greeting", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success', False):
                greeting_text = data.get('text', '')
                print(f"✅ Greeting Success: {greeting_text[:100]}...")
                return True
            else:
                print(f"❌ Greeting Failed: {data}")
                return False
        else:
            print(f"❌ Greeting Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Greeting Error: {e}")
        return False

def main():
    """Run comprehensive RAG operations test."""
    print("🔬 PocketPro:SBA Edition - Final RAG Operations Test")
    print("=" * 60)
    
    # Track test results
    results = {}
    
    # Run tests
    results['api_connectivity'] = test_api_connectivity()
    results['document_upload'] = test_document_upload()
    results['chromadb_debug'] = test_chromadb_debug()
    results['rag_query'] = test_rag_query()
    results['concierge_greeting'] = test_concierge_greeting()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Final Test Results:")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    # Overall status
    passed_tests = sum(results.values())
    total_tests = len(results)
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\n🎯 Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🚀 RAG Operations: FULLY FUNCTIONAL!")
    elif success_rate >= 60:
        print("⚡ RAG Operations: MOSTLY FUNCTIONAL")
    else:
        print("🔧 RAG Operations: NEEDS ATTENTION")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
