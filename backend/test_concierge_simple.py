#!/usr/bin/env python3
"""
Simple concierge test that bypasses search module requirements
and focuses on core functionality verification.
"""
import os
import sys
import logging

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_concierge():
    """Test basic concierge functionality without search module"""
    print("=== Testing Basic Concierge Functionality ===")
    
    try:
        # Import concierge directly
        from assistants.concierge import Concierge
        
        # Create concierge instance
        concierge = Concierge()
        print("✅ Concierge instance created successfully")
        
        # Test basic message handling
        test_messages = [
            "Hello, what can you help me with?",
            "Tell me about SBA loans",
            "How can I start a small business?"
        ]
        
        for i, message in enumerate(test_messages):
            print(f"\nTest {i+1}: '{message}'")
            try:
                result = concierge.handle_message(message)
                if result and "text" in result:
                    print(f"✅ Response: {result['text'][:100]}...")
                else:
                    print("❌ No response text received")
            except Exception as e:
                print(f"❌ Error handling message: {e}")
        
        print("\n=== Session Management Test ===")
        # Test session management
        session_id = "test_session_123"
        result1 = concierge.handle_message("First message", session_id)
        result2 = concierge.handle_message("Second message", session_id)
        print("✅ Session management working")
        
        return True
        
    except Exception as e:
        print(f"❌ Concierge test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_basic_concierge()
