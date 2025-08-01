import os
import logging
import time
import json
import math
import sys
from collections import Counter
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Handle ChromaDB import gracefully
try:
    from chromadb.config import Settings
    from chromadb.api.fastapi import FastAPI
    from chromadb.api.client import Client
    CHROMADB_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ChromaDB not available: {e}", file=sys.stderr)
    CHROMADB_AVAILABLE = False
    Settings = None
    Client = None

# Import flask_socketio and define SOCKETIO_AVAILABLE before usage
try:
    from flask_socketio import SocketIO
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False

app = Flask(__name__)
app.config.from_object(type('Config', (), {
    "SECRET_KEY": os.environ.get('SECRET_KEY') or 'a-default-secret-key-for-development',
    "GEMINI_API_KEY": os.environ.get('GEMINI_API_KEY')
}))

# Configure CORS
if os.environ.get("FLASK_ENV", "production") == "production":
    CORS(app, origins=[os.environ.get("CORS_ORIGIN", "*")])
else:
    CORS(app)

# Initialize SocketIO
if SOCKETIO_AVAILABLE:
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
else:
    socketio = None

# Use socketio.run to start the app if socketio is available
def run_app():
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "production") == "development"
    if socketio:
        socketio.run(app, host="0.0.0.0", port=port, debug=debug)
    else:
        app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)

if __name__ == "__main__":
    run_app()

# Simple embedding function
class SimpleEmbeddingFunction:
    def __call__(self, texts):
        embeddings = []
        all_words = set()
        text_words = []
        for text in texts:
            words = [w.lower() for w in text.split()]
            text_words.append(words)
            all_words.update(words)
        vocab = sorted(list(all_words))[:384]
        for words in text_words:
            word_counts = Counter(words)
            total_words = len(words)
            embedding = [float(word_counts.get(word, 0) / max(total_words, 1)) for word in vocab]
            while len(embedding) < 384:
                embedding.append(0.0)
            embeddings.append(embedding[:384])
        return embeddings

# Simple in-memory vector store fallback
class SimpleVectorStore:
    def __init__(self):
        self.documents = {}
        self.embeddings = {}
        self.embedding_function = SimpleEmbeddingFunction()

    def add_document(self, doc_id, text, metadata=None):
        self.documents[doc_id] = {'text': text, 'metadata': metadata or {}}
        embedding = self.embedding_function([text])[0]
        self.embeddings[doc_id] = embedding
        return doc_id

    def _cosine_similarity(self, vec1, vec2):
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(a * a for a in vec1))
        mag2 = math.sqrt(sum(a * a for a in vec2))
        if mag1 == 0 or mag2 == 0:
            return 0
        return dot_product / (mag1 * mag2)

    def search(self, query, n_results=5):
        if not self.documents:
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]], 'ids': [[]]}
        query_embedding = self.embedding_function([query])[0]
        similarities = [(doc_id, self._cosine_similarity(query_embedding, emb)) for doc_id, emb in self.embeddings.items()]
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_results = similarities[:n_results]
        documents, metadatas, distances, ids = [], [], [], []
        for doc_id, sim in top_results:
            doc = self.documents[doc_id]
            documents.append(doc['text'])
            metadatas.append(doc['metadata'])
            distances.append(1.0 - sim)
            ids.append(doc_id)
        return {'documents': [documents], 'metadatas': [metadatas], 'distances': [distances], 'ids': [ids]}

    def count(self):
        return len(self.documents)

# Initialize vector store and RAG availability
vector_store = SimpleVectorStore()
rag_system_available = True

# Initialize ChromaDB client if available
if CHROMADB_AVAILABLE:
    try:
        chroma_client = Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="./chroma_storage"
        ))
        logger.info("ChromaDB client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB client: {e}")
        chroma_client = None
        CHROMADB_AVAILABLE = False
else:
    chroma_client = None
    logger.warning("ChromaDB not available, using fallback vector store")

# API endpoints

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'PocketPro SBA',
        'version': '1.0.0',
        'rag_status': 'available' if rag_system_available else 'unavailable',
        'document_count': vector_store.count()
    })

@app.route('/api/registry', methods=['GET'])
def api_registry():
    # Return list of available endpoints
    endpoints = [
        '/health',
        '/api/registry',
        '/api/documents',
        '/api/documents/add',
        '/api/search',
        '/api/chat',
        '/api/rag'
    ]
    return jsonify({'endpoints': endpoints})

@app.route('/api/documents', methods=['GET'])
def get_documents():
    try:
        documents = vector_store.documents
        return jsonify({'documents': documents, 'count': len(documents)})
    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/add', methods=['POST'])
def add_document():
    if not rag_system_available:
        return jsonify({'error': 'RAG system not available'}), 503
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No document text provided'}), 400
    doc_id = data.get('id') or f'doc_{int(time.time()*1000)}'
    text = data['text']
    metadata = data.get('metadata', {})
    vector_store.add_document(doc_id, text, metadata)
    return jsonify({'success': True, 'document_id': doc_id})

@app.route('/api/search', methods=['POST'])
def semantic_search():
    if not rag_system_available:
        return jsonify({'error': 'RAG system not available'}), 503
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'error': 'No query provided'}), 400
    query = data['query']
    n_results = min(int(data.get('n_results', 5)), 20)
    results = vector_store.search(query, n_results)
    return jsonify({'query': query, 'results': results})

@app.route('/api/chat', methods=['POST'])
def rag_chat():
    if not rag_system_available:
        return jsonify({'error': 'RAG system not available'}), 503
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400
    message = data['message']
    # For simplicity, echo the message with a placeholder response
    response = f"Echo: {message}"
    return jsonify({'query': message, 'response': response})

@app.route('/api/rag', methods=['POST'])
def rag_query():
    if not CHROMADB_AVAILABLE or chroma_client is None:
        return jsonify({'error': 'ChromaDB not available'}), 503
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'error': 'No query provided'}), 400
    query = data['query']
    n_results = int(data.get('n_results', 5))
    try:
        results = chroma_client.query(query_text=query, n_results=n_results)
        return jsonify({'query': query, 'results': results})
    except Exception as e:
        logger.error(f"ChromaDB query error: {e}")
        return jsonify({'error': str(e)}), 500

# Serve React frontend catch-all route
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    # Serve React build files from /build folder to match React default build output
    build_dir = os.path.join(app.root_path, 'build')
    if path != "" and os.path.exists(os.path.join(build_dir, path)):
        return send_from_directory(build_dir, path)
    else:
        return send_from_directory(build_dir, 'index.html')

def run_app():
    port = int(os.environ.get("PORT", 10000))
    debug = os.environ.get("FLASK_ENV", "production") == "development"
    if socketio:
        socketio.run(app, host="0.0.0.0", port=port, debug=debug)
    else:
        app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)

if __name__ == "__main__":
    run_app()
