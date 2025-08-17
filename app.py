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

# Enhanced CORS configuration for production
CORS(app, 
     origins=[
         "http://localhost:3000",
         "http://localhost:5000",
         "https://pocketprosba-backend.onrender.com",
         "https://*.onrender.com",
         "https://*.vercel.app",
         "https://*.herokuapp.com",
         "http://localhost:3001",
         "http://localhost:3002"
     ],
     allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials", "X-Requested-With"],
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     expose_headers=["Access-Control-Allow-Origin"]
)

# Environment configuration
REQUIRED_ENV_VARS = ["GEMINI_API_KEY", "SECRET_KEY"]
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
if missing_vars:
    logger.warning(f"Missing environment variables: {missing_vars}")

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

# Production RAG Service
class ProductionRAGService:
    def __init__(self):
        self.documents = {}
        self.embeddings = {}
        self.initialized = False
        self._initialize_production_data()
    
    def _initialize_production_data(self):
        """Initialize with production-ready SBA data"""
        production_documents = [
            {
                "id": "sba_7a_loan_guide",
                "text": "SBA 7(a) loans provide up to $5 million for small businesses. Interest rates are typically prime + 2.25% to 4.75%. Terms: 25 years for real estate, 10 years for equipment, 7 years for working capital. Down payment as low as 10%.",
                "metadata": {"category": "financing", "type": "loan_guide", "amount": "up_to_5m"}
            },
            {
                "id": "business_plan_template",
                "text": "Essential business plan sections: Executive Summary, Company Description, Market Analysis, Organization & Management, Service/Product Line, Marketing & Sales, Funding Request, Financial Projections, Appendix.",
                "metadata": {"category": "planning", "type": "template", "priority": "high"}
            },
            {
                "id": "sba_504_loan_details",
                "text": "SBA 504 loans finance major fixed assets like real estate and equipment. Up to $5.5 million per project. Fixed-rate financing with 10, 20, or 25-year terms. Requires 10% borrower equity contribution.",
                "metadata": {"category": "financing", "type": "loan_details", "program": "504"}
            },
            {
                "id": "startup_funding_checklist",
                "text": "Startup funding options: SBA loans, personal savings, friends/family, angel investors, venture capital, crowdfunding, grants, business credit cards. Evaluate each based on your business stage and needs.",
                "metadata": {"category": "funding", "type": "checklist", "stage": "startup"}
            },
            {
                "id": "sba_microloan_program",
                "text": "SBA Microloans up to $50,000 for small businesses and nonprofits. Average loan is $13,000. Delivered through nonprofit intermediaries. Can be used for working capital, inventory, supplies, furniture, fixtures.",
                "metadata": {"category": "financing", "type": "program", "max_amount": "50k"}
            }
        ]
        
        for doc in production_documents:
            self.add_document(doc["text"], doc["metadata"], doc["id"])
        
        self.initialized = True
        logger.info("✅ Production RAG data initialized")
    
    def add_document(self, text: str, metadata: dict, doc_id: str = None) -> str:
        """Add document to knowledge base"""
        if not doc_id:
            import hashlib
            doc_id = hashlib.md5(text.encode()).hexdigest()[:8]
        
        self.documents[doc_id] = {
            "text": text,
            "metadata": metadata,
            "added_at": datetime.utcnow().isoformat()
        }
        return doc_id
    
    def search(self, query: str, limit: int = 5) -> list:
        """Search documents with basic relevance"""
        results = []
        query_lower = query.lower()
        
        for doc_id, doc in self.documents.items():
            if any(word in doc["text"].lower() for word in query_lower.split()):
                results.append({
                    "id": doc_id,
                    "content": doc["text"],
                    "metadata": doc["metadata"],
                    "relevance": 0.8
                })
        
        return results[:limit]
    
    def query(self, query: str) -> str:
        """Generate production response"""
        results = self.search(query, limit=2)
        
        if not results:
            return self._get_production_response(query)
        
        context = "\n\n".join([r["content"] for r in results])
        return f"Based on SBA resources: {context}"
    
    def _get_production_response(self, query: str) -> str:
        """Production fallback responses"""
        query_lower = query.lower()
        
        responses = {
            "loan": "I can help with SBA loan information. Would you like details about 7(a), 504, or microloans?",
            "business plan": "I have comprehensive business plan guidance. What specific section would you like help with?",
            "funding": "I can explain various funding options including SBA loans, grants, and investor funding.",
            "startup": "For startups, I recommend exploring SBA microloans, 7(a) loans, and business plan development.",
            "help": "I'm here to help with SBA programs, business planning, and funding guidance. What would you like to know?"
        }
        
        for keyword, response in responses.items():
            if keyword in query_lower:
                return response
        
        return "I'm here to help with SBA programs, business planning, and funding guidance. Could you tell me more specifically what you're looking for?"

# Initialize production RAG service
rag_service = ProductionRAGService()

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Production health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'PocketPro SBA Production',
        'version': '1.0.0',
        'rag_available': True,
        'document_count': len(rag_service.documents)
    })

# API status endpoint
@app.route('/api/status', methods=['GET'])
def api_status():
    """Production API status"""
    return jsonify({
        'service': 'PocketPro SBA Production',
        'status': 'operational',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'document_count': len(rag_service.documents)
    })

# Production chat endpoint
@app.route('/api/chat', methods=['POST'])
def chat():
    """Production chat endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Use production RAG service
        response = rag_service.query(message)
        
        return jsonify({
            'response': response,
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'production'
        })
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': 'Failed to process message'}), 500

# Documents endpoint
@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Get all documents"""
    try:
        documents = rag_service.get_all_documents() if hasattr(rag_service, 'get_all_documents') else []
        return jsonify({
            'documents': documents,
            'count': len(documents)
        })
    except Exception as e:
        logger.error(f"Documents error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve documents'}), 500

# Search endpoint
@app.route('/api/search', methods=['POST'])
def search():
    """Search documents"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        query = data.get('query', '').strip()
        limit = min(int(data.get('limit', 5)), 10)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        results = rag_service.search(query, limit)
        
        return jsonify({
            'query': query,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500

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
    logger.info("🚀 Initializing PocketPro SBA Production...")
    
    # Create uploads directory
    uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    
    logger.info("✅ Production application initialized")
    return app

# Production application instance
application = init_production_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "production") != "production"
    
    logger.info(f"🚀 Starting production server on port {port}")
    application.run(host="0.0.0.0", port=port, debug=debug)
