#!/usr/bin/env python3
"""
Script to run only the function agent tests
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run only the function agent tests to verify they pass"""
    # Find the project root directory
    project_root = Path(__file__).parent.parent
    
    if not project_root.exists():
        print(f"Error: Project directory not found at {project_root}")
        return 1
    
    # Change to the project directory
    os.chdir(project_root)
    
    # Make sure required packages are installed
    print("Checking for required packages...")
    subprocess.run([
        sys.executable, "-m", "pip", "install", 
        "pytest", "pytest-mock"
    ], check=True)
    
    # Set an API key for testing
    os.environ["GEMINI_API_KEY"] = "test-api-key"
    
    # Run the specific test
    print("\nRunning function agent tests...")
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/unit/test_function_agent.py", "-v"
    ])
    
    if result.returncode == 0:
        print("\n✅ Function agent tests PASSED!")
    else:
        print("\n❌ Function agent tests FAILED!")
        
        # Provide debugging info
        print("\nDebugging information:")
        print("1. Make sure the base_assistant.py file is properly implemented")
        print("2. Check that LLMFactory is correctly implemented")
        print("3. Verify that all imports are resolving correctly")
        
        # Try to import the modules to see detailed errors
        print("\nAttempting to import modules for diagnostics:")
        try:
            from app.services.function_agent import FunctionAgent
            print("✅ Function agent module imported successfully")
            
            agent = FunctionAgent()
            print("✅ Function agent instantiated successfully")
        except Exception as e:
            print(f"❌ Error importing or instantiating function agent: {str(e)}")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
