import requests
import json

# Test the chat endpoint
url = "http://localhost:5000/api/chat"
data = {
    "user_id": "test_user",
    "message": "Hello, how can you help me with my small business?"
}

try:
    # Test GET request to chat endpoint
    response = requests.get(url)
    print(f"GET Status Code: {response.status_code}")
    print(f"GET Response: {response.text}")
    
    # Test POST request to chat endpoint
    response = requests.post(url, json=data)
    print(f"POST Status Code: {response.status_code}")
    print(f"POST Response: {response.text}")
    
except Exception as e:
    print(f"Error: {e}")
