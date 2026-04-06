import os
from flask import jsonify
from wsgi import create_app
from backend.utils.chroma_utils import init_chroma_client

create_app = create_app
app = create_app()

try:
    chroma_client = init_chroma_client()
except Exception as e:
    chroma_client = None
    print(f"Error initializing ChromaDB client: {e}")

@app.route('/api/health')
def health_check():
    services = {'api': 'running'}

    if chroma_client is None:
        services['chromadb'] = 'unavailable'
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
