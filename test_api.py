import os
import requests
import sys

def check_endpoint(url, expected_status=200):
    """Check if an endpoint is accessible"""
    try:
        response = requests.get(url, timeout=5)
        status_code = response.status_code
        
        print(f"URL: {url}")
        print(f"Status Code: {status_code}")
        
        try:
            print(f"Content Type: {response.headers.get('Content-Type', 'unknown')}")
            print(f"Response: {response.text[:200]}...")  # Print first 200 chars
        except Exception as e:
            print(f"Error reading response: {e}")
            
        if status_code == expected_status:
            return True
        else:
            print(f"Expected status {expected_status}, got {status_code}")
            return False
    except Exception as e:
        print(f"Error connecting to {url}: {e}")
        return False

def main():
    """Main function to check API endpoints"""
    base_url = "http://localhost:5000"  # Adjust if different
    
    endpoints = [
        "/",
        "/health",
        "/api/health",
        "/api/documents/list"
    ]
    
    success = True
    
    print("=" * 60)
    print("API Endpoint Test")
    print("=" * 60)
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print("\nChecking endpoint:", endpoint)
        if not check_endpoint(url):
            success = False
        print("-" * 60)
    
    if success:
        print("\nAll endpoints are working!")
    else:
        print("\nSome endpoints failed. Make sure the Flask server is running.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
