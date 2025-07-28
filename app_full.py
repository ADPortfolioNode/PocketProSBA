from flask import send_from_directory
# --- BUILD/DEPLOYMENT REQUIREMENTS FILES ---
#
# IMPORTANT: This backend is built and deployed using the following files:
#   - Docker/Render.com: requirements-full.txt (NOT requirements.txt)
#   - Local development: requirements.txt (may be missing packages)
#
# To match production, always install dependencies with:
#     pip install -r requirements-full.txt
#
# See project documentation for details.

from dotenv import load_dotenv
import os
import logging
import time
start_time = time.time()
import hashlib
import re
import chromadb  # (See note above: installed via requirements-full.txt in Docker/Render)
import json
import math
from collections import Counter
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import math
import sys
from functools import wraps


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Handle ChromaDB import gracefully
try:
    from chromadb.config import Settings
    from chromadb.client import Client
    CHROMADB_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ChromaDB not available: {e}")
    CHROMADB_AVAILABLE = False
    Settings = None
    Client = None


# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
application = app  # Expose Flask app as 'application' for Gunicorn compatibility

def create_app():
    app = Flask(__name__)

    # --- Production Hardening Additions ---
    # Load required environment variables from .env
    REQUIRED_ENV_VARS = ["GEMINI_API_KEY", "SECRET_KEY"]

REQUIRED_ENV_VARS = ["GEMINI_API_KEY", "SECRET_KEY"]

def check_required_env_vars():
    missing = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        sys.exit(1)
check_required_env_vars()

# --- CORS: Allow all origins and headers for all routes ---
def setup_cors(app):
    CORS(app, resources={r"/*": {"origins": ["https://pocketprosba-frontend.onrender.com", "http://localhost:3000"]}}, supports_credentials=True, allow_headers="*")

app = Flask(__name__)
setup_cors(app)

application = app  # Expose Flask app as 'application' for Gunicorn compatibility

# Request logging
@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.path} | IP: {request.remote_addr} | Headers: {dict(request.headers)} | Body: {request.get_data(as_text=True)}")

# Global error handler for 500
@app.errorhandler(500)
def handle_500(e):
    logger.error(f"Internal server error: {str(e)}", exc_info=True)
    return jsonify({"error": "Internal server error"}), 500

# Global error handler for 404
@app.errorhandler(404)
def handle_404(e):
    return jsonify({"error": "Not found"}), 404

# --- API Health Endpoint for Frontend ---
@app.route('/api/health', methods=['GET', 'HEAD'])
def api_health_check():
    """Health check endpoint for monitoring (frontend expects /api/health)"""
    global rag_system_available
    response = jsonify({
        'status': 'healthy',
        'service': 'PocketPro SBA',
        'version': '1.0.0',
        'rag_status': 'available' if rag_system_available else 'unavailable',
        'document_count': vector_store.count()
    })
    return response

# --- API Endpoint Registry for Frontend ---
@app.route('/api/registry', methods=['GET'])
def api_registry():
    """Return a registry of available API endpoints for the frontend to discover capabilities."""
    # Base URL for API endpoints, configurable via environment variable
    base_url = os.environ.get('API_BASE_URL', '').rstrip('/')
    # Registry keys must match frontend usage exactly
    registry = {
        "documents": f"{base_url}/api/documents" if base_url else "/api/documents",
        "documents_add": f"{base_url}/api/documents/add" if base_url else "/api/documents/add",
        "uploads": f"{base_url}/api/uploads" if base_url else "/api/uploads",
        "upload": f"{base_url}/api/uploads" if base_url else "/api/uploads",  # alias for upload (frontend expects 'upload')
        "resources": f"{base_url}/api/resources" if base_url else "/api/resources",  # now points to new /api/resources endpoint
        "search": f"{base_url}/api/search" if base_url else "/api/search",
        "chat": f"{base_url}/api/chat" if base_url else "/api/chat",
        "rag": f"{base_url}/api/rag" if base_url else "/api/rag",
        "programs_rag": f"{base_url}/api/programs/<program_id>/rag" if base_url else "/api/programs/<program_id>/rag",
        "resources_rag": f"{base_url}/api/resources/<resource_id>/rag" if base_url else "/api/resources/<resource_id>/rag",
        "collections_stats": f"{base_url}/api/collections/stats" if base_url else "/api/collections/stats",
        "api_health": f"{base_url}/api/health" if base_url else "/api/health",
        "health": f"{base_url}/api/health" if base_url else "/api/health",
        "status": f"{base_url}/api/status" if base_url else "/api/status",
        "startup": f"{base_url}/startup" if base_url else "/startup",
        "info": f"{base_url}/api/info" if base_url else "/api/info",
        "models": f"{base_url}/api/models" if base_url else "/api/models",
        "chromadb_health": f"{base_url}/api/chromadb/health" if base_url else "/api/chromadb/health",
        "chat": f"{base_url}/api/chat" if base_url else "/api/chat"
    }
    return jsonify(registry), 200

