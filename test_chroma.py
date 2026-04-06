#!/usr/bin/env python3

import sys
sys.path.append('/app')

def test_chromadb():
    print('Testing ChromaDB connection...')
    try:
        from src.services.chroma_service import ChromaService
        
        chroma_service = ChromaService()
        print('✓ ChromaService initialized successfully')
        
        # Test client connection
        if hasattr(chroma_service, 'client') and chroma_service.client:
            print('✓ ChromaDB client is available')
            
            # Test heartbeat
            heartbeat = chroma_service.client.heartbeat()
            print(f'✓ ChromaDB heartbeat: {heartbeat}')
            
            # Test getting embedding info
            info = chroma_service.get_embedding_info()
            print(f'✓ Embedding info: {info}')
            
            # Test basic collection access if available
            if hasattr(chroma_service, 'collection') and chroma_service.collection:
                count = chroma_service.collection.count()
                print(f'✓ Collection access successful, document count: {count}')
            else:
                print('! Collection not initialized (this is expected on first run)')
                
        else:
            print('✗ ChromaDB client not available')
            return False
            
        print('✓ All ChromaDB tests passed!')
        return True
        
    except Exception as e:
        print(f'✗ ChromaDB test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_chromadb()
    sys.exit(0 if success else 1)
