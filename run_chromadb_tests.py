"""
ChromaDB Test Runner
Executes all ChromaDB tests in the correct order
"""
import subprocess
import sys
import os
from pathlib import Path

def run_script(script_name, description):
    """Run a Python script and return success status"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"Running: python {script_name}")
    print('='*60)
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=False, 
                              text=True,
                              cwd=Path.cwd())
        
        if result.returncode == 0:
            print(f"\n✅ {script_name} completed successfully!")
            return True
        else:
            print(f"\n❌ {script_name} failed with return code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error running {script_name}: {e}")
        return False

def check_files_exist():
    """Check if required files exist"""
    required_files = [
        'fix_chromadb.py',
        'test_chromadb_simple.py',
        'app.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files found")
    return True

def main():
    """Main test runner"""
    print("🚀 ChromaDB Test Runner for PocketPro SBA")
    print("This will run all ChromaDB tests in the correct order")
    
    # Check if files exist
    if not check_files_exist():
        return False
    
    # Step 1: Fix ChromaDB
    success_fix = run_script('fix_chromadb.py', 'Clean up and test ChromaDB')
    
    if not success_fix:
        print("\n❌ ChromaDB fix failed. Cannot proceed with further tests.")
        return False
    
    # Step 2: Simple functionality test
    success_simple = run_script('test_chromadb_simple.py', 'Verify basic functionality')
    
    if not success_simple:
        print("\n❌ Basic functionality test failed. App may still work, but with issues.")
    
    # Step 3: Start the app (this will run until interrupted)
    print(f"\n{'='*60}")
    print("🚀 Starting the main application")
    print("Running: python app.py")
    print("Press Ctrl+C to stop the application")
    print('='*60)
    
    try:
        subprocess.run([sys.executable, 'app.py'], cwd=Path.cwd())
    except KeyboardInterrupt:
        print("\n\n🛑 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error running app.py: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    print(f"\n{'='*60}")
    
    if success:
        print("🎉 ChromaDB test sequence completed!")
    else:
        print("❌ Some issues were encountered during testing")
    
    print("\nManual testing steps:")
    print("1. Check if the app started without ChromaDB errors")
    print("2. Test endpoints: http://localhost:5000/health")
    print("3. Test endpoints: http://localhost:5000/api/info")
    print("4. Try adding a document via POST /api/documents/add")
    
    sys.exit(0 if success else 1)
