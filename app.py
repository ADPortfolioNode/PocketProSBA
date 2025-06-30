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
from src.assistants.concierge import create_concierge
from src.services.startup_service import initialize_app_on_startup

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize services
rag_manager = get_rag_manager()
llm = LLMFactory.get_llm()
document_processor = DocumentProcessor()
concierge = create_concierge()

# Initialize application on startup (load files from uploads, etc.)
startup_results = initialize_app_on_startup()
print(f"🔄 Startup initialization results: {startup_results}")

# In-memory storage for demonstration
tasks = {}
files = []

@app.route('/api/greeting', methods=['GET'])
def get_greeting():
    """Get the system greeting and status."""
    try:
        greeting_response = concierge.get_system_greeting()
        return jsonify(greeting_response)
    except Exception as e:
        return jsonify({
            "success": False,
            "text": f"Welcome to PocketPro:SBA Edition! Error getting system status: {str(e)}",
            "additional_data": {"greeting": True, "error": str(e)}
        }), 500

@app.route('/api/decompose', methods=['POST'])
def decompose():
    try:
        data = request.json or {}
        task = data.get('task', '')
        message = data.get('message', task)  # Support both 'task' and 'message' fields
        
        if not message:
            return jsonify({
                "response": {
                    "text": "Please provide a task or message for me to process.",
                    "media": None,
                    "sources": []
                }
            }), 400
        
        # Use Concierge to handle the message
        concierge_response = concierge.handle_message(message)
        
        # Format response for API compatibility
        response = {
            "response": {
                "text": concierge_response.get("text", "No response generated"),
                "media": concierge_response.get("additional_data", {}).get("media"),
                "sources": concierge_response.get("additional_data", {}).get("sources", [])
            },
            "success": concierge_response.get("success", False)
        }
        
        # Add task data if it's a task decomposition
        if "task" in concierge_response.get("additional_data", {}):
            response["task"] = concierge_response["additional_data"]["task"]
        
        return jsonify(response)
    except Exception as e:
        return jsonify({
            "response": {
                "text": f"I encountered an error while processing your request: {str(e)}",
                "media": None,
                "sources": []
            },
            "success": False
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
    """Get application information including available models."""
    try:
        from src.services.model_discovery import get_model_discovery_service
        from src.services.llm_factory import LLMFactory
        
        collection_stats = rag_manager.get_collection_stats()
        model_service = get_model_discovery_service()
        llm = LLMFactory.get_llm()
        
        # Get available models
        available_models = model_service.discover_available_models()
        
        # Get current model info
        current_model_info = model_service.get_model_info(llm.model_name)
        
        return jsonify({
            "app_name": "PocketPro:SBA Edition",
            "version": "1.0.0",
            "brand": "StainlessDeoism.biz",
            "documents_count": collection_stats.get("document_count", 0),
            "supported_formats": list(config.ALLOWED_EXTENSIONS),
            "max_file_size": config.MAX_CONTENT_LENGTH,
            "current_model": {
                "name": llm.model_name,
                "display_name": current_model_info.get('display_name', 'Unknown') if current_model_info else 'Unknown',
                "description": current_model_info.get('description', '') if current_model_info else ''
            },
            "available_models": [
                {
                    "name": model['name'],
                    "display_name": model['display_name'],
                    "description": model['description']
                }
                for model in available_models
            ],
            "model_count": len(available_models),
            "services": {
                "llm": "connected" if llm else "disconnected",
                "chromadb": "connected" if rag_manager.chroma_service._chroma_available else "disconnected",
                "model_discovery": "active"
            }
        })
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


@app.route('/api/models', methods=['GET'])
def get_available_models():
    """Get detailed information about available models."""
    try:
        from src.services.model_discovery import get_model_discovery_service
        
        model_service = get_model_discovery_service()
        models = model_service.discover_available_models()
        
        return jsonify({
            "available_models": models,
            "count": len(models),
            "last_updated": "cached" if model_service._available_models else "live"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/models/refresh', methods=['POST'])
def refresh_models():
    """Force refresh the list of available models."""
    try:
        from src.services.model_discovery import get_model_discovery_service
        
        model_service = get_model_discovery_service()
        models = model_service.discover_available_models(force_refresh=True)
        
        return jsonify({
            "message": "Models refreshed successfully",
            "available_models": models,
            "count": len(models)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/models/switch', methods=['POST'])
def switch_model():
    """Switch to a different available model."""
    try:
        data = request.get_json()
        new_model = data.get('model_name')
        
        if not new_model:
            return jsonify({"error": "model_name is required"}), 400
        
        from src.services.model_discovery import get_model_discovery_service
        from src.services.llm_factory import LLMFactory
        
        model_service = get_model_discovery_service()
        
        # Validate the model
        if not model_service.validate_model(new_model):
            available_models = model_service.list_available_models()
            return jsonify({
                "error": f"Model '{new_model}' is not available",
                "available_models": available_models
            }), 400
        
        # Update the config and reinitialize
        config.LLM_MODEL = new_model
        LLMFactory._llm_instance = None  # Force recreation
        llm = LLMFactory.get_llm()
        
        return jsonify({
            "message": f"Successfully switched to model: {new_model}",
            "current_model": llm.model_name
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/debug/chromadb', methods=['GET'])
def debug_chromadb():
    """Debug ChromaDB connection status."""
    try:
        from src.services.chroma_service import get_chroma_service_instance
        
        # Get the ChromaDB service instance
        chroma_service = get_chroma_service_instance()
        
        # Test the connection
        connection_test = chroma_service.test_connection()
        
        # Get collection stats
        collection_stats = chroma_service.get_collection_stats()
        
        # Check if documents exist
        documents_test = None
        try:
            if hasattr(chroma_service, 'collection') and chroma_service.collection:
                documents_test = {
                    "collection_count": chroma_service.collection.count(),
                    "collection_name": config.CHROMA_COLLECTION_NAME
                }
        except Exception as e:
            documents_test = {"error": str(e)}
        
        return jsonify({
            "connection_test": connection_test,
            "collection_stats": collection_stats,
            "documents_test": documents_test,
            "chroma_available": getattr(chroma_service, '_chroma_available', False),
            "has_client": hasattr(chroma_service, 'client') and chroma_service.client is not None,
            "has_collection": hasattr(chroma_service, 'collection') and chroma_service.collection is not None
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "debug": "Failed to test ChromaDB connection"
        }), 500

@app.route('/api/admin/initialize', methods=['POST'])
def initialize_application():
    """Manually trigger application initialization (load files from uploads)."""
    try:
        from src.services.startup_service import initialize_app_on_startup
        
        results = initialize_app_on_startup()
        
        return jsonify({
            "success": True,
            "initialization_results": results,
            "message": "Application initialization completed"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Application initialization failed"
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
