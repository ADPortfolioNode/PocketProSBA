#!/usr/bin/env python3
"""
API Test Script for PocketProSBA - Testing User Greeting Flow
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8080"

def test_chat_with_user_greeting():
    """Test the chat API with user greeting"""
    print("Testing User Greeting Flow...")
    
    # 1. Start a session with user name
    user_data = {
        "message": "SYSTEM: User session started",
        "userName": "Test User"
    }
    
    try:
        print(f"POST {BASE_URL}/api/chat (Start Session)")
        response = requests.post(f"{BASE_URL}/api/chat", json=user_data)
        response.raise_for_status()
        session_cookies = response.cookies
        result = response.json()
        
        print(f"✅ Session Start Success (Status: {response.status_code})")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        # 2. Send a greeting message
        greeting_data = {
            "message": "Hello",
            "userName": "Test User"
        }
        
        print(f"\nPOST {BASE_URL}/api/chat (Greeting)")
        greeting_response = requests.post(
            f"{BASE_URL}/api/chat", 
            json=greeting_data,
            cookies=session_cookies
        )
        greeting_response.raise_for_status()
        greeting_result = greeting_response.json()
        
        print(f"✅ Greeting Success (Status: {greeting_response.status_code})")
        print(f"Response: {json.dumps(greeting_result, indent=2)}")
        
        # 3. Test a question about SBA
        question_data = {
            "message": "Tell me about SBA loans",
            "userName": "Test User"
        }
        
        print(f"\nPOST {BASE_URL}/api/chat (Question)")
        question_response = requests.post(
            f"{BASE_URL}/api/chat", 
            json=question_data,
            cookies=session_cookies
        )
        question_response.raise_for_status()
        question_result = question_response.json()
        
        print(f"✅ Question Success (Status: {question_response.status_code})")
        print(f"Response: {json.dumps(question_result, indent=2)}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_chat_with_user_greeting()
    if success:
        print("\n✅ User Greeting Flow Test Passed")
        sys.exit(0)
    else:
        print("\n❌ User Greeting Flow Test Failed")
        sys.exit(1)
