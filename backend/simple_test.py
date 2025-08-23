#!/usr/bin/env python3
"""
Simple test script for concierge functionality
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== Simple Concierge Test ===")

try:
    # Test basic imports
    from assistants.concierge import Concierge
    print("✓ Concierge imported successfully")
    
    # Test instantiation
    concierge = Concierge()
    print("✓ Concierge instantiated successfully")
    
    # Test intent classification
    test_messages = [
        "find SBA loan documents",
        "help me create business plan", 
        "what is SBA"
    ]
    
    for msg in test_messages:
        intent = concierge._classify_intent(msg, {})
        print(f"✓ '{msg[:20]}...' -> {intent}")
    
    # Test message handling
    result = concierge.handle_message("Tell me about SBA loans", "test-session-1")
    print("✓ Message handling completed")
    
    if 'text' in result:
        print(f"Response: {result['text'][:60]}...")
    else:
        print(f"Result: {result}")
    
    print("=== Test Completed Successfully ===")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
