#!/usr/bin/env python3
"""
Test script to check environment variables
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

print("Environment variables:")
print(f"GOOGLE_API_KEY: {os.getenv('GOOGLE_API_KEY')}")
print(f"GOOGLE_CSE_ID: {os.getenv('GOOGLE_CSE_ID')}")
print(f"GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY')}")
