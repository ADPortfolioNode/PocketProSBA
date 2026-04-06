import chromadb

print('=== Testing ChromaDB Client Patterns ===')

print('1. Testing EphemeralClient...')
try:
    client = chromadb.EphemeralClient()
    result = client.heartbeat()
    print(f'✓ EphemeralClient heartbeat: {result}')
except Exception as e:
    print(f'✗ EphemeralClient failed: {e}')

print('\n2. Testing HttpClient...')
try:
    client = chromadb.HttpClient(host='chromadb', port=8000)
    result = client.heartbeat()
    print(f'✓ HttpClient heartbeat: {result}')
except Exception as e:
    print(f'✗ HttpClient failed: {e}')

print('\n3. Testing PersistentClient...')
try:
    import os
    test_path = '/tmp/test_chroma'
    os.makedirs(test_path, exist_ok=True)
    client = chromadb.PersistentClient(path=test_path)
    result = client.heartbeat()
    print(f'✓ PersistentClient heartbeat: {result}')
except Exception as e:
    print(f'✗ PersistentClient failed: {e}')

print('\n=== Test Complete ===')
