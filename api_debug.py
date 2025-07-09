#!/usr/bin/env python
"""
API Test for PocketProSBA with better error handling
"""

import requests
import json
import sys

# Base URLs to test
URLS = [
    "http://localhost:8080",  # Nginx
    "http://localhost:5000",  # Backend direct
]

# Endpoints to test
ENDPOINTS = [
    {"method": "GET", "path": "/health", "name": "Simple Health"},
    {"method": "GET", "path": "/api/health", "name": "API Health"},
    {"method": "POST", "path": "/api/chat", "name": "Chat API", "data": {"message": "Hello"}},
    {"method": "POST", "path": "/api/chat", "name": "Chat API with userName", "data": {"message": "Hello", "userName": "TestUser"}},
    {"method": "POST", "path": "/api/chat", "name": "System Message", "data": {"message": "SYSTEM: User session started", "userName": "TestUser"}},
]

def test_endpoint(base_url, endpoint):
    """Test a specific endpoint at a base URL"""
    url = f"{base_url}{endpoint['path']}"
    method = endpoint["method"]
    data = endpoint.get("data")
    
    print(f"\nTesting {method} {url}...")
    print(f"Data: {json.dumps(data) if data else 'None'}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        else:
            return {"success": False, "error": f"Unsupported method: {method}"}
        
        # Print status code and headers for debugging
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        # Print raw response
        print(f"Raw Response: {response.text[:200]}...")
        
        # Check if response is JSON
        try:
            json_data = response.json()
            formatted_json = json.dumps(json_data, indent=2)
            result = {
                "success": response.status_code < 400,
                "status": response.status_code,
                "response": formatted_json
            }
        except ValueError as e:
            result = {
                "success": False,
                "status": response.status_code,
                "error": f"JSON Parse Error: {str(e)}",
                "content_type": response.headers.get("Content-Type", "unknown"),
                "content": response.text[:100] + "..." if len(response.text) > 100 else response.text
            }
            
        return result
    
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def main():
    """Run all tests"""
    for base_url in URLS:
        print(f"\nTesting endpoints at {base_url}")
        print("=" * 50)
        
        for endpoint in ENDPOINTS:
            result = test_endpoint(base_url, endpoint)
            endpoint_name = f"{endpoint['name']} ({base_url}{endpoint['path']})"
            
            print(f"Result for {endpoint_name}:")
            if result.get("success"):
                print("✅ Success")
                if "status" in result:
                    print(f"Status: {result['status']}")
                if "response" in result:
                    print(f"Response: {result['response']}")
            else:
                print("❌ Failed")
                if "error" in result:
                    print(f"Error: {result['error']}")
                if "content" in result:
                    print(f"Content: {result['content']}")
            
            print("-" * 50)

if __name__ == "__main__":
    main()
