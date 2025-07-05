"""
Startup verification script for PocketPro SBA
Run this to verify the app starts correctly before deployment
"""
import os
import sys
import time
import requests
import subprocess
from threading import Thread

def test_app_startup():
    """Test if the app starts and responds correctly"""
    print("🧪 Testing PocketPro SBA startup...")
    
    # Set test environment
    os.environ['PORT'] = '5001'  # Use different port for testing
    os.environ['FLASK_ENV'] = 'testing'
    
    # Start the app in a subprocess
    try:
        process = subprocess.Popen([
            sys.executable, 'app.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for startup
        time.sleep(5)
        
        # Test health endpoint
        try:
            response = requests.get('http://localhost:5001/health', timeout=10)
            if response.status_code == 200:
                data = response.json()
                print("✅ Health check passed:")
                print(f"   Status: {data.get('status')}")
                print(f"   Service: {data.get('service')}")
                print(f"   RAG Status: {data.get('rag_status')}")
                print(f"   Documents: {data.get('document_count')}")
                
                # Test info endpoint
                info_response = requests.get('http://localhost:5001/api/info', timeout=10)
                if info_response.status_code == 200:
                    print("✅ API info endpoint working")
                    
                    # Test a simple search
                    search_response = requests.post(
                        'http://localhost:5001/api/search',
                        json={'query': 'SBA loans', 'n_results': 3},
                        timeout=10
                    )
                    if search_response.status_code == 200:
                        search_data = search_response.json()
                        print(f"✅ Search endpoint working - found {search_data.get('count', 0)} results")
                        
                        print("\n🎉 All tests passed! App is ready for deployment.")
                        return True
                    else:
                        print(f"❌ Search endpoint failed: {search_response.status_code}")
                else:
                    print(f"❌ Info endpoint failed: {info_response.status_code}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            
    except Exception as e:
        print(f"❌ App startup failed: {e}")
        
    finally:
        # Clean up process
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
    
    return False

if __name__ == "__main__":
    success = test_app_startup()
    if success:
        print("\n✅ Ready for Render deployment!")
        print("   The app should start correctly on Render.")
    else:
        print("\n❌ Startup issues detected.")
        print("   Please fix the issues before deploying to Render.")
    
    sys.exit(0 if success else 1)
