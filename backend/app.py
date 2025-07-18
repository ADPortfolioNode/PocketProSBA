import os
import logging
import time
import hashlib
import re
import json
import math
from collections import Counter
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configure Flask-SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Import services after app is created
from services.chroma import ChromaService
from services.rag import RAGManager
from assistants.concierge import Concierge
from assistants.search import SearchAgent
from assistants.file import FileAgent
from assistants.function import FunctionAgent

# Initialize services
chroma_service = None
rag_manager = None
rag_system_available = False

# Global assistants
concierge = None
search_agent = None
file_agent = None
function_agent = None

def initialize_services():
    """Initialize all services on startup"""
    global chroma_service, rag_manager, rag_system_available
    global concierge, search_agent, file_agent, function_agent
    
    logger.info("🚀 Initializing PocketPro SBA RAG application...")
    
    try:
        # Initialize ChromaDB service
        chroma_host = os.environ.get("CHROMA_HOST", "localhost")
        chroma_port = int(os.environ.get("CHROMA_PORT", 8000))
        
        logger.info(f"Connecting to ChromaDB at {chroma_host}:{chroma_port}")
        chroma_service = ChromaService(host=chroma_host, port=chroma_port)
        
        # Initialize RAG manager
        rag_manager = RAGManager(chroma_service=chroma_service)
        
        # Initialize assistants
        concierge = Concierge()
        search_agent = SearchAgent()
        file_agent = FileAgent()
        function_agent = FunctionAgent()
        
        # Test the RAG system
        rag_system_available = rag_manager.test_connection()
        
        startup_results = {
            'startup_completed': True,
            'rag_status': 'available' if rag_system_available else 'unavailable',
            'chroma_available': chroma_service.is_available(),
            'document_count': rag_manager.get_document_count() if rag_system_available else 0,
        }
        
        logger.info(f"🎯 Startup Results: {startup_results}")
        return startup_results
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        rag_system_available = False
        return {
            'startup_completed': False,
            'error': str(e),
            'rag_status': 'unavailable',
            'chroma_available': False,
            'document_count': 0
        }

