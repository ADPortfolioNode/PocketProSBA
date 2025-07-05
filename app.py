import os
import logging
import time
import hashlib
import re
import shutil
from collections import Counter
from flask import Flask, request, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ChromaDB configuration and initialization
chroma_client = None
collection = None

class SimpleEmbeddingFunction:
    """Simple embedding function for ChromaDB 0.3.29 compatibility"""
    
    def __call__(self, texts):
        """Convert texts to simple embeddings using hash-based approach with TF-IDF style"""
        embeddings = []
        
        # Create a simple vocabulary from all texts
        all_words = set()
        text_words = []
        
        for text in texts:
            # Simple tokenization and preprocessing
            words = re.findall(r'\b\w+\b', str(text).lower())
            text_words.append(words)
            all_words.update(words)
        
        # Create consistent vocabulary
        vocab = sorted(list(all_words))[:384]  # Limit vocabulary size
        
        for words in text_words:
            # Create simple TF-IDF style embedding
            word_counts = Counter(words)
            total_words = len(words)
            
            embedding = []
            for word in vocab:
                # Simple term frequency
                tf = word_counts.get(word, 0) / max(total_words, 1)
                embedding.append(float(tf))
            
            # Pad to consistent length of 384
            while len(embedding) < 384:
                embedding.append(0.0)
            
            embeddings.append(embedding[:384])
        
        return embeddings

def cleanup_chroma_directories():
    """Clean up conflicting ChromaDB directories"""
    current_dir = os.getcwd()
    
    # List of potential conflicting directories
    conflicting_dirs = [
        os.path.join(current_dir, '.chroma'),
        os.path.join(current_dir, 'chroma_db'),
        os.path.join(current_dir, '.chromadb')
    ]
    
    for dir_path in conflicting_dirs:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                logger.info(f"Removed conflicting directory: {dir_path}")
            except Exception as e:
                logger.warning(f"Could not remove {dir_path}: {e}")

def initialize_chromadb():
    """Initialize ChromaDB with production-ready configuration"""
    global chroma_client, collection
    
    # Clean up any existing conflicting directories
    cleanup_chroma_directories()
    
    # Create a unique directory name to avoid conflicts
    db_path = os.path.abspath(os.path.join(os.getcwd(), 'pocketpro_vector_db'))
    
    # Remove and recreate the directory for clean state
    if os.path.exists(db_path):
        try:
            shutil.rmtree(db_path)
            logger.info(f"Cleaned existing database directory: {db_path}")
        except Exception as e:
            logger.warning(f"Could not clean database directory: {e}")
    
    os.makedirs(db_path, exist_ok=True)
    
    # Set environment variables to prevent conflicts
    os.environ['CHROMA_DB_IMPL'] = 'duckdb+parquet'
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Initialize ChromaDB client using 0.3.29 compatible method
        try:
            # Method 1: Use Settings for ChromaDB 0.3.29
            settings = Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=db_path,
                anonymized_telemetry=False
            )
            chroma_client = chromadb.Client(settings)
            logger.info(f"✅ ChromaDB Client initialized with Settings at: {db_path}")
        except Exception as settings_error:
            logger.warning(f"Settings-based client failed: {settings_error}")
            try:
                # Method 2: Default client for ChromaDB 0.3.29
                chroma_client = chromadb.Client()
                logger.info("✅ ChromaDB Client initialized with default method")
            except Exception as client_error:
                logger.error(f"All ChromaDB client methods failed: {client_error}")
                return False
        
        # Initialize embedding function
        embedding_function = SimpleEmbeddingFunction()
        
        # Test the embedding function
        try:
            test_embedding = embedding_function(["test document for embedding"])
            logger.info(f"✅ Embedding function test successful - dimension: {len(test_embedding[0])}")
        except Exception as embed_error:
            logger.error(f"Embedding function test failed: {embed_error}")
            return False
        
        # Collection management
        collection_name = "pocketpro_sba_documents"
        
        # Clean up existing collection
        try:
            existing_collections = chroma_client.list_collections()
            for col in existing_collections:
                if col.name == collection_name:
                    chroma_client.delete_collection(collection_name)
                    logger.info(f"Deleted existing collection: {collection_name}")
                    break
        except Exception as delete_error:
            logger.info(f"No existing collection to delete: {delete_error}")
        
        # Create new collection with embedding function - REQUIRED for ChromaDB 0.3.29
        try:
            collection = chroma_client.create_collection(
                name=collection_name,
                embedding_function=embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"✅ Created collection: {collection_name}")
            
        except Exception as collection_error:
            logger.error(f"Collection creation failed: {collection_error}")
            return False
        
        # Comprehensive functionality test
        try:
            # Test document
            test_doc = "This is a test document for PocketPro SBA RAG system functionality verification."
            test_id = "test_init_doc"
            test_metadata = {
                "type": "test", 
                "timestamp": int(time.time()),
                "source": "initialization"
            }
            
            # Test addition
            collection.add(
                documents=[test_doc],
                ids=[test_id],
                metadatas=[test_metadata]
            )
            logger.info("✅ Document addition test passed")
            
            # Test search
            search_results = collection.query(
                query_texts=["test document"],
                n_results=1
            )
            
            if search_results and search_results.get('documents') and search_results['documents'][0]:
                logger.info("✅ Search functionality test passed")
            else:
                logger.warning("⚠️ Search test returned no results")
            
            # Test deletion
            collection.delete(ids=[test_id])
            logger.info("✅ Document deletion test passed")
            
            # Final status
            final_count = collection.count()
            logger.info(f"🎉 ChromaDB RAG system fully initialized - {final_count} documents in collection")
            
            return True
            
        except Exception as test_error:
            logger.error(f"Functionality test failed: {test_error}")
            return False
        
    except ImportError as import_error:
        logger.error(f"ChromaDB import failed: {import_error}")
        return False
    except Exception as e:
        logger.error(f"❌ ChromaDB initialization failed: {str(e)}")
        return False

