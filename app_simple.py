"""
Simplified PocketPro SBA app for testing
"""
import os
import logging
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Simple global variables
rag_system_available = False
collection = None

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'PocketPro SBA Simple',
        'version': '1.0.0',
        'rag_available': rag_system_available
    })

@app.route('/api/info', methods=['GET'])
def get_system_info():
    """Get system information"""
    return jsonify({
        'service': 'PocketPro SBA Simple',
        'version': '1.0.0',
        'status': 'operational',
        'rag_available': rag_system_available,
        'endpoints': ['/health', '/api/info', '/api/test-rag']
    })

@app.route('/api/test-rag', methods=['GET'])
def test_rag():
    """Test RAG functionality"""
    try:
        # Import and test RAG components
        from app import SimpleEmbeddingFunction
        import chromadb
        
        # Quick test
        embedding_func = SimpleEmbeddingFunction()
        test_embedding = embedding_func(["test"])
        
        return jsonify({
            'rag_test': 'success',
            'embedding_dimension': len(test_embedding[0]),
            'chromadb_available': True,
            'message': 'RAG components are working'
        })
        
    except Exception as e:
        return jsonify({
            'rag_test': 'failed',
            'error': str(e),
            'chromadb_available': False,
            'message': 'RAG components have issues'
        }), 500

@app.route('/api/demo-chat', methods=['POST'])
def demo_chat():
    """Demo chat endpoint without full RAG"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Simple demo response
        demo_responses = {
            'sba': 'The Small Business Administration provides loans, grants, and resources for entrepreneurs.',
            'loan': 'SBA offers various loan programs including 7(a) loans, 504 loans, and microloans.',
            'business plan': 'A business plan is essential for securing funding and outlining your business strategy.',
            'startup': 'Starting a business requires planning, funding, legal structure, and market research.'
        }
        
        # Simple keyword matching
        response = "I'm a demo chatbot for PocketPro SBA. "
        for keyword, info in demo_responses.items():
            if keyword.lower() in user_message.lower():
                response += info
                break
        else:
            response += "I can help with SBA loans, business planning, and startup guidance."
        
        return jsonify({
            'query': user_message,
            'response': response,
            'demo_mode': True,
            'rag_enabled': rag_system_available
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))  # Use different port
    
    logger.info(f"🚀 Starting PocketPro SBA Simple on 0.0.0.0:{port}")
    logger.info("📋 Available endpoints:")
    logger.info("   GET  /api/health - Health check")
    logger.info("   GET  /api/info - System info")
    logger.info("   GET  /api/test-rag - Test RAG functionality")
    logger.info("   POST /api/demo-chat - Demo chat")
    
    app.run(host='0.0.0.0', port=port, debug=True)
