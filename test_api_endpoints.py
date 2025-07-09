#!/usr/bin/env python3
"""
API Health Check Script
Verifies that all required API endpoints are responding correctly
"""
import sys
import json
import requests
from pprint import pprint

def test_endpoint(url, method='GET', data=None, headers=None):
    """Test a specific endpoint and return the result"""
    print(f"\nTesting {method} {url}...")
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=10)
        else:
            return {"success": False, "error": f"Unsupported method: {method}"}
        
        # Try to parse JSON response
        try:
            json_data = response.json()
            formatted_json = json.dumps(json_data, indent=2)
            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "data": json_data,
                "formatted": formatted_json
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": f"Failed to parse JSON: {str(e)}",
                "content": response.text[:200] + "..." if len(response.text) > 200 else response.text
            }
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    """Main function to test all endpoints"""
    # Base URL for all tests
    base_url = "http://localhost:8080"  # For Nginx-proxied access
    
    # Define the endpoints to test
    endpoints = [
        {"url": f"{base_url}/", "method": "GET", "name": "Frontend Root"},
        {"url": f"{base_url}/health", "method": "GET", "name": "Health Check"},
        {"url": f"{base_url}/api/health", "method": "GET", "name": "API Health"},
        {
            "url": f"{base_url}/api/chat", 
            "method": "POST", 
            "name": "Chat API",
            "data": {"message": "Hello", "userName": "Tester"}
        }
    ]
    
    # Test each endpoint
    results = []
    for endpoint in endpoints:
        result = test_endpoint(
            endpoint["url"], 
            endpoint["method"], 
            endpoint.get("data"), 
            endpoint.get("headers")
        )
        result["name"] = endpoint["name"]
        results.append(result)
        
        print(f"Result for {endpoint['name']} ({endpoint['url']}):")
        if result["success"]:
            print(f"✅ Success (Status: {result.get('status_code')})")
            if "formatted" in result:
                print(f"Response: {result['formatted']}")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
            if "content" in result:
                print(f"Content: {result['content']}")
        print("-" * 50)
    
    # Summary
    print("\n=== SUMMARY ===")
    success_count = sum(1 for r in results if r["success"])
    print(f"Total Endpoints: {len(results)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(results) - success_count}")
    
    return 0 if success_count == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())
