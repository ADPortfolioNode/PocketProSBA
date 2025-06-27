from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import sys
from datetime import datetime
from datetime import datetime

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import our services
from src.utils.config import config
from src.services.rag_manager import get_rag_manager
from src.services.llm_factory import LLMFactory
from src.services.document_processor import DocumentProcessor

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize services
rag_manager = get_rag_manager()
llm = LLMFactory.get_llm()
document_processor = DocumentProcessor()

# In-memory storage for demonstration
tasks = {}
files = []

@app.route('/api/decompose', methods=['POST'])
def decompose():
    try:
        data = request.json or {}
        message = data.get('message', '')
        
        # Use LLM to generate response or decompose task
        intent = llm.classify_intent(message)
        
        if intent in ['document_search', 'simple_query']:
            # Generate RAG response
            response_data = rag_manager.generate_rag_response(message)
            response = {
                "response": {
                    "text": response_data.get('text', 'No response generated'),
                    "media": None,
                    "sources": response_data.get('sources', [])
                }
            }
        else:
            # Decompose complex task
            task_data = llm.decompose_task(message)
            response = {
                "response": {
                    "text": f"I've broken down your task into {len(task_data.get('steps', []))} steps.",
                    "media": None,
                    "sources": []
                },
                "task": task_data
            }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({
            "response": {
                "text": f"I encountered an error: {str(e)}",
                "media": None,
                "sources": []
            }
        }), 500

@app.route('/api/execute', methods=['POST'])
def execute():
    data = request.json or {}
    task = data.get('task', {})
    step_number = task.get('step_number')
    instruction = task.get('instruction')
    suggested_agent_type = task.get('suggested_agent_type')
    # Dummy execution response
    result = {
        "step_number": step_number,
        "status": "completed",
        "result": f"Executed step {step_number} with instruction: {instruction} using agent {suggested_agent_type}"
    }
    return jsonify(result)

@app.route('/api/validate', methods=['POST'])
def validate():
    data = request.json or {}
    result_text = data.get('result', '')
    task = data.get('task', {})
    step_number = task.get('step_number')
    instruction = task.get('instruction')
    # Dummy validation response
    response = {
        "status": "PASS",
        "confidence": 0.95,
        "feedback": f"Validation passed for step {step_number}"
    }
    return jsonify(response)

@app.route('/api/tasks/<task_id>/results', methods=['GET'])
def task_results(task_id):
    # Dummy task results
    response = {
        "task_id": task_id,
        "status": "completed",
        "steps": []
    }
    return jsonify(response)

@app.route('/api/files', methods=['GET'])
def list_files():
    return jsonify({"files": files})

@app.route('/api/files', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"message": "No file part"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"message": "No selected file"}), 400
        
        filename = file.filename or "unnamed_file"
        
        # Check if file type is supported
        if not document_processor.is_supported_file(filename):
            return jsonify({
                "message": f"File type not supported. Supported types: {', '.join(config.ALLOWED_EXTENSIONS)}"
            }), 400
        
        # Save file
        upload_folder = config.UPLOAD_FOLDER
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Process and add to vector database
        result = document_processor.process_file(file_path, filename)
        
        if result.get('success'):
            files.append({"id": len(files)+1, "name": filename})
            return jsonify({
                "message": f"File uploaded and processed successfully. Created {result.get('chunks_created', 0)} chunks.",
                "filename": filename
            })
        else:
            return jsonify({
                "message": f"File uploaded but processing failed: {result.get('error', 'Unknown error')}",
                "filename": filename
            }), 500
            
    except Exception as e:
        return jsonify({"message": f"Upload failed: {str(e)}"}), 500

@app.route('/api/documents/upload_and_ingest_document', methods=['POST'])
def upload_and_ingest():
    # For simplicity, reuse upload_file logic
    return upload_file()

@app.route('/api/chroma/store_document_embedding', methods=['POST'])
def store_document_embedding():
    data = request.json
    # Dummy response
    return jsonify({"success": True, "id": "doc-123"})

@app.route('/api/chroma/store_step_embedding', methods=['POST'])
def store_step_embedding():
    data = request.json
    # Dummy response
    return jsonify({"message": "Step embedding stored", "status": "success"})

@app.route('/api/query', methods=['POST'])
def query():
    try:
        data = request.json or {}
        query_text = data.get('query', '')
        top_k = data.get('top_k', config.DEFAULT_TOP_K)
        
        # Use RAG manager to search documents
        results = rag_manager.query_documents(query_text, top_k)
        
        return jsonify(results)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "results": []
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for container monitoring."""
    try:
        # Check ChromaDB connection
        chroma_stats = rag_manager.get_collection_stats()
        
        return jsonify({
            "status": "healthy",
            "timestamp": str(datetime.now()),
            "services": {
                "chromadb": "connected" if chroma_stats.get("success") else "disconnected",
                "llm": "connected" if config.GEMINI_API_KEY else "not_configured"
            },
            "collection_stats": chroma_stats
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/api/info', methods=['GET'])
def get_info():
    """Get application information."""
    try:
        collection_stats = rag_manager.get_collection_stats()
        return jsonify({
            "app_name": "PocketPro:SBA Edition",
            "version": "1.0.0",
            "brand": "StainlessDeoism.biz",
            "documents_count": collection_stats.get("document_count", 0),
            "supported_formats": list(config.ALLOWED_EXTENSIONS),
            "max_file_size": config.MAX_CONTENT_LENGTH
        })
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@socketio.on('connect')
def on_connect():
    emit('assistant_status', {"status": "connected"})

@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected')

@socketio.on('chat_message')
def on_chat_message(data):
    text = data.get('text', '')
    # Dummy response
    emit('chat_response', {"text": f"Echo: {text}", "sources": []})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
