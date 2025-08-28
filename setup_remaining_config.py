#!/usr/bin/env python3
"""
Script to guide through the remaining configuration steps for PocketProSBA
"""
import os
import sys

def setup_google_cse():
    """Guide for setting up Google Custom Search Engine"""
    print("🔍 Google CSE Setup Instructions:")
    print("=" * 50)
    print("1. Go to: https://programmablesearchengine.google.com/")
    print("2. Create a new search engine")
    print("3. Configure the search engine to search the entire web")
    print("4. Get your Search Engine ID (looks like: 012345678901234567890:abcdefghijk)")
    print("5. Update backend/.env file:")
    print("   GOOGLE_CSE_ID=your_actual_search_engine_id_here")
    print()

def setup_chromadb():
    """Guide for setting up ChromaDB"""
    print("📚 ChromaDB Setup Options:")
    print("=" * 50)
    print("Option 1: Local ChromaDB (Development)")
    print("   pip install chromadb")
    print("   chroma run --host localhost --port 8000")
    print("   Then set in backend/.env:")
    print("   CHROMADB_HOST=localhost")
    print("   CHROMADB_PORT=8000")
    print()
    print("Option 2: ChromaDB Cloud (Production)")
    print("   Sign up at: https://www.trychroma.com/")
    print("   Create a collection and get API credentials")
    print("   Set in backend/.env:")
    print("   CHROMADB_HOST=api.trychroma.com")
    print("   CHROMADB_PORT=443")
    print("   CHROMADB_API_KEY=your_api_key_here")
    print()

def deploy_render():
    """Guide for Render deployment"""
    print("🚀 Render Deployment Instructions:")
    print("=" * 50)
    print("1. Connect your GitHub repository to Render")
    print("2. Create a new Web Service from render.yaml")
    print("3. Set environment variables in Render dashboard:")
    print("   - GEMINI_API_KEY")
    print("   - GOOGLE_API_KEY") 
    print("   - GOOGLE_CSE_ID")
    print("   - SECRET_KEY")
    print("   - CHROMADB_HOST")
    print("   - CHROMADB_PORT")
    print("4. Deploy and monitor logs")
    print()

def check_current_config():
    """Check current configuration status"""
    print("📋 Current Configuration Status:")
    print("=" * 50)
    
    env_file = 'backend/.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            content = f.read()
            if 'your_google_custom_search_engine_id_here' in content:
                print("⚠️  GOOGLE_CSE_ID: Needs configuration")
            else:
                print("✅ GOOGLE_CSE_ID: Configured")
                
            if 'localhost' in content and '8000' in content:
                print("✅ ChromaDB: Local configuration set")
            else:
                print("⚠️  ChromaDB: Needs configuration")
    else:
        print("❌ Environment file not found")

def main():
    """Main configuration guide"""
    print("PocketProSBA - Remaining Configuration Guide")
    print("=" * 60)
    
    check_current_config()
    print()
    
    setup_google_cse()
    setup_chromadb()
    deploy_render()
    
    print("✅ Configuration guide complete!")
    print("Follow these steps to complete your production setup.")

if __name__ == "__main__":
    main()
