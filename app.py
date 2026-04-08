import os
from flask import jsonify
from backend.app import create_app

app = create_app()
chroma_client = None
chroma_client_error = None

@app.route('/api/health')
def health_check():
    global chroma_client, chroma_client_error

    services = {'api': 'running'}

    if chroma_client is None and chroma_client_error is None:
        try:
            from backend.utils.chroma_utils import init_chroma_client
            chroma_client = init_chroma_client()
        except Exception as e:
            chroma_client_error = str(e)
            chroma_client = None
            print(f"Error initializing ChromaDB client: {e}")

    if chroma_client is None:
        services['chromadb'] = 'unavailable'
        if chroma_client_error:
            services['chromadb_error'] = chroma_client_error
    else:
        try:
            chroma_client.get_or_create_collection(name='default_collection')
            services['chromadb'] = 'connected'
        except Exception as e:
            services['chromadb'] = 'disconnected'
            services['chromadb_error'] = str(e)

    return jsonify({
        'status': 'healthy',
        'services': services
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