# --- ChromaDB health endpoint ---
@app.route('/api/chromadb/health', methods=['GET'])
def chromadb_health():
    """Health/status endpoint for ChromaDB vector DB"""
    status = {
        "chroma_enabled": CHROMADB_AVAILABLE,
        "client_initialized": CHROMADB_AVAILABLE and chroma_client is not None,
        "persist_directory": getattr(chroma_client, 'persist_directory', None) if CHROMADB_AVAILABLE and chroma_client is not None else None
    }
    return jsonify(status)
# --- New: /api/resources endpoint for frontend resource loading ---
@app.route('/api/resources', methods=['GET'])
def get_resources():
    """Return a list of resources for the frontend sidebar (mirrors /api/documents for now)"""
    try:
        documents = vector_store.get_all_documents()
        # Optionally, filter/transform documents to match frontend resource expectations
        resources = [
            {
                'id': doc['id'],
                'title': doc['metadata'].get('title', doc['id']),
                'description': doc['metadata'].get('description', doc['text'][:120] + ("..." if len(doc['text']) > 120 else "")),
                'metadata': doc['metadata']
            }
            for doc in documents
        ]
        return jsonify({'resources': resources, 'count': len(resources)})
    except Exception as e:
        logger.error(f"Error getting resources: {str(e)}")
        return jsonify({'resources': [], 'count': 0, 'error': str(e)}), 500

# Initialize ChromaDB client
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

# --- Advanced Assistant/Session/Task Architecture Additions ---
import threading

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

try:
    from flask_socketio import SocketIO, emit
    import gevent
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    SocketIO = None

# Initialize Flask-SocketIO with gevent async mode if available, else fallback
if SOCKETIO_AVAILABLE and SocketIO is not None:
    try:
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')
    except Exception as e:
        # Fallback to threading if gevent not available or invalid
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
else:
    socketio = None

# Redis-backed ConversationStore with fallback to in-memory
class ConversationStore:
    def __init__(self, redis_url=None):
        self.use_redis = False
        self.redis_url = redis_url or os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        if REDIS_AVAILABLE:
            try:
                self.r = redis.Redis.from_url(self.redis_url)
                self.r.ping()
                self.use_redis = True
            except Exception as e:
                logger.warning(f"Redis unavailable: {e}. Using in-memory store.")
                self.r = None
        else:
            self.r = None
        self.memory_store = {}  # {session_id: [messages]}
        self.lock = threading.Lock()

    def get(self, session_id):
        if self.use_redis:
            data = self.r.get(f"conv:{session_id}")
            if data:
                return json.loads(data)
            return []
        else:
            with self.lock:
                return self.memory_store.get(session_id, []).copy()

    def append(self, session_id, message):
        if self.use_redis:
            history = self.get(session_id)
            history.append(message)
            self.r.set(f"conv:{session_id}", json.dumps(history))
        else:
            with self.lock:
                self.memory_store.setdefault(session_id, []).append(message)

    def clear(self, session_id):
        if self.use_redis:
            self.r.delete(f"conv:{session_id}")
        else:
            with self.lock:
                self.memory_store.pop(session_id, None)

conversation_store = ConversationStore()

# --- TaskAssistant and StepAssistant stubs ---
class TaskAssistant:
    def __init__(self, store):
        self.store = store
        # TODO: Implement task decomposition, execution, validation

    def decompose(self, user_message):
        # TODO: Use LLM to decompose user_message into steps
        return []

    def execute(self, task_id):
        # TODO: Execute steps for a given task_id
        return []

    def validate(self, task_id):
        # TODO: Validate results for a given task_id
        return True

# StepAssistant stubs (to be implemented)
class SearchAgent:
    pass
class FileAgent:
    pass
class FunctionAgent:
    pass

# Intent classification stub
class Concierge:
    def __init__(self, store):
        self.store = store

    def classify_intent(self, message):
        # TODO: Use LLM to classify intent
        return "unknown"

    def handle_message(self, session_id, message):
        # TODO: Route message to correct workflow
        return {"response": "Not implemented yet."}

concierge = Concierge(conversation_store)
task_assistant = TaskAssistant(conversation_store)
# --- End Advanced Additions ---

