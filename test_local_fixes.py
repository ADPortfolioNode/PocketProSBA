#!/usr/bin/env python3
"""
Local test script to verify all ChromaDB v2 API fixes are working.
Tests the fixes before deploying to Render.com
"""

import requests
import json
import sys

def test_endpoint(name, url, description=""):
    """Test a single endpoint and return result"""
    try:
        print(f"Testing {name}...")
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            print(f"   ✅ {name}: PASS (Status: {r.status_code})")
            return True, r.json()
        else:
            print(f"   ❌ {name}: FAIL (Status: {r.status_code}) - {r.text[:100]}")
            return False, None
    except Exception as e:
        print(f"   ❌ {name}: ERROR - {str(e)}")
        return False, None

def main():
    print("=== LOCAL TESTING: ChromaDB v2 API FIXES ===")
    print("Testing locally before Render.com deployment...")
    print()
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: ChromaDB v2 API Direct
    total_tests += 1
    success, data = test_endpoint(
        "ChromaDB v2 Heartbeat", 
        "http://localhost:8000/api/v2/heartbeat",
        "Direct test of fixed v2 endpoint"
    )
    if success:
        tests_passed += 1
        if 'nanosecond heartbeat' in data:
            print(f"      Response type: {type(data['nanosecond heartbeat'])}")
    
    print()
    
    # Test 2: Backend Health Check
    total_tests += 1
    success, data = test_endpoint(
        "Backend Health", 
        "http://localhost:5000/health",
        "Test updated health check"
    )
    if success:
        tests_passed += 1
        print(f"      Service: {data.get('service', 'N/A')}")
        print(f"      ChromaDB Available: {data.get('chromadb_available', 'N/A')}")
    
    print()
    
    # Test 3: Root Route
    total_tests += 1
    success, data = test_endpoint(
        "Root Route", 
        "http://localhost:5000/",
        "Test fixed root route"
    )
    if success:
        tests_passed += 1
        print(f"      Message: {data.get('message', 'N/A')}")
        print(f"      ChromaDB Status: {data.get('chromadb_status', 'N/A')}")
    
    print()
    
    # Test 4: API Endpoints Discovery
    total_tests += 1
    success, data = test_endpoint(
        "API Endpoints", 
        "http://localhost:5000/api/endpoints",
        "Test endpoint discovery"
    )
    if success:
        tests_passed += 1
        print(f"      Total Endpoints: {data.get('count', 0)}")
    
    print()
    
    # Test 5: System Status
    total_tests += 1
    success, data = test_endpoint(
        "System Status", 
        "http://localhost:5000/api/status",
        "Test comprehensive status"
    )
    if success:
        tests_passed += 1
        services = data.get('services', {})
        print(f"      ChromaDB: {services.get('chromadb', {}).get('status', 'unknown')}")
        print(f"      LLM: {services.get('llm', {}).get('status', 'unknown')}")
    
    print()
    print("=== TEST SUMMARY ===")
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! Ready for Render.com deployment!")
        print()
        print("✅ ChromaDB v2 API fixes working locally")
        print("✅ No more 'v1 API deprecated' errors")
        print("✅ Health checks updated and functional")
        print("✅ Root route working correctly")
        print("✅ All API endpoints accessible")
        return True
    else:
        print(f"❌ {total_tests - tests_passed} tests failed. Please fix before deploying.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
