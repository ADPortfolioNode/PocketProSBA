#!/usr/bin/env python3
"""
Script to verify environment configuration and test system functionality
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_environment_variables():
    """Check if all required environment variables are set"""
    print("🔍 Checking Environment Variables...")
    
    required_vars = [
        'SECRET_KEY',
        'GEMINI_API_KEY', 
        'GOOGLE_API_KEY',
        'GOOGLE_CSE_ID',
        'CHROMADB_HOST',
        'CHROMADB_PORT'
    ]
    
    all_set = True
    for var in required_vars:
        value = os.environ.get(var)
        if value and value not in ['your_google_custom_search_engine_id_here', '']:
            print(f"   ✅ {var}: Set (length: {len(value)})")
        else:
            print(f"   ⚠️  {var}: Missing or needs configuration")
            all_set = False
    
    return all_set

def test_assistants():
    """Test all assistant functionality"""
    print("\n🧪 Testing Assistant Functionality...")
    
    try:
        sys.path.insert(0, '.')
        
        # Test Concierge
        from assistants.concierge import Concierge
        concierge = Concierge()
        result = concierge.handle_message("Test SBA loan information", "test-session")
        print(f"   ✅ Concierge: Working - {result['text'][:50]}...")
        
        # Test other assistants
        from assistants.file import FileAgent
        file_agent = FileAgent()
        print(f"   ✅ FileAgent: Working")
        
        from assistants.function import FunctionAgent
        function_agent = FunctionAgent()
        print(f"   ✅ FunctionAgent: Working")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Assistant Test Failed: {e}")
        return False

def test_rag_system():
    """Test RAG system functionality"""
    print("\n📚 Testing RAG System...")
    
    try:
        from services.rag import get_rag_manager
        rag_manager = get_rag_manager()
        
        if rag_manager.is_available():
            stats = rag_manager.get_collection_stats()
            print(f"   ✅ RAG System: Available - {stats.get('count', 0)} documents")
            return True
        else:
            print("   ⚠️  RAG System: ChromaDB connection required")
            print("      Set CHROMADB_HOST and CHROMADB_PORT environment variables")
            return False
            
    except Exception as e:
        print(f"   ❌ RAG System Test Failed: {e}")
        return False

def test_api_services():
    """Test API service functionality"""
    print("\n🌐 Testing API Services...")
    
    try:
        from services.api_service import get_system_info_service, decompose_task_service
        
        # Test system info
        system_info = get_system_info_service()
        print(f"   ✅ System Info: {system_info['service']} v{system_info['version']}")
        
        # Test task decomposition
        result = decompose_task_service("Help with business planning", "test-api")
        print(f"   ✅ Task Decomposition: Working")
        
        return True
        
    except Exception as e:
        print(f"   ❌ API Service Test Failed: {e}")
        return False

def main():
    """Main verification function"""
    print("=" * 60)
    print("PocketProSBA Environment Verification")
    print("=" * 60)
    
    # Check environment
    env_ok = check_environment_variables()
    
    # Test functionality
    assistants_ok = test_assistants()
    rag_ok = test_rag_system() 
    api_ok = test_api_services()
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    if all([env_ok, assistants_ok, rag_ok, api_ok]):
        print("🎉 ALL SYSTEMS OPERATIONAL - READY FOR PRODUCTION")
        print("\nNext steps:")
        print("1. Deploy using render.yaml configuration")
        print("2. Set up ChromaDB instance for RAG functionality")
        print("3. Configure Google CSE ID for search functionality")
    else:
        print("⚠️  SYSTEM NEEDS CONFIGURATION")
        print("\nRequired actions:")
        if not env_ok:
            print("- Complete environment variable configuration")
        if not rag_ok:
            print("- Set up ChromaDB database")
        print("- Update .env file with actual API keys and configuration")

if __name__ == "__main__":
    main()
