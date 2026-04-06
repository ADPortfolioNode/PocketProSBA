#!/usr/bin/env python3
"""
Test conversation store functionality
"""
import os
import sys
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_conversation_store():
    """Test conversation store functionality"""
    print("🧪 Testing Conversation Store")
    print("=" * 40)

    try:
        from backend.services.conversation_store import ConversationStore

        # Test 1: Basic initialization
        print("1. Testing Conversation Store Initialization...")
        store = ConversationStore()
        print("   ✅ Conversation store initialized")

        # Test 2: Create and retrieve conversation
        print("\n2. Testing Conversation Creation and Retrieval...")
        session_id = "test_session_123"

        # Get conversation (should create new one)
        conversation = store.get_conversation(session_id)
        if conversation and conversation.get("session_id") == session_id:
            print("   ✅ Conversation created and retrieved successfully")
        else:
            print("   ❌ Failed to create/retrieve conversation")
            return False

        # Test 3: Add messages
        print("\n3. Testing Message Addition...")
        success1 = store.add_message(session_id, "user", "Hello, I need help with SBA loans")
        success2 = store.add_message(session_id, "assistant", "I'd be happy to help you with SBA loans!")

        if success1 and success2:
            print("   ✅ Messages added successfully")
        else:
            print("   ❌ Failed to add messages")
            return False

        # Test 4: Retrieve messages
        print("\n4. Testing Message Retrieval...")
        messages = store.get_recent_messages(session_id, limit=5)
        if len(messages) == 2:
            print(f"   ✅ Retrieved {len(messages)} messages correctly")
        else:
            print(f"   ❌ Expected 2 messages, got {len(messages)}")
            return False

        # Test 5: Update conversation state
        print("\n5. Testing Conversation State Updates...")
        success = store.update_conversation_state(session_id, "task_in_progress")
        if success:
            # Retrieve and check
            updated_conversation = store.get_conversation(session_id)
            if updated_conversation.get("conversation_state") == "task_in_progress":
                print("   ✅ Conversation state updated successfully")
            else:
                print("   ❌ Conversation state not updated correctly")
                return False
        else:
            print("   ❌ Failed to update conversation state")
            return False

        # Test 6: Conversation summary
        print("\n6. Testing Conversation Summary...")
        summary = store.get_conversation_summary(session_id)
        if summary and "total_messages" in summary:
            print(f"   ✅ Conversation summary generated: {summary['total_messages']} messages")
        else:
            print("   ❌ Failed to generate conversation summary")
            return False

        # Test 7: Session stats
        print("\n7. Testing Session Statistics...")
        stats = store.get_session_stats()
        if stats and "total_sessions" in stats:
            print(f"   ✅ Session stats retrieved: {stats['total_sessions']} sessions")
        else:
            print("   ❌ Failed to retrieve session stats")
            return False

        print("\n" + "=" * 40)
        print("🎉 Conversation store is working correctly!")
        return True

    except Exception as e:
        print(f"❌ Conversation store test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_conversation_store()
    sys.exit(0 if success else 1)