def startup():
    """Initialize all services on startup"""
    logger.info("🚀 Initializing PocketPro SBA RAG application...")
    
    try:
        # Initialize ChromaDB
        chromadb_available = initialize_chromadb()
        
        startup_results = {
            'startup_completed': True,
            'chromadb_status': 'available' if chromadb_available else 'unavailable',
            'available_models': ['gemini-pro', 'rag-simple'] if chromadb_available else [],
            'collection_available': collection is not None,
            'client_available': chroma_client is not None,
            'embedding_model': 'simple-tfidf-custom',
            'db_path': os.path.abspath(os.path.join(os.getcwd(), 'pocketpro_vector_db')),
            'rag_ready': chromadb_available
        }
        
        logger.info(f"🎯 Startup Results: {startup_results}")
        return startup_results
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        return {
            'startup_completed': False,
            'error': str(e),
            'chromadb_status': 'unavailable',
            'available_models': [],
            'collection_available': False,
            'client_available': False,
            'rag_ready': False
        }

# Initialize on startup
startup()

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'PocketPro SBA',
        'version': '1.0.0',
        'chromadb_status': 'available' if collection else 'unavailable'
    })

# API endpoints
@app.route('/api/info', methods=['GET'])
def get_system_info():
    """Get system information"""
    return jsonify({
        'service': 'PocketPro SBA',
        'version': '1.0.0',
        'status': 'operational',
        'chromadb_status': 'available' if collection else 'unavailable'
    })

@app.route('/api/models', methods=['GET'])
def get_available_models():
    """Get available AI models"""
    return jsonify({'models': ['gemini-pro']})

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Get all documents"""
    if collection:
        try:
            results = collection.get()
            documents = []
            if results and 'documents' in results:
                for i, doc in enumerate(results['documents']):
                    documents.append({
                        'id': results['ids'][i] if 'ids' in results else f'doc_{i}',
                        'content': doc,
                        'metadata': results['metadatas'][i] if 'metadatas' in results else {}
                    })
            
            return jsonify({
                'documents': documents,
                'count': len(documents),
                'chromadb_status': 'available'
            })
        except Exception as e:
            logger.error(f"Error getting documents: {str(e)}")
    
    return jsonify({
        'documents': [],
        'count': 0,
        'chromadb_status': 'unavailable'
    })

@app.route('/api/collections/stats', methods=['GET'])
def get_collection_stats():
    """Get collection statistics"""
    if collection:
        try:
            count = collection.count()
            return jsonify({
                'total_documents': count,
                'collection_name': 'pocketpro_sba_documents',
                'chromadb_status': 'available'
            })
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
    
    return jsonify({
        'total_documents': 0,
        'collection_name': 'pocketpro_sba_documents',
        'chromadb_status': 'unavailable'
    })

@app.route('/api/search/filters', methods=['GET'])
def get_search_filters():
    """Get available search filters"""
    return jsonify({
        'filters': ['document_type', 'created_date', 'tags'],
        'document_types': ['pdf', 'docx', 'txt', 'md']
    })

@app.route('/api/assistants', methods=['GET'])
def get_assistants():
    """Get available AI assistants"""
    assistants = [
        {'id': 'sba_advisor', 'name': 'SBA Business Advisor', 'type': 'business'},
        {'id': 'document_analyzer', 'name': 'Document Analyzer', 'type': 'analysis'}
    ]
    return jsonify({'assistants': assistants})

# Startup endpoint for Docker health checks
@app.route('/startup', methods=['GET'])
def startup_check():
    """Startup readiness check for Docker"""
    status = {
        'ready': True,
        'chromadb_available': collection is not None,
        'service': 'PocketPro SBA'
    }
    
    if collection:
        try:
            status['document_count'] = collection.count()
        except:
            status['document_count'] = 0
    
    return jsonify(status)

# Create socketio for compatibility with run.py
socketio = None

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"🚀 Starting PocketPro SBA RAG Edition on 0.0.0.0:{port}")
    logger.info(f"Environment: {'development' if debug else 'production'}")
    logger.info(f"ChromaDB Status: {'✅ Available' if collection else '❌ Unavailable'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
