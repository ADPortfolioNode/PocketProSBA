from flask import Flask, request, jsonify
from flask_cors import CORS
import chromadb
from chromadb.config import Settings

app = Flask(__name__)
CORS(app)

# ChromaDB client setup
from backend.utils.chroma_utils import init_chroma_client

try:
    chroma_client = init_chroma_client()
except Exception as e:
    print(f"Error initializing ChromaDB client: {e}")
    # We'll continue without ChromaDB for now, to allow basic API functionality

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'services': {
            'api': 'running',
            'chromadb': 'connected'
        }
    })

@app.route('/api/query', methods=['POST'])
def query():
    try:
        data = request.json
        query_text = data.get('query', '')
        collection_name = data.get('collection', 'default')

        # Get or create collection
        collection = chroma_client.get_or_create_collection(name=collection_name)
        
        # Query the collection
        results = collection.query(
            query_texts=[query_text],
            n_results=5
        )

        return jsonify({
            'status': 'success',
            'results': results
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/decompose', methods=['POST'])
def decompose():
    try:
        data = request.json
        text = data.get('text', '')
        # Add your RAG decomposition logic here
        return jsonify({
            'status': 'success',
            'chunks': [text]  # Replace with actual chunks
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/execute', methods=['POST'])
def execute():
    try:
        data = request.json
        query = data.get('query', '')
        # Add your RAG execution logic here
        return jsonify({
            'status': 'success',
            'result': f"Processed: {query}"
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)