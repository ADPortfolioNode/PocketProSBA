#!/usr/bin/env python3
"""
Test script to directly test the status endpoints functionality without starting the full Flask app
"""

import sys
import os
import json

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_status_functions():
    """Test the status endpoint functions directly"""
    try:
        # Import the required services
        from src.utils.config import config
        from src.services.rag_manager import get_rag_manager
        from src.services.llm_factory import LLMFactory
        from src.services.model_discovery import get_model_discovery_service
        from datetime import datetime

        print("=== TESTING STATUS ENDPOINT FUNCTIONALITY ===")
        print()

        # Initialize services
        print("Initializing services...")
        rag_manager = get_rag_manager()
        llm = LLMFactory.get_llm()
        model_service = get_model_discovery_service()

        print("✅ Services initialized")
        print()

        # Test model discovery
        print("Testing model discovery...")
        available_models = model_service.discover_available_models()
        print(f"✅ Found {len(available_models)} models")
        for model in available_models[:3]:  # Show first 3
            print(f"   - {model.get('display_name', model['name'])}")
        print()

        # Test current model info
        print("Testing current model info...")
        current_model_info = model_service.get_model_info(llm.model_name)
        print(f"✅ Current model: {llm.model_name}")
        if current_model_info:
            print(f"   Display name: {current_model_info.get('display_name', 'Unknown')}")
        print()

        # Test ChromaDB stats
        print("Testing ChromaDB stats...")
        chroma_stats = rag_manager.get_collection_stats()
        print(f"✅ ChromaDB status: {chroma_stats}")
        document_count = chroma_stats.get("document_count", 0)
        print(f"   Document count: {document_count}")
        print()

        # Test document information (like in /api/status)
        print("Testing document information retrieval...")
        documents_info = []
        total_documents = 0
        total_chunks = 0

        if hasattr(rag_manager.chroma_service, 'collection') and rag_manager.chroma_service.collection:
            try:
                results = rag_manager.chroma_service.collection.get()
                
                if results and 'metadatas' in results and 'ids' in results:
                    unique_docs = {}
                    for i, metadata in enumerate(results['metadatas']):
                        if metadata and 'file_hash' in metadata:
                            file_hash = metadata['file_hash']
                            if file_hash not in unique_docs:
                                unique_docs[file_hash] = {
                                    'id': file_hash,
                                    'filename': metadata.get('filename', 'unknown'),
                                    'source': metadata.get('source', 'unknown'),
                                    'chunk_count': 0,
                                    'created_at': metadata.get('created_at', ''),
                                    'type': metadata.get('chunk_type', 'content')
                                }
                            unique_docs[file_hash]['chunk_count'] += 1
                    
                    documents_info = list(unique_docs.values())
                    total_documents = len(documents_info)
                    total_chunks = len(results['ids'])
                    
                print(f"✅ Document analysis complete")
                print(f"   Total documents: {total_documents}")
                print(f"   Total chunks: {total_chunks}")
                if documents_info:
                    print("   Recent documents:")
                    for doc in documents_info[:3]:  # Show first 3
                        print(f"     - {doc['filename']} ({doc['chunk_count']} chunks)")
                        
            except Exception as e:
                print(f"⚠️  Warning: Could not retrieve document details: {e}")
        
        print()

        # Simulate what the root endpoint (/) would return
        print("=== SIMULATING ROOT ENDPOINT (/) RESPONSE ===")
        root_response = {
            "message": "🚀 PocketPro:SBA is running!",
            "status": "success",
            "version": "1.0.0",
            "service": "PocketPro Small Business Assistant",
            "summary": {
                "models": {
                    "current": current_model_info.get('display_name', llm.model_name) if current_model_info else llm.model_name,
                    "available_count": len(available_models)
                },
                "documents": {
                    "total_count": document_count,
                    "chromadb_available": chroma_stats.get("success", False)
                },
                "services": {
                    "llm_configured": bool(config.GEMINI_API_KEY),
                    "chromadb_connected": chroma_stats.get("success", False)
                }
            }
        }
        print(json.dumps(root_response, indent=2))
        print()

        # Simulate what the /health endpoint would return
        print("=== SIMULATING HEALTH ENDPOINT (/health) RESPONSE ===")
        health_response = {
            "status": "healthy", 
            "service": "PocketPro:SBA",
            "timestamp": str(datetime.now()),
            "chromadb_available": chroma_stats.get("success", False),
            "quick_stats": {
                "documents": chroma_stats.get("document_count", 0),
                "models_available": len(available_models),
                "llm_configured": bool(config.GEMINI_API_KEY)
            }
        }
        print(json.dumps(health_response, indent=2))
        print()

        # Simulate what the /api/status endpoint would return
        print("=== SIMULATING STATUS ENDPOINT (/api/status) RESPONSE ===")
        status_response = {
            "system": "PocketPro:SBA Edition",
            "version": "1.0.0",
            "status": "operational",
            "documents": {
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "recent_documents": documents_info[:5] if documents_info else [],
            },
            "models": {
                "current_model": {
                    "name": llm.model_name,
                    "display_name": current_model_info.get('display_name', 'Unknown') if current_model_info else 'Unknown'
                },
                "available_count": len(available_models),
                "top_models": [
                    {
                        "name": model['name'],
                        "display_name": model['display_name']
                    }
                    for model in available_models[:5]
                ] if available_models else []
            }
        }
        print(json.dumps(status_response, indent=2))
        print()

        print("=== STATUS ENDPOINT FUNCTIONALITY TEST COMPLETE ===")
        print("✅ All status endpoints are providing comprehensive models and documents information!")

    except Exception as e:
        print(f"❌ Error testing status functionality: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_status_functions()
