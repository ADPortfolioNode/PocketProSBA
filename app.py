import os
import logging
import time
import hashlib
import re
import json
import math
from collections import Counter
from flask import Flask, request, jsonify
from flask_cors import CORS
from src.utils.config import config

# Initialize Flask app and load config
app = Flask(__name__)
app.config.from_object(config)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def initialize_rag_system():
    """Initialize the RAG system"""
    global vector_store, rag_system_available
    
    try:
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
        
        logger.info(f"✅ Added {len(sample_docs)} sample documents")
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

# Initialize on startup
startup_result = startup()

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        'service': 'PocketPro SBA',
        'version': '1.0.0',
        'status': 'operational',
        'message': 'Welcome to PocketPro SBA RAG API'
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'PocketPro SBA',
        'version': '1.0.0',
        'rag_status': 'available' if rag_system_available else 'unavailable',
        'document_count': vector_store.count()
    })

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
        data = request.get_json()
        user_query = data.get('message', '')
        
        if not user_query:
            return jsonify({'error': 'Message is required'}), 400
        
        # Retrieve relevant documents
        search_results = vector_store.search(user_query, n_results=3)
        
        # Build context and sources
        context_parts = []
        sources = []
        
        if search_results['documents'][0]:
            for i, doc in enumerate(search_results['documents'][0]):
                context_parts.append(f"Source {i+1}: {doc}")
                sources.append({
                    'id': search_results['ids'][0][i],
                    'content': doc[:200] + "..." if len(doc) > 200 else doc,
                    'metadata': search_results['metadatas'][0][i],
                    'relevance': 1 - search_results['distances'][0][i]
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
        logger.error(f"RAG chat error: {str(e)}")
        return jsonify({'error': f'Chat failed: {str(e)}'}), 500

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

# Create socketio for compatibility with run.py
socketio = None

# Utility function for searching
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
        
        return {
            'query': query,
            'results': formatted_results,
            'count': len(formatted_results),
            'search_time': time.time()
        }
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return {'error': f'Search failed: {str(e)}'}

       

# Register all routes in one place
from routes import register_all_routes

# Create socketio for compatibility with run.py
socketio = None

if __name__ == '__main__':
    # Render.com compatible port binding
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    vector_store_type = "Simple Memory"
    
    logger.info(f"🚀 Starting PocketPro SBA RAG Edition on 0.0.0.0:{port}")
    logger.info(f"Environment: {'development' if debug else 'production'}")
    logger.info(f"Vector Store: {vector_store_type}")
    logger.info(f"RAG System: {'✅ Available' if rag_system_available else '❌ Unavailable'}")
    logger.info(f"Documents loaded: {vector_store.count() if vector_store else 0}")
    
    # Start the application
    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)
