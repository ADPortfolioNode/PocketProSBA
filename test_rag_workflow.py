#!/usr/bin/env python3
"""
Test script to verify RAG operations work properly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.document_processor import DocumentProcessor
from src.services.chroma_service import get_chroma_service_instance
from src.services.rag_manager import get_rag_manager
from src.services.llm_factory import LLMFactory

def test_document_processing():
    """Test document processing functionality."""
    print("🔍 Testing Document Processing...")
    
    processor = DocumentProcessor()
    
    # Test file path
    test_file = "uploads/test_rag_document.txt"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    try:
        # Process the document
        processed = processor.process_file(test_file)
        
        if processed["success"]:
            print(f"✅ Document processed successfully")
            print(f"   - Chunks created: {len(processed['chunks'])}")
            print(f"   - First chunk preview: {processed['chunks'][0][:100]}...")
            return True
        else:
            print(f"❌ Document processing failed: {processed.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Document processing error: {e}")
        return False

def test_chroma_connection():
    """Test ChromaDB connection."""
    print("\n🔍 Testing ChromaDB Connection...")
    
    try:
        chroma_service = get_chroma_service_instance()
        
        # Test basic connection
        stats = chroma_service.get_collection_stats()
        
        if stats.get("success", False):
            print("✅ ChromaDB connection successful")
            print(f"   - Document count: {stats.get('document_count', 0)}")
            return True
        else:
            print(f"❌ ChromaDB connection failed: {stats.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ ChromaDB connection error: {e}")
        return False

def test_llm_connection():
    """Test LLM connection."""
    print("\n🔍 Testing LLM Connection...")
    
    try:
        llm = LLMFactory.get_llm()
        
        # Test simple generation
        response = llm.generate_response(
            prompt="Say 'Hello World' to test the connection.",
            context="",
            system_prompt="You are a helpful assistant. Respond exactly as requested."
        )
        
        if response and "hello" in response.lower():
            print("✅ LLM connection successful")
            print(f"   - Response: {response[:100]}...")
            return True
        else:
            print(f"❌ LLM connection failed or unexpected response: {response}")
            return False
            
    except Exception as e:
        print(f"❌ LLM connection error: {e}")
        return False

def test_rag_workflow():
    """Test complete RAG workflow."""
    print("\n🔍 Testing RAG Workflow...")
    
    try:
        rag_manager = get_rag_manager()
        
        # Test a query
        query = "What are the key features mentioned in the document?"
        
        response = rag_manager.generate_rag_response(
            query=query,
            system_prompt="You are a helpful assistant. Answer based on the provided context."
        )
        
        if response.get("success", False):
            print("✅ RAG workflow successful")
            print(f"   - Query: {query}")
            print(f"   - Response: {response['text'][:200]}...")
            print(f"   - Sources found: {len(response.get('sources', []))}")
            return True
        else:
            print(f"❌ RAG workflow failed: {response.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ RAG workflow error: {e}")
        return False

def main():
    """Run all RAG operation tests."""
    print("🚀 Starting RAG Operations Verification\n")
    
    results = {
        "document_processing": test_document_processing(),
        "chroma_connection": test_chroma_connection(), 
        "llm_connection": test_llm_connection(),
        "rag_workflow": test_rag_workflow()
    }
    
    print("\n📊 Test Results Summary:")
    print("=" * 40)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 40)
    
    if all_passed:
        print("🎉 All RAG operations are working correctly!")
    else:
        print("⚠️  Some RAG operations need attention.")
        
    return all_passed

if __name__ == "__main__":
    main()
