import sys
sys.path.append('/app')

def debug_chroma():
    print('=== ChromaDB Debug ===')
    try:
        from src.services.chroma_service import ChromaService
        print('✓ Import successful')
        
        service = ChromaService()
        print('✓ Service created')
        
        print('Has client:', hasattr(service, 'client'))
        print('Client value:', getattr(service, 'client', None))
        print('Has _chroma_available:', hasattr(service, '_chroma_available'))
        print('_chroma_available value:', getattr(service, '_chroma_available', None))
        
        # Test basic connection if client exists
        if hasattr(service, 'client') and service.client is not None:
            try:
                heartbeat = service.client.heartbeat()
                print(f'✓ Heartbeat successful: {heartbeat}')
            except Exception as hb_error:
                print(f'✗ Heartbeat failed: {hb_error}')
        else:
            print('✗ No client available')
            
    except Exception as e:
        print(f'✗ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_chroma()
