#!/usr/bin/env python3
"""
Minimal Flask app for Render.com deployment testing
This version strips down to essentials to ensure deployment works
"""
import os
import sys
import logging
import time
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='[%(asctime)s] %(levelname)s: %(message)s',
                   datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

# Set up the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Get PORT from environment (critical for Render.com)
PORT = int(os.environ.get('PORT', 5000))

# Configure uploads folder
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'frontend', 'uploads'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure uploads directory exists

# Create minimal Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')

# Configure CORS with more specific settings
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:3000",  # React dev server
            "http://localhost:8080",  # Nginx proxy
            "http://frontend:3000",   # Docker service name
            "*"                       # Allow all origins as fallback
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Export for Gunicorn to find - CRITICAL for Render.com
application = app

# Log port information at startup
logger.info("🚀 Application configured to run on port %s (host: 0.0.0.0)", PORT)
logger.info("🔍 Render.com environment: %s", "Yes" if os.environ.get('RENDER') else "No")

@app.route('/')
def index():
    """Root route - minimal response"""
    return jsonify({
        "message": "🚀 PocketPro:SBA is running!",
        "status": "success",
        "version": "1.0.0",
        "service": "PocketPro Small Business Assistant",
        "environment": os.environ.get('FLASK_ENV', 'unknown'),
        "python_version": sys.version.split()[0],
        "port": PORT,
        "host": "0.0.0.0",  # Always binding to all interfaces
        "render": "Yes" if os.environ.get('RENDER') else "No"
    })

@app.route('/health')
def health():
    """Health check endpoint required by Render"""
    return jsonify({
        "status": "healthy",
        "success": True
    })