# Simple in-memory vector store
class SimpleVectorStore:
    """Simple in-memory vector store for RAG functionality"""
    
    def __init__(self):
        self.documents = {}
        self.embeddings = {}
        self.embedding_function = SimpleEmbeddingFunction()
    
    def add_document(self, doc_id, text, metadata=None):
        """Add a document to the store"""
        self.documents[doc_id] = {
            'text': text,
            'metadata': metadata or {}
        }
        # Generate embedding
        embedding = self.embedding_function([text])[0]
        self.embeddings[doc_id] = embedding
        return doc_id
    
    def search(self, query, n_results=5):
        """Search for similar documents"""
        if not self.documents:
            return {'documents': [], 'metadatas': [], 'distances': [], 'ids': []}
        
        # Generate query embedding
        query_embedding = self.embedding_function([query])[0]
        
        # Calculate similarities
        similarities = []
        for doc_id, doc_embedding in self.embeddings.items():
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            similarities.append((doc_id, similarity))
        
        # Sort by similarity (higher is better)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Get top results
        top_results = similarities[:n_results]
        
        # Format results
        documents = []
        metadatas = []
        distances = []
        ids = []
        
        for doc_id, similarity in top_results:
            doc = self.documents[doc_id]
            documents.append(doc['text'])
            metadatas.append(doc['metadata'])
            distances.append(1.0 - similarity)  # Convert similarity to distance
            ids.append(doc_id)
        
        return {
            'documents': [documents],
            'metadatas': [metadatas], 
            'distances': [distances],
            'ids': [ids]
        }
    
    def delete_document(self, doc_id):
        """Delete a document"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            del self.embeddings[doc_id]
            return True
        return False
    
    def count(self):
        """Get document count"""
        return len(self.documents)
    
    def get_all_documents(self):
        """Get all documents"""
        return [
            {
                'id': doc_id,
                'text': doc['text'],
                'metadata': doc['metadata']
            }
            for doc_id, doc in self.documents.items()
        ]
    
    def _cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0
        
        return dot_product / (magnitude1 * magnitude2)

class SimpleEmbeddingFunction:
    """Simple embedding function that works without external dependencies"""
    
    def __call__(self, texts):
        """Convert texts to simple embeddings using TF-IDF style approach"""
        embeddings = []
        
        # Create a vocabulary from all texts
        all_words = set()
        text_words = []
        
        for text in texts:
            words = re.findall(r'\b\w+\b', str(text).lower())
            text_words.append(words)
            all_words.update(words)
        
        # Limit vocabulary size
        vocab = sorted(list(all_words))[:384]
        
        for words in text_words:
            word_counts = Counter(words)
            total_words = len(words)
            
            embedding = []
            for word in vocab:
                tf = word_counts.get(word, 0) / max(total_words, 1)
                embedding.append(float(tf))
            
            # Pad to 384 dimensions
            while len(embedding) < 384:
                embedding.append(0.0)
            
            embeddings.append(embedding[:384])
        
        return embeddings

# Global vector store
vector_store = SimpleVectorStore()
rag_system_available = True

UPLOADS_DIR = os.environ.get('UPLOAD_FOLDER', './uploads')

@app.route('/api/uploads', methods=['GET'])
def list_uploaded_files():
    """List files in the uploads directory"""
    try:
        files = os.listdir(UPLOADS_DIR)
        file_info = []
        for fname in files:
            fpath = os.path.join(UPLOADS_DIR, fname)
            if os.path.isfile(fpath):
                stat = os.stat(fpath)
                file_info.append({
                    'filename': fname,
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
        return jsonify({'files': file_info, 'count': len(file_info)})
    except Exception as e:
        logger.error(f"Error listing uploads: {e}")
        return jsonify({'error': str(e), 'files': [], 'count': 0}), 500

def initialize_rag_system():
    """Initialize the RAG system and index new uploads"""
    global vector_store, rag_system_available
    
    try:
        # Index new files in uploads directory
        files = os.listdir(UPLOADS_DIR)
        for fname in files:
            fpath = os.path.join(UPLOADS_DIR, fname)
            if os.path.isfile(fpath):
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                doc_id = f"upload_{fname}"
                # Avoid duplicate indexing in in-memory vector store
                if not any(doc.get('id') == doc_id for doc in vector_store.get_all_documents()):
                    vector_store.add_document(doc_id, text, {'source': 'upload', 'filename': fname})
                    # Also add to ChromaDB if available
                    if CHROMADB_AVAILABLE and chroma_client is not None:
                        try:
                            chroma_client.add(
                                documents=[text],
                                metadatas=[{'source': 'upload', 'filename': fname}],
                                ids=[doc_id]
                            )
                            logger.info(f"Document {doc_id} added to ChromaDB.")
                        except Exception as e:
                            logger.warning(f"Failed to add document {doc_id} to ChromaDB: {e}")
        
        # Test the vector store
        test_id = vector_store.add_document(
            "test_init",
            "This is a test document for RAG system initialization.",
            {"type": "test", "timestamp": int(time.time())}
        )
        
        # Test search
        results = vector_store.search("test document", n_results=1)
        
        # Clean up test document
        vector_store.delete_document(test_id)
        
        logger.info("✅ RAG system initialized successfully")
        rag_system_available = True
        

        # Add an initial document to the vector store and ChromaDB for AI self-awareness and project context
        initial_doc_id = 'ai_self_awareness'
        initial_doc_text = (
            'I am the AI assistant for the PocketPro SBA project. '
            'My purpose is to help users interact with the Small Business Administration (SBA) resources, answer questions, and assist with RAG (Retrieval-Augmented Generation) workflows. '
            'I am aware of my project context and can provide guidance on using the system. '
            'For detailed project instructions and guidelines, see the INSTRUCTIONS.md file: '
            'https://pocketprosba-backend.onrender.com/static/INSTRUCTIONS.md'
        )
        initial_doc_metadata = {
            'source': 'self_awareness',
            'type': 'project_info',
            'category': 'meta',
            'link': 'https://pocketprosba-backend.onrender.com/static/INSTRUCTIONS.md',
            'description': 'AI assistant self-awareness and project context.'
        }
        vector_store.add_document(initial_doc_id, initial_doc_text, initial_doc_metadata)
        # If ChromaDB is available, add to ChromaDB as well
        if CHROMADB_AVAILABLE and chroma_client is not None:
            try:
                chroma_client.add(
                    documents=[initial_doc_text],
                    metadatas=[initial_doc_metadata],
                    ids=[initial_doc_id]
                )
                logger.info("Initial self-awareness document added to ChromaDB.")
            except Exception as e:
                logger.warning(f"Failed to add initial doc to ChromaDB: {e}")

        # Add some sample SBA documents
        sample_docs = [
            {
                'id': 'sba_loans_guide',
                'text': 'The Small Business Administration (SBA) provides various loan programs to help small businesses start and grow. SBA loans offer favorable terms and lower down payments than conventional business loans.',
                'metadata': {'source': 'sba_guide', 'type': 'loans', 'category': 'financing'}
            },
            {
                'id': 'business_plan_guide', 
                'text': 'A business plan is a written document that describes your business concept, how you will make money, and how you will manage the business. It is essential for securing funding from lenders and investors.',
                'metadata': {'source': 'business_guide', 'type': 'planning', 'category': 'startup'}
            },
            {
                'id': 'sba_504_loans',
                'text': 'SBA 504 loans are specifically designed for purchasing real estate or equipment. These loans provide long-term, fixed-rate financing for major fixed assets that promote business growth.',
                'metadata': {'source': 'loan_programs', 'type': 'real_estate', 'category': 'financing'}
            }
        ]
        for doc in sample_docs:
            vector_store.add_document(doc['id'], doc['text'], doc['metadata'])
        logger.info(f"✅ Added {len(sample_docs) + 1} sample documents (including self-awareness doc)")
        return True
        
    except Exception as e:
        logger.error(f"❌ RAG system initialization failed: {e}")
        rag_system_available = False
        return False

def startup():
    """Initialize all services on startup"""
    logger.info("🚀 Initializing PocketPro SBA RAG application...")
    
    try:
        # Initialize RAG system
        rag_available = initialize_rag_system()
        
        startup_results = {
            'startup_completed': True,
            'rag_status': 'available' if rag_available else 'unavailable',
            'available_models': ['simple-rag'] if rag_available else [],
            'vector_store_available': rag_system_available,
            'document_count': vector_store.count(),
            'embedding_model': 'simple-tfidf'
        }
        
        logger.info(f"🎯 Startup Results: {startup_results}")
        return startup_results
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        return {
            'startup_completed': False,
            'error': str(e),
            'rag_status': 'unavailable',
            'available_models': [],
            'vector_store_available': False,
            'document_count': 0
        }

from src.services.startup_service import initialize_app_on_startup

# Initialize on startup
startup_result = initialize_app_on_startup()

## ...existing code...
## Removed the '/' JSON endpoint so the catch-all route serves React frontend

# Removed alias routes for /registry and /health to eliminate redundancy

# Log the configured port - CRITICAL for Render.com

# For Render.com, we need to expose the app for Gunicorn to find
application = app

# Create socketio for compatibility with run.py
socketio = None

import requests

@app.route('/api/info', methods=['GET'])
def api_info():
    """Return basic server info for frontend system resources tab"""
    info = {
        'version': '1.0.0',
        'model': 'PocketPro SBA',
        'status': 'running',
        'uptime': time.time() - start_time if 'start_time' in globals() else None,
        'description': 'PocketPro SBA backend server info endpoint'
    }
    return jsonify(info)
