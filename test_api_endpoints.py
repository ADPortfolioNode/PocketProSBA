#!/usr/bin/env python3
"""
Test script to verify API endpoints are working
"""

import requests
import sys

def test_endpoint(endpoint, method='GET', data=None):
    """Test a single API endpoint"""
    url = f"http://localhost:5000{endpoint}"
    try:
        if method == 'GET':
            response = requests.get(url, timeout=5)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=5)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
            
        print(f"🔍 {method} {endpoint}: Status {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Response: {response.text[:100]}...")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed: Cannot connect to {url}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Test all API endpoints"""
    print("🧪 Testing API Endpoints")
    print("=" * 50)
    
    endpoints = [
        ('/api/health', 'GET'),
        ('/api/info', 'GET'),
        ('/api/diagnostics', 'GET'),
        ('/api/decompose', 'POST', {'message': 'test task'}),
        ('/api/execute', 'POST', {'task': {'step': 'test step'}}),
        ('/api/validate', 'POST', {'result': 'test result', 'task': {'step': 'test step'}}),
        ('/api/query', 'POST', {'query': 'test question', 'top_k': 3}),
        ('/api/chat/', 'GET'),
        ('/api/chat/', 'POST', {'user_id': 'test_user', 'message': 'hello'})
    ]
    
    results = []
    for endpoint in endpoints:
        if len(endpoint) == 2:
            endpoint_path, method = endpoint
            data = None
        else:
            endpoint_path, method, data = endpoint
            
        success = test_endpoint(endpoint_path, method, data)
        results.append((endpoint_path, success))
        print()
    
    # Summary
    print("📊 Test Results Summary")
    print("=" * 50)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for endpoint, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {endpoint}")
    
    print(f"\nOverall: {passed}/{total} endpoints passed")
    
    if passed == total:
        print("🎉 All API endpoints are working correctly!")
        return 0
    else:
        print("⚠️  Some endpoints need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())
