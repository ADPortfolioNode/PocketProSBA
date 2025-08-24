#!/usr/bin/env python3
"""
Test script to verify the fixes for the identified issues.
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

def test_models_import():
    """Test that models can be imported correctly"""
    print("Testing models import...")
    try:
        from models import db, ChatMessage
        print("✓ Models imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Models import failed: {e}")
        return False

def test_config_import():
    """Test that config can be imported correctly"""
    print("Testing config import...")
    try:
        from config import Config, TestConfig
        print("✓ Config imported successfully")
        
        # Test that TestConfig has proper attributes
        test_config = TestConfig()
        assert test_config.TESTING == True
        assert 'test.db' in test_config.SQLALCHEMY_DATABASE_URI
        print("✓ TestConfig configuration verified")
        return True
    except Exception as e:
        print(f"✗ Config import failed: {e}")
        return False

def test_conftest_import():
    """Test that conftest can be imported correctly"""
    print("Testing conftest import...")
    try:
        from conftest import app, client
        print("✓ Conftest imported successfully")
        return True
    except Exception as e:
        print(f"✗ Conftest import failed: {e}")
        return False

def test_env_example_exists():
    """Test that frontend .env.example exists"""
    print("Testing frontend .env.example...")
    env_example_path = Path('frontend/.env.example')
    if env_example_path.exists():
        print("✓ Frontend .env.example exists")
        return True
    else:
        print("✗ Frontend .env.example does not exist")
        return False

def main():
    """Run all tests"""
    print("Running verification tests for PocketPro fixes...\n")
    
    tests = [
        test_models_import,
        test_config_import,
        test_conftest_import,
        test_env_example_exists
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()
    
    passed = sum(results)
    total = len(results)
    
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All fixes verified successfully!")
        return 0
    else:
        print("✗ Some fixes need attention")
        return 1

if __name__ == '__main__':
    sys.exit(main())
