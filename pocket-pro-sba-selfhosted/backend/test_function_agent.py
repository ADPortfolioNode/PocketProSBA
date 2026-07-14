#!/usr/bin/env python3
"""
Test script for FunctionAgent functionality
"""

import sys
import os
sys.path.insert(0, '.')

print("=== Testing FunctionAgent ===")

try:
    from assistants.function import FunctionAgent
    
    # Test initialization
    print("1. Testing FunctionAgent initialization...")
    fa = FunctionAgent()
    print("   ✅ FunctionAgent instantiated successfully")
    
    # Test message handling
    print("\n2. Testing message handling...")
    result = fa.handle_message("test function message")
    print(f"   ✅ Message handling result: {result}")
    
    print("\n=== FunctionAgent Test Completed Successfully ===")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