# Initialize on startup
startup_result = initialize_services()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    # Only serve frontend for non-API/non-health routes
    if path.startswith('api/') or path == 'health':
        return handle_404(None)
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
        return send_from_directory(static_dir, path)
    else:
        return send_from_directory(static_dir, 'index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    global rag_system_available
    
    chroma_available = chroma_service.is_available() if chroma_service else False
    doc_count = rag_manager.get_document_count() if rag_manager and rag_system_available else 0
    
    return jsonify({
        'status': 'healthy',
        'service': 'PocketPro SBA',
        'version': '1.0.0',
        'rag_status': 'available' if rag_system_available else 'unavailable',
        'chroma_available': chroma_available,
        'document_count': doc_count
    })

@app.route('/api/info', methods=['GET'])
def get_system_info():
    """Get system information"""
    global rag_system_available
    
    return jsonify({
        'service': 'PocketPro SBA',
        'version': '1.0.0',
        'status': 'operational',
        'rag_status': 'available' if rag_system_available else 'unavailable',
        'vector_store': 'chromadb',
        'document_count': rag_manager.get_document_count() if rag_manager and rag_system_available else 0
    })

@app.route('/api/decompose', methods=['POST'])
def decompose_task():
    """Decompose user task into steps"""
    if not concierge:
        return jsonify({'error': 'Concierge agent not initialized'}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Use Concierge to handle the message
        result = concierge.handle_message(message)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Task decomposition error: {str(e)}")
        return jsonify({'error': f'Failed to decompose task: {str(e)}'}), 500

@app.route('/api/execute', methods=['POST'])
def execute_task():
    """Execute a task step with the appropriate agent"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        task = data.get('task', {})
        if not task:
            return jsonify({'error': 'Task data is required'}), 400
        
        step_number = task.get('step_number')
        instruction = task.get('instruction')
        agent_type = task.get('suggested_agent_type')
        
        if not all([step_number, instruction, agent_type]):
            return jsonify({'error': 'Incomplete task data'}), 400
        
        # Select the appropriate agent
        if agent_type == 'SearchAgent' and search_agent:
            result = search_agent.handle_message(instruction)
        elif agent_type == 'FileAgent' and file_agent:
            result = file_agent.handle_message(instruction)
        elif agent_type == 'FunctionAgent' and function_agent:
            result = function_agent.handle_message(instruction)
        else:
            # Fall back to Concierge
            result = concierge.handle_message(instruction)
        
        # Add step information to result
        result['step_number'] = step_number
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Task execution error: {str(e)}")
        return jsonify({'error': f'Failed to execute task: {str(e)}'}), 500

@app.route('/api/validate', methods=['POST'])
def validate_step():
    """Validate a step result"""
    if not concierge:
        return jsonify({'error': 'Concierge agent not initialized'}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        result = data.get('result')
        task = data.get('task', {})
        
        if not result or not task:
            return jsonify({'error': 'Result and task data are required'}), 400
        
        # Use Concierge to validate the step
        validation = concierge.validate_step(result, task)
        
        return jsonify(validation)
        
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({'error': f'Failed to validate step: {str(e)}'}), 500

@app.route('/api/query', methods=['POST'])
def search():
    """Search for documents"""
    if not rag_system_available or not rag_manager:
        return jsonify({'error': 'RAG system not available'}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        query = data.get('query', '')
        top_k = min(int(data.get('top_k', 5)), 20)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Perform search
        results = rag_manager.query_documents(query, top_k=top_k)
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'count': len(results) if isinstance(results, list) else 0,
            'search_time': time.time()
        })
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/api/files', methods=['GET'])
def list_files():
    """List uploaded files"""
    if not file_agent:
        return jsonify({'error': 'File agent not initialized'}), 503
    
    try:
        # Use FileAgent to list files
        result = file_agent.list_files()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"List files error: {str(e)}")
        return jsonify({'error': f'Failed to list files: {str(e)}'}), 500

@app.route('/api/files', methods=['POST'])
def upload_file():
    """Upload a file"""
    if not file_agent:
        return jsonify({'error': 'File agent not initialized'}), 503
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400
            
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Use FileAgent to upload file
        result = file_agent.upload_file(file)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        return jsonify({'error': f'Failed to upload file: {str(e)}'}), 500

@app.route('/api/documents/upload_and_ingest_document', methods=['POST'])
def upload_and_ingest():
    """Upload and ingest a document"""
    if not file_agent or not rag_manager or not rag_system_available:
        return jsonify({'error': 'Required services not available'}), 503
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400
            
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Upload file
        upload_result = file_agent.upload_file(file)
        
        if 'error' in upload_result:
            return jsonify(upload_result), 400
        
        # Ingest document
        ingest_result = rag_manager.ingest_document(upload_result['filepath'])
        
        return jsonify({
            'message': 'Document uploaded and ingested successfully',
            'filename': file.filename,
            'document_id': ingest_result.get('document_id'),
            'chunks': ingest_result.get('chunks', 0)
        })
        
    except Exception as e:
        logger.error(f"Document upload and ingest error: {str(e)}")
        return jsonify({'error': f'Failed to upload and ingest document: {str(e)}'}), 500

@app.route('/api/chroma/store_document_embedding', methods=['POST'])
def store_document_embedding():
    """Store document embedding in ChromaDB"""
    if not chroma_service or not rag_system_available:
        return jsonify({'error': 'ChromaDB service not available'}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        content = data.get('content', '')
        metadata = data.get('metadata', {})
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        # Store document embedding
        result = rag_manager.store_document(content, metadata)
        
        return jsonify({
            'success': True,
            'id': result.get('id'),
            'message': 'Document embedding stored successfully'
        })
        
    except Exception as e:
        logger.error(f"Store document embedding error: {str(e)}")
        return jsonify({'error': f'Failed to store document embedding: {str(e)}'}), 500

@app.route('/api/chroma/store_step_embedding', methods=['POST'])
def store_step_embedding():
    """Store step embedding in ChromaDB"""
    if not chroma_service or not rag_system_available:
        return jsonify({'error': 'ChromaDB service not available'}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        step_id = data.get('step_id', '')
        embedding = data.get('embedding', [])
        metadata = data.get('metadata', {})
        
        if not step_id or not embedding:
            return jsonify({'error': 'Step ID and embedding are required'}), 400
        
        # Store step embedding
        result = rag_manager.store_step_embedding(step_id, embedding, metadata)
        
        return jsonify({
            'message': 'Step embedding stored successfully',
            'status': 'success',
            'id': result.get('id')
        })
        
    except Exception as e:
        logger.error(f"Store step embedding error: {str(e)}")
        return jsonify({'error': f'Failed to store step embedding: {str(e)}'}), 500

@app.route('/api/tasks/<task_id>/results', methods=['GET'])
def get_task_results(task_id):
    """Get task results"""
    if not concierge:
        return jsonify({'error': 'Concierge agent not initialized'}), 503
    
    try:
        # Get task results
        results = concierge.get_task_results(task_id)
        
        if not results:
            return jsonify({'error': f'Task {task_id} not found'}), 404
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Get task results error: {str(e)}")
        return jsonify({'error': f'Failed to get task results: {str(e)}'}), 500

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    socketio.emit('assistant_status', {
        'status': 'connected',
        'message': 'Connected to PocketPro SBA server'
    }, room=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle chat message from client"""
    if not concierge:
        socketio.emit('chat_response', {
            'error': 'Concierge agent not initialized'
        }, room=request.sid)
        return
    
    try:
        message = data.get('message', '')
        
        if not message:
            socketio.emit('chat_response', {
                'error': 'Message is required'
            }, room=request.sid)
            return
        
        # Update status
        socketio.emit('assistant_status', {
            'status': 'processing',
            'message': 'Processing your request...'
        }, room=request.sid)
        
        # Use Concierge to handle the message
        result = concierge.handle_message(message)
        
        # Send response
        socketio.emit('chat_response', result, room=request.sid)
        
        # Update status
        socketio.emit('assistant_status', {
            'status': 'ready',
            'message': 'Ready for next request'
        }, room=request.sid)
        
    except Exception as e:
        logger.error(f"Chat message error: {str(e)}")
        socketio.emit('chat_response', {
            'error': f'Failed to process message: {str(e)}'
        }, room=request.sid)
        
        # Update status
        socketio.emit('assistant_status', {
            'status': 'error',
            'message': f'Error: {str(e)}'
        }, room=request.sid)

@socketio.on('health_check')
def handle_health_check():
    """Handle health check from client"""
    socketio.emit('health_response', {
        'status': 'healthy',
        'timestamp': time.time()
    }, room=request.sid)

if __name__ == '__main__':
    # This block will not be executed when imported
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "production") == "development"
    
    logger.info(f"🚀 Starting PocketPro SBA RAG application on port {port}")
    
    # Start the application with SocketIO
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)