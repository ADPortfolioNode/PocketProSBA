import os
import logging
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import time

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Enhanced CORS configuration for production and development
CORS(app, 
     origins=[
         "*",  # Allow all origins
         "http://localhost:3000",
         "http://localhost:5000",
         "https://pocketprosba-backend.onrender.com",
         "https://pocketprosba-frontend.onrender.com",
         "https://*.onrender.com",
         "https://*.vercel.app",
         "https://*.herokuapp.com",
         "http://localhost:3001",
         "http://localhost:3002",
         "http://127.0.0.1:3000",
         "http://127.0.0.1:5000"
     ],
     allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials", "X-Requested-With", "Access-Control-Request-Method", "Access-Control-Request-Headers", "X-API-Key"],
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
     expose_headers=["Access-Control-Allow-Origin", "Access-Control-Allow-Credentials", "X-Requested-With"],
     max_age=3600
)

# Import enhanced RAG service
sys.path.append('./backend')
from backend.enhanced_gemini_rag_service import enhanced_rag_service

# Initialize enhanced RAG service
def initialize_enhanced_rag():
    """Initialize the enhanced Gemini RAG service"""
    try:
        success = enhanced_rag_service.initialize_full_service()
        if success:
            logger.info("✅ Enhanced Gemini RAG service initialized")
        else:
            logger.error("❌ Failed to initialize enhanced RAG service")
        return success
    except Exception as e:
        logger.error(f"❌ Error initializing enhanced RAG: {str(e)}")
        return False

# Initialize on startup
rag_initialized = initialize_enhanced_rag()

# Global error handlers for production
@app.errorhandler(500)
def handle_500(e):
    logger.error(f"Internal server error: {str(e)}", exc_info=True)
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def handle_404(e):
    return jsonify({"error": "Not found"}), 404

# Production request logging
@app.before_request
def log_request():
    logger.info(f"{request.method} {request.path} from {request.remote_addr}")

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Production health check"""
    rag_status = enhanced_rag_service.get_service_status() if rag_initialized else {"status": "unavailable"}
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'PocketPro SBA Enhanced',
        'version': '2.0.0',
        'rag_available': rag_initialized,
        'rag_status': rag_status
    })

# API health check endpoint
@app.route('/api/health', methods=['GET'])
def api_health_check():
    """API health check endpoint"""
    rag_status = enhanced_rag_service.get_service_status() if rag_initialized else {"status": "unavailable"}
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'PocketPro SBA API Enhanced',
        'version': '2.0.0',
        'rag_available': rag_initialized,
        'rag_status': rag_status
    })

# API status endpoint
@app.route('/api/status', methods=['GET'])
def api_status():
    """Production API status"""
    rag_status = enhanced_rag_service.get_service_status() if rag_initialized else {"status": "unavailable"}
    return jsonify({
        'service': 'PocketPro SBA Enhanced',
        'status': 'operational',
        'version': '2.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'rag_available': rag_initialized,
        'rag_status': rag_status
    })

# Enhanced chat endpoint with full RAG
@app.route('/api/chat', methods=['POST'])
def chat():
    """Enhanced chat endpoint with full RAG functionality"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        if not rag_initialized:
            return jsonify({
                'response': "I'm currently setting up my enhanced knowledge base. Please try again in a moment.",
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat(),
                'service': 'fallback'
            }), 503
        
        # Use enhanced RAG service
        result = enhanced_rag_service.query_sba_loans(message)
        
        if 'error' in result:
            return jsonify({
                'response': result.get('answer', 'Sorry, I encountered an error processing your question.'),
                'error': result['error'],
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat(),
                'service': 'enhanced'
            }), 500
        
        return jsonify({
            'response': result['answer'],
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'enhanced',
            'sources': result.get('source_documents', [])
        })
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': 'Failed to process message'}), 500

# Enhanced search endpoint
@app.route('/api/search', methods=['POST'])
def search():
    """Enhanced search with semantic similarity"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        query = data.get('query', '').strip()
        limit = min(int(data.get('limit', 5)), 10)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        if not rag_initialized:
            return jsonify({
                'query': query,
                'results': [],
                'count': 0,
                'error': 'RAG service not available'
            }), 503
        
        results = enhanced_rag_service.search_documents(query, limit)
        
        return jsonify({
            'query': query,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500

# Get SBA overview endpoint
@app.route('/api/sba-overview', methods=['GET'])
def sba_overview():
    """Get comprehensive SBA information overview"""
    try:
        if not rag_initialized:
            return jsonify({
                'error': 'RAG service not available',
                'overview': 'Basic SBA information'
            }), 503
        
        overview = enhanced_rag_service.get_sba_overview()
        return jsonify(overview)
        
    except Exception as e:
        logger.error(f"Overview error: {str(e)}")
        return jsonify({'error': 'Failed to get overview'}), 500

# Production frontend serving
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve production React frontend"""
    if path.startswith('api/') or path == 'health':
        return jsonify({'error': 'Not found'}), 404
    
    static_dir = os.path.join(os.path.dirname(__file__), 'frontend', 'build')
    
    if path != "" and os.path.exists(os.path.join(static_dir, path)):
        return send_from_directory(static_dir, path)
    else:
        return send_from_directory(static_dir, 'index.html')

# Initialize production app
def init_production_app():
    """Initialize production application"""
    logger.info("🚀 Initializing PocketPro SBA Enhanced...")
    
    # Create uploads directory
    uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    
    logger.info("✅ Enhanced application initialized")
    return app

# Production application instance
application = init_production_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "production") != "production"
    
    logger.info(f"🚀 Starting enhanced server on port {port}")
    application.run(host="0.0.0.0", port=port, debug=debug)
