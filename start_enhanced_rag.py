#!/usr/bin/env python3
"""
Enhanced RAG Service Startup Script
Activates full Gemini-powered RAG functionality for SBA loan information
"""

import os
import sys
import logging
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = ["GEMINI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        logger.error("Please set GEMINI_API_KEY in your environment")
        return False
    
    logger.info("✅ All required environment variables are set")
    return True

def install_dependencies():
    """Install required dependencies for enhanced RAG"""
    try:
        logger.info("📦 Installing enhanced RAG dependencies...")
        
        # Install backend dependencies
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-full.txt"], 
                      check=True, capture_output=True)
        
        logger.info("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        return False

def create_knowledge_base():
    """Create comprehensive SBA knowledge base"""
    try:
        logger.info("📚 Creating comprehensive SBA knowledge base...")
        
        # Import and initialize knowledge base creation
        sys.path.append('./backend')
        from backend.enhanced_gemini_rag_service import EnhancedGeminiRAGService
        
        # Create service instance to trigger knowledge base creation
        service = EnhancedGeminiRAGService()
        service._create_comprehensive_knowledge_base()
        
        logger.info("✅ Knowledge base created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create knowledge base: {e}")
        return False

def initialize_vector_store():
    """Initialize the vector store with embeddings"""
    try:
        logger.info("🔄 Initializing vector store with Gemini embeddings...")
        
        sys.path.append('./backend')
        from backend.enhanced_gemini_rag_service import enhanced_rag_service
        
        success = enhanced_rag_service.initialize_full_service()
        
        if success:
            logger.info("✅ Vector store initialized successfully")
            return True
        else:
            logger.error("❌ Failed to initialize vector store")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error initializing vector store: {e}")
        return False

def test_rag_functionality():
    """Test the RAG functionality with sample queries"""
    try:
        logger.info("🧪 Testing RAG functionality...")
        
        sys.path.append('./backend')
        from backend.enhanced_gemini_rag_service import enhanced_rag_service
        
        # Test queries
        test_queries = [
            "What are the different types of SBA loans?",
            "What are the eligibility requirements for an SBA 7(a) loan?",
            "How long does the SBA loan application process take?",
            "What are the current SBA loan interest rates?"
        ]
        
        for query in test_queries:
            logger.info(f"Testing query: {query}")
            result = enhanced_rag_service.query_sba_loans(query)
            
            if 'error' not in result:
                logger.info(f"✅ Query successful: {query[:50]}...")
            else:
                logger.warning(f"⚠️ Query failed: {result.get('error')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing RAG functionality: {e}")
        return False

def start_server():
    """Start the enhanced Flask server"""
    try:
        logger.info("🚀 Starting enhanced Flask server...")
        
        # Set environment variables
        os.environ.setdefault('FLASK_ENV', 'development')
        
        # Start the server
        subprocess.run([
            sys.executable, 
            "app_enhanced.py"
        ], check=True)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to start server: {e}")
        return False
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
        return True

def main():
    """Main startup sequence"""
    logger.info("🎯 Starting Enhanced RAG Service Activation...")
    logger.info("=" * 60)
    
    # Step 1: Check environment
    if not check_environment():
        sys.exit(1)
    
    # Step 2: Install dependencies
    if not install_dependencies():
        logger.warning("⚠️  Dependencies may already be installed, continuing...")
    
    # Step 3: Create knowledge base
    if not create_knowledge_base():
        logger.error("❌ Cannot proceed without knowledge base")
        sys.exit(1)
    
    # Step 4: Initialize vector store
    if not initialize_vector_store():
        logger.error("❌ Cannot proceed without vector store")
        sys.exit(1)
    
    # Step 5: Test functionality
    if not test_rag_functionality():
        logger.warning("⚠️  Some tests failed, but continuing...")
    
    # Step 6: Start server
    logger.info("✅ All systems ready! Starting server...")
    logger.info("=" * 60)
    logger.info("🎉 Enhanced RAG Service is now ACTIVE!")
    logger.info("📊 Full semantic search and AI-powered responses enabled")
    logger.info("🌐 Server will be available at: http://localhost:5000")
    logger.info("🔍 Test the RAG functionality with: 'What are SBA 7(a) loans?'")
    logger.info("=" * 60)
    
    start_server()

if __name__ == "__main__":
    main()
