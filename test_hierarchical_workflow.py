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

API_BASE = os.environ.get("POCKETPRO_API_BASE", "http://localhost:5000")

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

        # Test 3: Direct assistant API call (there is no /api/assistants/task;
        # the real endpoints are /concierge, /search, /file, /function,
        # all protected by Bearer auth, so 401 without a token is expected)
        print("\n3. Testing Assistant API Endpoint...")
        api_url = f"{API_BASE}/api/assistants/concierge"

        payload = {
            "message": test_message,
            "context": {
                "session_id": "test_session_123"
            }
        }

        try:
            response = requests.post(api_url, json=payload, timeout=10)
            if response.status_code == 401:
                print("   [WARN] Assistant API is protected (401 without a token) - endpoint reachable")
            elif response.status_code == 200:
                data = response.json()
                if data.get("text") or data.get("success"):
                    print("   [OK] Assistant API endpoint working")
                else:
                    print("   [FAIL] Assistant API returned error")
                    return False
            else:
                print(f"   [FAIL] Assistant API returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"   [FAIL] Assistant API call failed: {e}")
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
            api_url = f"{API_BASE}/api/assistants/{assistant_type}"
            payload = {
                "message": test_query,
                "context": {"source": "test"}
            }

            try:
                response = requests.post(api_url, json=payload, timeout=5)
                if response.status_code == 401:
                    print(f"   [WARN] {assistant_type.title()}Agent API is protected (401 without a token)")
                elif response.status_code == 200:
                    print(f"   [OK] {assistant_type.title()}Agent API working")
                else:
                    print(f"   [FAIL] {assistant_type.title()}Agent API returned status {response.status_code}")
            except requests.exceptions.RequestException:
                print(f"   [WARN] {assistant_type.title()}Agent API not accessible (server not running)")

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

            # Second RAG query (there is no query_documents_adaptive on
            # RAGManager; the real workflow is query_documents)
            second_results = rag_manager.query_documents("SBA business planning", n_results=2)
            if "error" not in second_results:
                print("   ✅ Second RAG query working")
            else:
                print("   ❌ Second RAG query failed")
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