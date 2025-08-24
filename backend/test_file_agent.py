#!/usr/bin/env python3
"""
Test script for FileAgent functionality
"""

import sys
import os
sys.path.insert(0, '.')

print("=== Testing FileAgent ===")

try:
    from assistants.file import FileAgent
    
    # Test initialization
    print("1. Testing FileAgent initialization...")
    fa = FileAgent()
    print("   ✅ FileAgent instantiated successfully")
    
    # Test message handling
    print("\n2. Testing message handling...")
    result = fa.handle_message("test file message")
    print(f"   ✅ Message handling result: {result}")
    
    # Test list files
    print("\n3. Testing list files...")
    files_result = fa.list_files()
    print(f"   ✅ List files result: {files_result}")
    
    print("\n=== FileAgent Test Completed Successfully ===")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
