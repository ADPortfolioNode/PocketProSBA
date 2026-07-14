#!/usr/bin/env python3
import sys
import os
sys.path.append('.')

print('=== PocketPro SBA Concierge Assistant Diagnostic ===')
print()

# Test basic imports
try:
    from services.chroma import ChromaService
    from services.rag import RAGManager
    from assistants.concierge import Concierge
    print('✅ All imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)

print()
print('=== Testing ChromaDB Service ===')
try:
    chroma_service = ChromaService()
    if chroma_service.is_available():
        print('✅ ChromaDB service available')
        stats = chroma_service.get_collection_stats()
        print(f'📊 Collection stats: {stats}')
    else:
        print('❌ ChromaDB service unavailable')
        print('   This could be due to:')
        print('   - ChromaDB server not running')
        print('   - Network connectivity issues')
        print('   - Authentication problems')
except Exception as e:
    print(f'❌ ChromaDB error: {e}')

print()
print('=== Testing RAG Manager ===')
try:
    rag_manager = RAGManager(chroma_service=chroma_service)
    if rag_manager.is_available():
        print('✅ RAG manager available')
        count = rag_manager.get_document_count()
        print(f'📄 Document count: {count}')
    else:
        print('❌ RAG manager unavailable')
        print('   This could be due to:')
        print('   - ChromaDB service unavailable')
        print('   - Collection initialization issues')
        print('   - Embedding model problems')
except Exception as e:
    print(f'❌ RAG manager error: {e}')

print()
print('=== Testing Concierge Assistant ===')
try:
    concierge = Concierge()
    if concierge.rag_manager:
        print('✅ Concierge RAG manager initialized')
        # Test a simple query
        result = concierge.handle_message('Hello, what can you help me with?')
        print(f'🤖 Concierge response: {result.get("text", "No response")[:100]}...')
    else:
        print('❌ Concierge RAG manager not initialized')
        print('   This could be due to:')
        print('   - RAG manager unavailable')
        print('   - Import issues in concierge.py')
except Exception as e:
    print(f'❌ Concierge error: {e}')

print()
print('=== Environment Check ===')
print(f'CHROMA_HOST: {os.environ.get("CHROMA_HOST", "localhost")}')
print(f'CHROMA_PORT: {os.environ.get("CHROMA_PORT", "8000")}')
