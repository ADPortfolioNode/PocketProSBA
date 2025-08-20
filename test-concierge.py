#!/usr/bin/env python3
"""
Quick Concierge Regression Test
"""

import requests
import json

def test_concierge():
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Concierge Functionality...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test task decomposition
    test_messages = [
        "Help me create a business plan",
        "Find documents about SBA loans",
        "What are business requirements?"
    ]
    
    for message in test_messages:
        try:
            response = requests.post(
                f"{base_url}/api/decompose",
                json={"message": message},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if "text" in data and len(data["text"]) > 0:
                    print(f"✅ Task decomposition: '{message[:30]}...'")
                else:
                    print(f"❌ Invalid response for: '{message[:30]}...'")
                    return False
            else:
                print(f"❌ HTTP {response.status_code} for: '{message[:30]}...'")
                return False
                
        except Exception as e:
            print(f"❌ Error testing '{message[:30]}...': {e}")
            return False
    
    print("✅ All concierge tests passed!")
    return True

if __name__ == "__main__":
    test_concierge()
