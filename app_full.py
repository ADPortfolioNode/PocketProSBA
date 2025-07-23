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


# --- Production Hardening Additions ---
# Load required environment variables from .env
REQUIRED_ENV_VARS = ["GEMINI_API_KEY", "SECRET_KEY"]

def check_required_env_vars():
    missing = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        sys.exit(1)
check_required_env_vars()

# --- CORS: Allow all origins and headers for all routes ---
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True, allow_headers="*")

# Request logging
@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.path} | IP: {request.remote_addr}")

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
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'GET,HEAD,OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response

# --- API Endpoint Registry for Frontend ---
@app.route('/api/registry', methods=['GET'])
def api_registry():
    """Return a registry of available API endpoints for the frontend to discover capabilities."""
    # Registry keys must match frontend usage exactly
    return jsonify({
        "documents": "/api/documents",
        "documents_add": "/api/documents/add",
        "uploads": "/api/uploads",
        "upload": "/api/uploads",  # alias for upload (frontend expects 'upload')
        "resources": "/api/resources",  # now points to new /api/resources endpoint
        "search": "/api/search",
        "chat": "/api/chat",
        "rag": "/api/rag",
        "programs_rag": "/api/programs/<program_id>/rag",
        "resources_rag": "/api/resources/<resource_id>/rag",
        "collections_stats": "/api/collections/stats",
        "api_health": "/api/health",
        "health": "/health",
        "status": "/api/status",
        "startup": "/startup",
        "info": "/api/info",
        "models": "/api/models",
        "chromadb_health": "/api/chromadb/health"
    }), 200

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

# Add /registry and /health routes for frontend compatibility (return same as /api/registry and /api/health)
@app.route('/registry', methods=['GET'])
def registry_alias():
    return api_registry()

@app.route('/health', methods=['GET', 'HEAD'])
def health_alias():
    return api_health_check()

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

try:
    from flask_socketio import SocketIO, emit
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False

# Initialize Flask-SocketIO
if SOCKETIO_AVAILABLE:
    socketio = SocketIO(app, cors_allowed_origins="*")
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

@app.route('/health', methods=['GET', 'HEAD'])
def health_check():
    """Health check endpoint for monitoring"""
    global rag_system_available
    response = jsonify({
        'status': 'healthy',
        'service': 'PocketPro SBA',
        'version': '1.0.0',
        'rag_status': 'available' if rag_system_available else 'unavailable',
        'document_count': vector_store.count()
    })
    # Add CORS headers explicitly for all methods
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'GET,HEAD,OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response

@app.route('/api/info', methods=['GET'])
def get_system_info():
    """Get system information"""
    return jsonify({
        'service': 'PocketPro SBA',
        'version': '1.0.0',
        'status': 'operational',
        'rag_status': 'available' if rag_system_available else 'unavailable',
        'vector_store': 'simple-memory',
        'document_count': vector_store.count()
    })

