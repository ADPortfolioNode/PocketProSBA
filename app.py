import os
import logging
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

def initialize_chromadb():
    """Initialize ChromaDB with new client configuration"""
    global chroma_client, collection
    
    try:
        import chromadb
        
        # Use new ChromaDB client configuration (updated for latest version)
        chroma_client = chromadb.Client()
        
        # Create or get collection
        collection = chroma_client.get_or_create_collection(
            name="pocketpro_sba_documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info("✅ ChromaDB initialized successfully with new client")
        return True
        
    except ImportError:
        logger.warning("⚠️ ChromaDB not available - running in minimal mode")
        return False
    except Exception as e:
        logger.error(f"❌ ChromaDB initialization failed: {str(e)}")
        return False

def startup():
    """Initialize all services on startup"""
    logger.info("🔄 Initializing PocketPro SBA application...")
    
    # Initialize ChromaDB
    chromadb_available = initialize_chromadb()
    
    startup_results = {
        'startup_completed': True,
        'chromadb_status': 'available' if chromadb_available else 'unavailable',
        'available_models': ['gemini-pro'] if chromadb_available else []
    }
    
    logger.info(f"🔄 Startup initialization results: {startup_results}")
    return startup_results

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
    logger.info(f"Starting PocketPro SBA Edition on 0.0.0.0:{port}")
    logger.info("Environment: development")
    app.run(host='0.0.0.0', port=port, debug=True)
