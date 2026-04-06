#!/usr/bin/env python3
"""
Minimal test script to verify ChromaDB connection
"""
import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_chromadb_connection():
    """Test ChromaDB connection"""
    try:
        import chromadb
        logger.info("✅ ChromaDB import successful")
        
        # Test connection
        client = chromadb.HttpClient(
            host=os.environ.get('CHROMA_HOST', 'chromadb'),
            port=int(os.environ.get('CHROMA_PORT', 8000))
        )
        
        # Test heartbeat
        result = client.heartbeat()
        logger.info(f"✅ ChromaDB heartbeat successful: {result}")
        
        # Test collection creation
        collection = client.get_or_create_collection("test_collection")
        logger.info(f"✅ Collection created: {collection.name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ChromaDB connection failed: {e}")
        return False

def test_basic_imports():
    """Test basic imports"""
    try:
        import flask
        import flask_cors
        import flask_socketio
        import google.generativeai
        logger.info("✅ All basic imports successful")
        return True
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        return False

if __name__ == '__main__':
    logger.info("🔄 Starting PocketPro SBA connection tests...")
    
    # Test basic imports
    if not test_basic_imports():
        sys.exit(1)
    
    # Test ChromaDB connection
    if not test_chromadb_connection():
        sys.exit(1)
    
    logger.info("✅ All tests passed! System ready.")
    
    # Start minimal Flask app
    from flask import Flask, jsonify
    from flask_cors import CORS
    
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy",
            "service": "PocketPro SBA Backend",
            "chromadb": "connected"
        })
    
    @app.route('/')
    def index():
        return jsonify({
            "message": "PocketPro SBA Backend Test",
            "status": "running"
        })
    
    logger.info("🚀 Starting minimal Flask server...")
    app.run(host='0.0.0.0', port=5000, debug=False)