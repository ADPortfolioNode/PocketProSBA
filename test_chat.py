import requests
import json

url = "http://localhost:5000/api/chat"
data = {
    "user_id": "test-user",
    "message": "Hello"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