@app.route('/api/models', methods=['GET'])
def get_available_models():
    """Get available AI models"""
    return jsonify({'models': ['simple-rag']})

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Get all documents"""
    try:
        documents = vector_store.get_all_documents()
        return jsonify({
            'documents': documents,
            'count': len(documents),
            'rag_status': 'available'
        })
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        return jsonify({
            'documents': [],
            'count': 0,
            'rag_status': 'unavailable'
        })

@app.route('/api/documents/add', methods=['POST'])
def add_document():
    """Add a new document to the vector database"""
    if not rag_system_available:
        return jsonify({'error': 'RAG system not available'}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        document_text = data.get('text', '')
        document_id = data.get('id')
        metadata = data.get('metadata', {})
        
        if not document_text:
            return jsonify({'error': 'Document text is required'}), 400
        
        # Generate ID if not provided
        if not document_id:
            document_id = f'doc_{int(time.time() * 1000)}'
        
        # Add timestamp to metadata
        metadata.update({
            'added_at': int(time.time()),
            'content_length': len(document_text),
            'source': 'api_upload'
        })
        
        # Add to vector store
        vector_store.add_document(document_id, document_text, metadata)
        
        logger.info(f"✅ Document added: {document_id}")
        return jsonify({
            'success': True,
            'document_id': document_id,
            'message': 'Document added successfully',
            'metadata': metadata
        })
        
    except Exception as e:
        logger.error(f"Error adding document: {str(e)}")
        return jsonify({'error': f'Failed to add document: {str(e)}'}), 500

@app.route('/api/search', methods=['POST'])
def semantic_search():
    """Perform semantic search on documents"""
    if not rag_system_available:
        return jsonify({'error': 'RAG system not available'}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        query = data.get('query', '')
        n_results = min(int(data.get('n_results', 5)), 20)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Perform search
        results = vector_store.search(query, n_results=n_results)
        
        # Format results
        formatted_results = []
        if results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'content': doc,
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i],
                    'relevance_score': 1 - results['distances'][0][i]
                })
        
        return jsonify({
            'query': query,
            'results': formatted_results,
            'count': len(formatted_results),
            'search_time': time.time()
        })
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/api/chat', methods=['POST'])
def rag_chat():
    """RAG-powered chat endpoint"""
    if not rag_system_available:
        return jsonify({'error': 'RAG system not available'}), 503
    
    try:
        data = request.get_json(force=True, silent=True)
        logger.info(f"/api/chat request data: {data}")
        if not data or not isinstance(data, dict):
            logger.error("/api/chat: No JSON data or invalid format received.")
            return jsonify({'error': 'No JSON data provided or invalid format'}), 400

        user_query = data.get('message', '')
        if not user_query:
            logger.error("/api/chat: 'message' field missing in request data.")
            return jsonify({'error': 'Message is required'}), 400

        # Retrieve relevant documents
        search_results = vector_store.search(user_query, n_results=3)

        # Build context and sources
        context_parts = []
        sources = []

        if 'documents' in search_results and search_results['documents'] and search_results['documents'][0]:
            for i, doc in enumerate(search_results['documents'][0]):
                context_parts.append(f"Source {i+1}: {doc}")
                sources.append({
                    'id': search_results['ids'][0][i] if 'ids' in search_results and search_results['ids'] and len(search_results['ids'][0]) > i else None,
                    'content': doc[:200] + "..." if len(doc) > 200 else doc,
                    'metadata': search_results['metadatas'][0][i] if 'metadatas' in search_results and search_results['metadatas'] and len(search_results['metadatas'][0]) > i else None,
                    'relevance': 1 - search_results['distances'][0][i] if 'distances' in search_results and search_results['distances'] and len(search_results['distances'][0]) > i else None
                })

        # Generate response
        context = "\n\n".join(context_parts)

        if context:
            response = f"Based on my knowledge base, here's what I found regarding '{user_query}':\n\n{context}"
        else:
            response = f"I don't have specific information about '{user_query}' in my current knowledge base. Please add relevant documents to help me provide better answers."

        return jsonify({
            'query': user_query,
            'response': response,
            'sources': sources,
            'context_used': bool(context),
            'response_time': time.time()
        })

    except Exception as e:
        import traceback
        logger.error(f"RAG chat error: {str(e)}\n{traceback.format_exc()}")
        logger.error(f"Request data that caused error: {request.get_data(as_text=True)}")
        return jsonify({'error': f'Chat failed: {str(e)}'}), 500

@app.route('/api/rag', methods=['POST'])
def rag_query():
    """Perform RAG operations using ChromaDB or fallback"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        n_results = data.get('n_results', 5)

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        # Check if ChromaDB is available
        if not CHROMADB_AVAILABLE or chroma_client is None:
            return jsonify({
                'query': query,
                'results': [],
                'count': 0,
                'message': 'ChromaDB not available, using fallback functionality'
            })

        # Perform search in ChromaDB
        results = chroma_client.query(query_text=query, n_results=n_results)

        # Format results
        formatted_results = [
            {
                'id': result['id'],
                'content': result['document'],
                'metadata': result['metadata'],
                'distance': result['distance']
            }
            for result in results
        ]

        return jsonify({
            'query': query,
            'results': formatted_results,
            'count': len(formatted_results)
        })
    except Exception as e:
        logger.error(f"RAG query error: {str(e)}")
        return jsonify({'error': f'Failed to process query: {str(e)}'}), 500

@app.route('/api/programs/<program_id>/rag', methods=['GET'])
def rag_program(program_id):
    """RAG response for a selected program"""
    try:
        # Find the program document by id
        all_docs = vector_store.get_all_documents()
        program_doc = next((doc for doc in all_docs if doc.get('metadata', {}).get('id') == program_id or doc.get('id') == program_id), None)
        if not program_doc:
            return jsonify({'error': f'Program {program_id} not found'}), 404
        # Use the document text as the query/context
        user_query = program_doc['text']
        search_results = vector_store.search(user_query, n_results=3)
        context = '\n\n'.join([f"Source {i+1}: {doc}" for i, doc in enumerate(search_results['documents'][0])]) if search_results['documents'][0] else ""
        response = f"RAG summary for program '{program_id}':\n\n{context}" if context else f"No relevant information found for program '{program_id}'."
        return jsonify({
            'program_id': program_id,
            'response': response,
            'sources': search_results['documents'][0],
            'context_used': bool(context)
        })
    except Exception as e:
        logger.error(f"RAG program error: {str(e)}")
        return jsonify({'error': f'RAG program failed: {str(e)}'}), 500

