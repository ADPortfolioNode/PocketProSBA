"""
Test Google Internet Search Integration

This script tests the Google Custom Search API integration for WhiteLabelRAG.
It verifies that the system can use the Google API key to perform internet searches.

Usage:
    python scripts/test_internet_search.py
"""

import os
import sys
import json
import requests
import argparse
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

def test_direct_google_api():
    """Test Google Custom Search API directly."""
    print("\n===== Testing Direct Google API Call =====")
    
    api_key = os.environ.get('GOOGLE_API_KEY')
    search_engine_id = os.environ.get('INTERNET_SEARCH_ENGINE_ID')
    
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found in environment variables.")
        print("   Make sure to set it in your .env file or export it.")
        return False
        
    if not search_engine_id:
        print("❌ Error: INTERNET_SEARCH_ENGINE_ID not found in environment variables.")
        print("   Make sure to set it in your .env file or export it.")
        return False
    
    print(f"✓ Found API key: {api_key[:4]}...{api_key[-4:]}")
    print(f"✓ Found Search Engine ID: {search_engine_id}")
    
    query = "latest AI advancements"
    base_url = "https://www.googleapis.com/customsearch/v1"
    
    params = {
        'key': api_key,
        'cx': search_engine_id,
        'q': query,
        'num': 3
    }
    
    try:
        print(f"\nSending test query: '{query}'")
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract and display search results
        items = data.get('items', [])
        if items:
            print(f"\n✓ Success! Found {len(items)} results:")
            for i, item in enumerate(items, 1):
                print(f"\n{i}. {item.get('title')}")
                print(f"   Link: {item.get('link')}")
                print(f"   Snippet: {item.get('snippet')}")
            return True
        else:
            print("❌ No results found. The API call worked but returned no items.")
            return False
    
    except requests.RequestException as e:
        print(f"❌ API request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_app_integration():
    """Test the app's internet search integration through the API endpoint."""
    print("\n===== Testing App Integration =====")
    
    try:
        # Ensure the app is running
        app_url = "http://localhost:5000"
        health_check = requests.get(f"{app_url}/health", timeout=5)
        if health_check.status_code != 200:
            print(f"❌ App health check failed with status code: {health_check.status_code}")
            print("   Make sure the app is running on http://localhost:5000")
            return False
        
        print("✓ App is running")
        
        # Test the query endpoint with internet search
        query_data = {
            'query': 'latest AI developments',
            'top_k': 3,
            'use_internet_search': True
        }
        
        print(f"\nSending test query to app: '{query_data['query']}'")
        response = requests.post(f"{app_url}/api/query", json=query_data, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Query API call failed with status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        data = response.json()
        
        # Check for internet search results
        internet_results = data.get('internet_search_response')
        if internet_results:
            print("\n✓ Success! Received internet search results from the app.")
            
            # Display a preview of the results
            if 'text' in internet_results:
                print("\nResponse preview:")
                preview = internet_results['text'][:200] + "..." if len(internet_results['text']) > 200 else internet_results['text']
                print(preview)
            
            # Check for result details
            if 'additional_data' in internet_results and 'results' in internet_results['additional_data']:
                result_count = len(internet_results['additional_data']['results'])
                print(f"\nFound {result_count} search results in the response")
            
            return True
        else:
            print("❌ No internet search results found in the response.")
            print("   This might indicate the app is not properly configured for internet search.")
            print(f"   Full response: {json.dumps(data, indent=2)}")
            return False
    
    except requests.RequestException as e:
        print(f"❌ API request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function to run tests."""
    parser = argparse.ArgumentParser(description='Test Google Internet Search integration')
    parser.add_argument('--direct-only', action='store_true', help='Only test the direct API call')
    parser.add_argument('--app-only', action='store_true', help='Only test the app integration')
    args = parser.parse_args()

    print("🔍 Google Internet Search Integration Test")
    print("==========================================")
    
    # Run direct API test if requested or if no specific test is specified
    direct_result = False
    if args.direct_only or not args.app_only:
        direct_result = test_direct_google_api()
    
    # Run app integration test if requested or if no specific test is specified
    app_result = False
    if args.app_only or not args.direct_only:
        app_result = test_app_integration()
    
    # Print overall results
    print("\n==========================================")
    if args.direct_only:
        print(f"Direct API Test: {'✅ PASSED' if direct_result else '❌ FAILED'}")
    elif args.app_only:
        print(f"App Integration Test: {'✅ PASSED' if app_result else '❌ FAILED'}")
    else:
        print(f"Direct API Test: {'✅ PASSED' if direct_result else '❌ FAILED'}")
        print(f"App Integration Test: {'✅ PASSED' if app_result else '❌ FAILED'}")
        if direct_result and not app_result:
            print("\n⚠️ Your Google API key works but the app integration failed.")
            print("   This suggests an issue with how the app is using the API key.")
        elif not direct_result:
            print("\n⚠️ The direct API test failed, which means your Google API key or Search Engine ID may be invalid.")
    
    return 0 if (args.direct_only and direct_result) or (args.app_only and app_result) or (direct_result and app_result) else 1

if __name__ == "__main__":
    sys.exit(main())
