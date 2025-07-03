#!/usr/bin/env python3
"""Test script to check the current status endpoints."""

import requests
import json

def test_endpoints():
    """Test the Flask app endpoints if it's running."""
    try:
        # Test root endpoint
        response = requests.get('http://localhost:5000/', timeout=5)
        print('=== ROOT ENDPOINT (/) ===')
        print(json.dumps(response.json(), indent=2))
        print()
        
        # Test health endpoint
        response = requests.get('http://localhost:5000/health', timeout=5)
        print('=== HEALTH ENDPOINT (/health) ===')
        print(json.dumps(response.json(), indent=2))
        print()
        
        # Test status endpoint
        response = requests.get('http://localhost:5000/api/status', timeout=5)
        print('=== STATUS ENDPOINT (/api/status) ===')
        print(json.dumps(response.json(), indent=2))
        
    except Exception as e:
        print(f'Flask app not running locally: {e}')
        print('This is expected if the app is not currently running.')

if __name__ == "__main__":
    test_endpoints()