@app.route('/api/resources/<resource_id>/rag', methods=['GET'])
def rag_resource(resource_id):
    """RAG response for a selected resource"""
    try:
        # Find the resource document by id
        all_docs = vector_store.get_all_documents()
        resource_doc = next((doc for doc in all_docs if doc.get('metadata', {}).get('id') == resource_id or doc.get('id') == resource_id), None)
        if not resource_doc:
            return jsonify({'error': f'Resource {resource_id} not found'}), 404
        user_query = resource_doc['text']
        search_results = vector_store.search(user_query, n_results=3)
        context = '\n\n'.join([f"Source {i+1}: {doc}" for i, doc in enumerate(search_results['documents'][0])]) if search_results['documents'][0] else ""
        response = f"RAG summary for resource '{resource_id}':\n\n{context}" if context else f"No relevant information found for resource '{resource_id}'."
        return jsonify({
            'resource_id': resource_id,
            'response': response,
            'sources': search_results['documents'][0],
            'context_used': bool(context)
        })
    except Exception as e:
        logger.error(f"RAG resource error: {str(e)}")
        return jsonify({'error': f'RAG resource failed: {str(e)}'}), 500

# Additional endpoints for compatibility
@app.route('/api/collections/stats', methods=['GET'])
def get_collection_stats():
    """Get collection statistics"""
    return jsonify({
        'total_documents': vector_store.count(),
        'collection_name': 'simple_vector_store',
        'rag_status': 'available' if rag_system_available else 'unavailable'
    })

@app.route('/startup', methods=['GET'])
def startup_check():
    """Startup readiness check"""
    return jsonify({
        'ready': True,
        'rag_available': rag_system_available,
        'service': 'PocketPro SBA',
        'document_count': vector_store.count()
    })

# Utility function to perform search
def perform_search(query, n_results=3):
    try:
        results = vector_store.search(query, n_results=n_results)
        
        # Format results
        formatted_results = []
        if results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'content': doc,
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i],
                    'relevance_score': 1 - results['distances'][0][i]
                })
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return []

# Register all routes in one place
try:
    from routes import register_all_routes
    register_all_routes(app)
    logger.info("✅ All API routes registered successfully")
except Exception as e:
    logger.warning(f"⚠️ Failed to register API routes: {str(e)}")

# Attach global assistants to app for routes access
app.concierge = Concierge(conversation_store)
app.search_agent = SearchAgent()
app.file_agent = FileAgent()
app.function_agent = FunctionAgent()

# Log the configured port - CRITICAL for Render.com

# For Render.com, we need to expose the app for Gunicorn to find
application = app

# Create socketio for compatibility with run.py
socketio = None

def run_app():
    port = int(os.environ.get("PORT", 5000))  # Use 5000 for Render, not 10000
    debug = os.environ.get("FLASK_ENV", "production") == "development"
    logger.info(f"🚀 Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)

if __name__ == "__main__":
    run_app()

try:
    from chromadb.config import Settings
except ImportError as e:
    raise ImportError("Missing 'chromadb' dependency. Ensure it is installed in your environment.") from e


# --- Serve React Frontend Build for All Non-API Routes ---
# This catch-all route should be registered LAST, after all API and health routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    # Block all API and health routes from being served by React
    if (
        path.startswith('api') or path.startswith('/api') or
        path in ['health', '/health'] or
        path.startswith('static/')
    ):
        logger.info(f"[Catch-all] Blocked attempt to serve frontend for API/health route: {path}")
        return '', 404
    static_dir = os.path.join(app.root_path, 'static')
    react_build_dir = os.path.join(app.root_path, 'frontend', 'build')
    # Ensure static directory exists, and copy from React build if missing
    if not os.path.exists(static_dir):
        os.makedirs(static_dir, exist_ok=True)
        # Copy React build files if available
        if os.path.exists(react_build_dir):
            import shutil
            for item in os.listdir(react_build_dir):
                s = os.path.join(react_build_dir, item)
                d = os.path.join(static_dir, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
    # Serve static file or index.html
    if path != "" and os.path.exists(os.path.join(static_dir, path)):
        logger.info(f"[Catch-all] Serving static file: {path}")
        return send_from_directory(static_dir, path)
    else:
        logger.info(f"[Catch-all] Serving index.html for path: {path}")
        return send_from_directory(static_dir, 'index.html')