@app.route('/api/health')
def api_health():
    """API health check endpoint for frontend connection status"""
    return jsonify({
        "status": "connected",
        "success": True,
        "version": "1.0.0",
        "environment": os.environ.get('FLASK_ENV', 'development')
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Simple chat endpoint to respond to frontend requests"""
    try:
        data = request.get_json()
        query = data.get('query', data.get('message', ''))
        user_name = data.get('userName', 'Guest')
        
        # Handle system message
        if query.startswith("SYSTEM:"):
            return jsonify({
                "success": True,
                "response": f"Session started for {user_name}. Welcome to the SBA Assistant!"
            })
        
        # Simple personalized response for minimal app
        response = f"Hello {user_name}! You asked: {query}\n\nThis is a simple response from the minimal backend. For full RAG functionality, use the complete app."
        
        return jsonify({
            "success": True,
            "response": response
        })
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "response": "Sorry, there was an error processing your request."
        }), 500

@app.route('/api/documents/upload', methods=['POST'])
def upload_document():
    """Document upload endpoint"""
    try:
        # Check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file part in the request'
            }), 400
        
        file = request.files['file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No selected file'
            }), 400
        
        # Save the file to the uploads folder
        filename = file.filename
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Get file stats
        stats = os.stat(file_path)
        size_bytes = stats.st_size
        modified_timestamp = stats.st_mtime
        
        # Get file extension
        file_ext = Path(filename).suffix[1:].lower() if '.' in filename else ""
        
        # Determine number of pages (mock for now)
        pages = 1
        if file_ext.lower() in ['pdf', 'docx']:
            # Simulate document with multiple pages
            pages = max(1, size_bytes // 5000)
        
        # Create document metadata
        document = {
            'filename': filename,
            'path': file_path,
            'size': size_bytes,
            'modified': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(modified_timestamp)),
            'type': file_ext,
            'pages': pages
        }
        
        return jsonify({
            'success': True,
            'message': f'File {filename} uploaded successfully',
            'document': document
        })
        
    except Exception as e:
        logger.error(f"Error in document upload: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/documents/search', methods=['GET'])
def search_documents():
    """Mock document search endpoint"""
    query = request.args.get('query', '')
    try:
        # Return mock search results
        return jsonify({
            "success": True,
            "query": query,
            "matches": [
                {
                    "id": "doc1",
                    "title": "SBA Loan Programs Guide",
                    "snippet": "Information about various SBA loan programs including 7(a), 504, and microloans.",
                    "score": 0.92
                },
                {
                    "id": "doc2",
                    "title": "Business Plan Template",
                    "snippet": "Step-by-step guide to creating an effective business plan for SBA loan applications.",
                    "score": 0.85
                }
            ]
        })
    except Exception as e:
        logger.error(f"Error in document search: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/rag/query', methods=['POST'])
def rag_query():
    """Mock RAG query endpoint"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        # Return mock RAG response
        return jsonify({
            "success": True,
            "query": query,
            "response": f"Based on the available information, here's what I can tell you about '{query}': The SBA offers various loan programs to help small businesses, including the 7(a) loan program which provides up to $5 million for various business purposes like working capital, equipment purchase, and real estate.",
            "sources": [
                {
                    "title": "SBA Loan Programs Guide",
                    "page": 12,
                    "relevance": 0.94
                }
            ]
        })
    except Exception as e:
        logger.error(f"Error in RAG query: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "response": "Sorry, there was an error processing your RAG query."
        }), 500

@app.route('/api/documents/list', methods=['GET'])
def list_documents():
    """List documents in the uploads folder"""
    try:
        documents = []
        
        # Check if uploads folder exists
        if not os.path.exists(UPLOAD_FOLDER):
            return jsonify({
                'success': True,
                'documents': documents
            })
        
        # List files in the uploads folder
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                # Get file stats
                stats = os.stat(file_path)
                size_bytes = stats.st_size
                modified_timestamp = stats.st_mtime
                
                # Get file extension
                file_ext = Path(filename).suffix[1:].lower() if '.' in filename else ""
                
                # Determine number of pages (mock for now)
                pages = 1
                if file_ext.lower() in ['pdf', 'docx']:
                    # Simulate document with multiple pages
                    pages = max(1, size_bytes // 5000)
                
                documents.append({
                    'filename': filename,
                    'path': file_path,
                    'size': size_bytes,
                    'modified': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(modified_timestamp)),
                    'type': file_ext,
                    'pages': pages
                })
        
        return jsonify({
            'success': True,
            'documents': documents
        })
        
    except Exception as e:
        logger.error(f"Document listing error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test')
def test():
    """Test endpoint to verify basic functionality"""
    return jsonify({
        "test": "passed",
        "environment_vars": {
            "FLASK_ENV": os.environ.get('FLASK_ENV'),
            "PORT": os.environ.get('PORT'),
            "GEMINI_API_KEY": "***" if os.environ.get('GEMINI_API_KEY') else None
        },
        "python_path": sys.path[:3]
    })

@app.route('/port-debug')
def port_debug():
    """Debug endpoint to check port configuration"""
    # Get all relevant environment variables
    important_vars = ['PORT', 'FLASK_APP', 'FLASK_ENV', 'PYTHONPATH', 'RENDER', 'PYTHON_VERSION']
    env_vars = {k: v for k, v in os.environ.items() if k in important_vars}
    
    # Get network information
    import socket
    hostname = socket.gethostname()
    try:
        ip = socket.gethostbyname(hostname)
    except:
        ip = "Unable to determine"
    
    return jsonify({
        "configured_port": PORT,
        "environment_variables": env_vars,
        "process_id": os.getpid(),
        "working_directory": os.getcwd(),
        "hostname": hostname,
        "ip_address": ip,
        "python_version": sys.version,
        "render_deployment": os.environ.get('RENDER') is not None
    })

# For Gunicorn
application = app

# When run directly, use the PORT environment variable
if __name__ == "__main__":
    port_num = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Starting development server on port {port_num}")
    app.run(host='0.0.0.0', port=port_num, debug=True)
