#!/usr/bin/env python3
"""
Test script to verify hierarchical assistant workflow
Tests the flow: Concierge → TaskAssistant → Step Assistants
"""
import os
import sys
import json
import requests
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_hierarchical_workflow():
    """Test the complete hierarchical workflow"""
    print("🧪 Testing Hierarchical Assistant Workflow")
    print("=" * 50)

    # Test data
    test_message = "Help me create a business plan for a small coffee shop. I need to research SBA loan options and create a marketing strategy."

    try:
        # Test 1: Concierge classification
        print("1. Testing Concierge Intent Classification...")
        from backend.assistants.concierge import Concierge
        concierge = Concierge()

        # Create a mock conversation
        conversation = {
            "session_id": "test_session_123",
            "messages": [],
            "user_info": {},
            "conversation_state": "information_gathering",
            "last_activity": datetime.now().isoformat()
        }

        # Test intent classification
        intent = concierge._classify_intent(test_message, conversation)
        print(f"   Intent classified as: {intent}")

        if intent == "task_request":
            print("   ✅ Intent classification working correctly")
        else:
            print(f"   ❌ Expected 'task_request', got '{intent}'")
            return False

        # Test 2: Task decomposition via Concierge
        print("\n2. Testing Task Decomposition...")
        result = concierge.handle_message(test_message, "test_session_123")

        if result and "text" in result:
            print("   ✅ Concierge handled task request successfully")
            print(f"   Response preview: {result['text'][:100]}...")
        else:
            print("   ❌ Concierge failed to handle task request")
            return False

        # Test 3: Direct TaskAssistant API call
        print("\n3. Testing TaskAssistant API Endpoint...")
        api_url = "http://localhost:5000/api/assistants/task"

        payload = {
            "message": test_message,
            "context": {
                "session_id": "test_session_123"
            }
        }

        try:
            response = requests.post(api_url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print("   ✅ TaskAssistant API endpoint working")
                    print(f"   Response preview: {data['response']['text'][:100]}...")
                else:
                    print("   ❌ TaskAssistant API returned error")
                    return False
            else:
                print(f"   ❌ TaskAssistant API returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"   ❌ TaskAssistant API call failed: {e}")
            print("   Note: This is expected if the server is not running")
            print("   Manual testing required when server is running")

        # Test 4: Step Assistant API endpoints
        print("\n4. Testing Step Assistant API Endpoints...")

        assistants = [
            ("search", "Find information about SBA business loans"),
            ("file", "List available documents"),
            ("function", "Calculate simple interest for a loan")
        ]

        for assistant_type, test_query in assistants:
            api_url = f"http://localhost:5000/api/assistants/{assistant_type}"
            payload = {
                "message": test_query,
                "context": {"source": "test"}
            }

            try:
                response = requests.post(api_url, json=payload, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        print(f"   ✅ {assistant_type.title()}Agent API working")
                    else:
                        print(f"   ❌ {assistant_type.title()}Agent API returned error")
                else:
                    print(f"   ❌ {assistant_type.title()}Agent API returned status {response.status_code}")
            except requests.exceptions.RequestException:
                print(f"   ⚠️  {assistant_type.title()}Agent API not accessible (server not running)")

        # Test 5: RAG Workflow verification
        print("\n5. Testing RAG Workflows...")
        from backend.services.rag import get_rag_manager
        rag_manager = get_rag_manager()

        if rag_manager and rag_manager.is_available():
            # Test basic RAG
            basic_results = rag_manager.query_documents("SBA loans", n_results=2)
            if "error" not in basic_results:
                print("   ✅ Basic RAG workflow working")
            else:
                print("   ❌ Basic RAG workflow failed")

            # Test adaptive RAG
            adaptive_results = rag_manager.query_documents_adaptive("SBA business planning", n_results=2)
            if "error" not in adaptive_results:
                print("   ✅ Adaptive RAG workflow working")
            else:
                print("   ❌ Adaptive RAG workflow failed")
        else:
            print("   ⚠️  RAG manager not available for testing")

        print("\n" + "=" * 50)
        print("🎉 Hierarchical workflow test completed!")
        print("\nNote: Some API tests may show as not accessible if the server is not running.")
        print("Run the server with 'python run.py' and re-run this test for full verification.")

        return True

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_hierarchical_workflow()
    sys.exit(0 if success else 1)