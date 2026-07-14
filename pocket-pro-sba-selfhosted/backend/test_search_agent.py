#!/usr/bin/env python3
"""
Test script for SearchAgent
"""

import os
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    from assistants.search import SearchAgent
    
    print("Testing SearchAgent initialization...")
    search_agent = SearchAgent()
    print("SearchAgent initialized successfully!")
    
    # Test search functionality
    print("\nTesting search functionality...")
    result = search_agent.handle_message("SBA loan eligibility")
    print(f"Search completed: {len(result.get('sources', []))} sources found")
    print("SearchAgent test passed!")
    
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
