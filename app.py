from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import os
import sys
import json
import uuid
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

# RESTful API endpoints for RAG operations

# =============================================================================
# DOCUMENT OPERATIONS (RESTful)
# =============================================================================


@app.route('/api/documents', methods=['GET'])
def list_documents():
    """List all documents in the collection."""
    try:
        # Get all documents from ChromaDB
        stats = rag_manager.get_collection_stats()
        
        # Get document metadata
        documents_info = []
        if hasattr(rag_manager.chroma_service, 'collection') and rag_manager.chroma_service.collection:
            try:
                # Get all documents
                results = rag_manager.chroma_service.collection.get()
                
                if results and 'metadatas' in results and 'ids' in results:
                    # Group by file_hash to get unique documents
                    unique_docs = {}
                    for i, metadata in enumerate(results['metadatas']):
                        if metadata and 'file_hash' in metadata:
                            file_hash = metadata['file_hash']
                            if file_hash not in unique_docs:
                                unique_docs[file_hash] = {
                                    'id': file_hash,
                                    'filename': metadata.get('filename', 'unknown'),
                                    'source': metadata.get('source', 'unknown'),
                                    'file_path': metadata.get('file_path', ''),
                                    'chunk_count': 0,
                                    'created_at': metadata.get('created_at', ''),
                                    'type': metadata.get('chunk_type', 'content')
                                }
                            unique_docs[file_hash]['chunk_count'] += 1
                    
                    documents_info = list(unique_docs.values())
            except Exception as e:
                print(f"Warning: Could not retrieve document details: {e}")
        
        return jsonify({
            "success": True,
            "documents": documents_info,
            "total_documents": len(documents_info),
            "total_chunks": stats.get("document_count", 0),
            "collection_stats": stats
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "documents": []
        }), 500

@app.route('/api/documents', methods=['POST'])
def create_document():
    """Upload and create a new document."""
    try:
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No file part in request"
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "No file selected"
            }), 400
        
        filename = secure_filename(file.filename)
        
        # Check if file type is supported
        if not document_processor.is_supported_file(filename):
            return jsonify({
                "success": False,
                "error": f"File type not supported. Supported types: {', '.join(config.ALLOWED_EXTENSIONS)}"
            }), 400
        
        # Save file
        upload_folder = config.UPLOAD_FOLDER
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Process and add to vector database
        result = document_processor.process_file(file_path, filename)
        
        if result.get('success'):
            # Generate document ID (using file hash if available)
            doc_id = result.get('file_hash', str(uuid.uuid4()))
            
            return jsonify({
                "success": True,
                "message": "Document created successfully",
                "document": {
                    "id": doc_id,
                    "filename": filename,
                    "chunks_created": result.get('chunks_created', 0),
                    "file_path": file_path
                }
            }), 201
        else:
            return jsonify({
                "success": False,
                "error": f"Document processing failed: {result.get('error', 'Unknown error')}",
                "filename": filename
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Document creation failed: {str(e)}"
        }), 500

@app.route('/api/documents/<document_id>', methods=['GET'])
def get_document(document_id):
    """Get a specific document by ID."""
    try:
        # Query ChromaDB for document chunks
        if hasattr(rag_manager.chroma_service, 'collection') and rag_manager.chroma_service.collection:
            results = rag_manager.chroma_service.collection.get(
                where={"file_hash": document_id}
            )
            
            if results and 'documents' in results and 'metadatas' in results:
                document_chunks = []
                metadata = None
                
                for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas'])):
                    if i == 0:  # Use first chunk's metadata for document info
                        metadata = meta
                    
                    document_chunks.append({
                        "chunk_index": meta.get('chunk_index', i),
                        "content": doc,
                        "type": meta.get('chunk_type', 'content')
                    })
                
                if metadata:
                    return jsonify({
                        "success": True,
                        "document": {
                            "id": document_id,
                            "filename": metadata.get('filename', 'unknown'),
                            "source": metadata.get('source', 'unknown'),
                            "file_path": metadata.get('file_path', ''),
                            "chunks": document_chunks,
                            "chunk_count": len(document_chunks)
                        }
                    })
        
        return jsonify({
            "success": False,
            "error": "Document not found"
        }), 404
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/documents/<document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Delete a specific document by ID."""
    try:
        # Get all chunk IDs for this document
        if hasattr(rag_manager.chroma_service, 'collection') and rag_manager.chroma_service.collection:
            results = rag_manager.chroma_service.collection.get(
                where={"file_hash": document_id}
            )
            
            if results and 'ids' in results and results['ids']:
                # Delete all chunks for this document
                delete_result = rag_manager.chroma_service.delete_documents(ids=results['ids'])
                
                if delete_result:
                    return jsonify({
                        "success": True,
                        "message": f"Document deleted successfully",
                        "chunks_deleted": len(results['ids'])
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": "Failed to delete document from database"
                    }), 500
            else:
                return jsonify({
                    "success": False,
                    "error": "Document not found"
                }), 404
        
        return jsonify({
            "success": False,
            "error": "ChromaDB collection not available"
        }), 500
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/documents/<document_id>/chunks', methods=['GET'])
def get_document_chunks(document_id):
    """Get all chunks for a specific document."""
    try:
        if hasattr(rag_manager.chroma_service, 'collection') and rag_manager.chroma_service.collection:
            results = rag_manager.chroma_service.collection.get(
                where={"file_hash": document_id}
            )
            
            if results and 'documents' in results and 'metadatas' in results:
                chunks = []
                for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas'])):
                    chunks.append({
                        "chunk_id": results['ids'][i] if 'ids' in results else f"{document_id}_{i}",
                        "chunk_index": meta.get('chunk_index', i),
                        "content": doc,
                        "type": meta.get('chunk_type', 'content'),
                        "metadata": meta
                    })
                
                return jsonify({
                    "success": True,
                    "document_id": document_id,
                    "chunks": chunks,
                    "total_chunks": len(chunks)
                })
        
        return jsonify({
            "success": False,
            "error": "Document not found"
        }), 404
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# =============================================================================
# SEARCH & QUERY OPERATIONS (RESTful)
# =============================================================================

@app.route('/api/search', methods=['POST'])
def semantic_search():
    """Perform semantic search across documents."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required"
            }), 400
        
        query_text = data.get('query', '').strip()
        if not query_text:
            return jsonify({
                "success": False,
                "error": "Query text is required"
            }), 400
        
        n_results = min(data.get('n_results', 5), 20)  # Limit to 20 results max
        include_metadata = data.get('include_metadata', True)
        filters = data.get('filters', {})
        
        # Perform semantic search using ChromaDB directly for filters
        if filters:
            # Use ChromaDB service directly for filtered search
            results = rag_manager.chroma_service.query_documents(
                query_text=query_text,
                n_results=n_results,
                where=filters
            )
        else:
            # Use RAG manager for standard search
            results = rag_manager.query_documents(
                query=query_text,
                n_results=n_results
            )
        
        if results.get('success'):
            search_results = []
            query_results = results.get('results', {})
            
            documents = query_results.get('documents', [[]])[0]
            metadatas = query_results.get('metadatas', [[]])[0] if include_metadata else []
            distances = query_results.get('distances', [[]])[0]
            ids = query_results.get('ids', [[]])[0]
            
            for i, doc in enumerate(documents):
                result_item = {
                    "id": ids[i] if i < len(ids) else f"result_{i}",
                    "content": doc,
                    "relevance_score": 1 - distances[i] if i < len(distances) else 0.5,
                    "distance": distances[i] if i < len(distances) else 0.5
                }
                
                if include_metadata and i < len(metadatas):
                    result_item["metadata"] = metadatas[i]
                    result_item["filename"] = metadatas[i].get('filename', 'unknown')
                    result_item["source"] = metadatas[i].get('source', 'unknown')
                
                search_results.append(result_item)
            
            return jsonify({
                "success": True,
                "query": query_text,
                "results": search_results,
                "total_results": len(search_results),
                "filters_applied": filters
            })
        else:
            return jsonify({
                "success": False,
                "error": results.get('error', 'Search failed'),
                "query": query_text,
                "results": []
            }), 500
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "results": []
        }), 500

@app.route('/api/query', methods=['POST'])
def rag_query():
    """Perform RAG query with context generation."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required"
            }), 400
        
        query_text = data.get('query', '').strip()
        if not query_text:
            return jsonify({
                "success": False,
                "error": "Query text is required"
            }), 400
        
        # Parameters for RAG query
        max_context_length = data.get('max_context_length', 2000)
        n_results = min(data.get('n_results', 5), 10)
        include_sources = data.get('include_sources', True)
        assistant_type = data.get('assistant_type', 'general')
        
        # Get relevant documents using ChromaDB service directly for more control
        search_results = rag_manager.chroma_service.query_documents(
            query_text=query_text,
            n_results=n_results
        )
        
        if not search_results.get('success'):
            return jsonify({
                "success": False,
                "error": "Failed to retrieve relevant documents",
                "query": query_text
            }), 500
        
        # Build context from search results
        context_parts = []
        sources = []
        
        query_results = search_results.get('results', {})
        documents = query_results.get('documents', [[]])[0]
        metadatas = query_results.get('metadatas', [[]])[0]
        distances = query_results.get('distances', [[]])[0]
        
        for i, doc in enumerate(documents):
            if len(' '.join(context_parts)) + len(doc) > max_context_length:
                break
            
            context_parts.append(doc)
            
            if include_sources and i < len(metadatas):
                sources.append({
                    "filename": metadatas[i].get('filename', 'unknown'),
                    "chunk_index": metadatas[i].get('chunk_index', i),
                    "relevance_score": 1 - distances[i] if i < len(distances) else 0.5
                })
        
        context = '\n\n'.join(context_parts)
        
        # Generate response using LLM
        try:
            # Create a simple RAG prompt
            rag_prompt = f"""Based on the following context, please answer the question:

Context:
{context}

Question: {query_text}

Please provide a helpful and accurate answer based on the context provided."""
            
            # Get LLM response
            llm_response = llm.generate_response(rag_prompt)
            
            return jsonify({
                "success": True,
                "query": query_text,
                "answer": llm_response,
                "context_used": len(context_parts),
                "sources": sources if include_sources else [],
                "metadata": {
                    "assistant_type": assistant_type,
                    "context_length": len(context),
                    "max_context_length": max_context_length
                }
            })
            
        except Exception as llm_error:
            # Fallback: return search results without LLM generation
            return jsonify({
                "success": True,
                "query": query_text,
                "answer": "I found relevant information but couldn't generate a response. Please check the sources below.",
                "context_used": len(context_parts),
                "sources": sources if include_sources else [],
                "error": f"LLM generation failed: {str(llm_error)}",
                "fallback_mode": True
            })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "query": query_text if 'query_text' in locals() else ""
        }), 500

# =============================================================================
# ASSISTANT OPERATIONS (RESTful)
# =============================================================================

@app.route('/api/assistants', methods=['GET'])
def list_assistants():
    """List available assistant types."""
    try:
        from src.assistants import concierge, file_agent, function_agent, search_agent
        
        assistants = [
            {
                "type": "concierge",
                "name": "Concierge Assistant",
                "description": "General purpose assistant for SBA-related queries and guidance",
                "capabilities": ["general_questions", "sba_guidance", "business_advice"]
            },
            {
                "type": "search",
                "name": "Search Agent",
                "description": "Specialized in document search and information retrieval",
                "capabilities": ["document_search", "semantic_search", "information_retrieval"]
            },
            {
                "type": "file",
                "name": "File Agent",
                "description": "Handles file operations and document management",
                "capabilities": ["file_upload", "document_processing", "file_management"]
            },
            {
                "type": "function",
                "name": "Function Agent",
                "description": "Executes specific business functions and workflows",
                "capabilities": ["business_functions", "workflow_execution", "task_automation"]
            }
        ]
        
        return jsonify({
            "success": True,
            "assistants": assistants,
            "total_assistants": len(assistants)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "assistants": []
        }), 500

@app.route('/api/assistants/<assistant_type>/query', methods=['POST'])
def query_assistant(assistant_type):
    """Query a specific assistant type."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required"
            }), 400
        
        query_text = data.get('query', '').strip()
        if not query_text:
            return jsonify({
                "success": False,
                "error": "Query text is required"
            }), 400
        
        context = data.get('context', {})
        use_rag = data.get('use_rag', True)
        
        # Route to appropriate assistant
        if assistant_type == "concierge":
            response = concierge.handle_message(query_text)
        elif assistant_type == "search":
            from src.assistants.search_agent import create_search_agent
            search_agent = create_search_agent()
            response = search_agent.handle_message(query_text)
        elif assistant_type == "file":
            from src.assistants.file_agent import create_file_agent
            file_agent = create_file_agent()
            response = file_agent.handle_message(query_text)
        elif assistant_type == "function":
            from src.assistants.function_agent import create_function_agent
            function_agent = create_function_agent()
            response = function_agent.handle_message(query_text)
        else:
            return jsonify({
                "success": False,
                "error": f"Unknown assistant type: {assistant_type}"
            }), 400
        
        return jsonify({
            "success": True,
            "assistant_type": assistant_type,
            "query": query_text,
            "response": response
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "assistant_type": assistant_type,
            "query": query_text if 'query_text' in locals() else ""
        }), 500

# =============================================================================
# COLLECTION & SYSTEM OPERATIONS (RESTful)
# =============================================================================

@app.route('/api/collections/stats', methods=['GET'])
def get_collection_stats():
    """Get comprehensive collection statistics."""
    try:
        stats = rag_manager.get_collection_stats()
        
        # Get additional information
        if hasattr(rag_manager.chroma_service, 'collection') and rag_manager.chroma_service.collection:
            try:
                collection_info = {
                    "name": getattr(rag_manager.chroma_service.collection, 'name', config.CHROMA_COLLECTION_NAME),
                    "embedding_function": str(type(rag_manager.chroma_service.embedding_function)) if rag_manager.chroma_service.embedding_function else "default"
                }
            except:
                collection_info = {"name": config.CHROMA_COLLECTION_NAME}
        else:
            collection_info = {"status": "not_available"}
        
        return jsonify({
            "success": True,
            "collection_stats": stats,
            "collection_info": collection_info,
            "chromadb_available": getattr(rag_manager.chroma_service, '_chroma_available', False)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/collections/reindex', methods=['POST'])
def reindex_collection():
    """Reindex all documents in the collection."""
    try:
        # This would trigger a full reindex of documents
        # For now, return a placeholder response
        return jsonify({
            "success": True,
            "message": "Collection reindexing initiated",
            "status": "in_progress"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/embeddings/info', methods=['GET'])
def get_embedding_info():
    """Get information about the embedding model being used."""
    try:
        embedding_info = rag_manager.chroma_service.get_embedding_info()
        
        return jsonify({
            "success": True,
            "embedding_info": embedding_info
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
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

@app.route('/api/endpoints', methods=['GET'])
def get_endpoints():
    """
    Returns all registered endpoints in the Flask application.
    This allows frontend and concierge services to discover available routes.
    """
    endpoints = []
    for rule in app.url_map.iter_rules():
        # Skip the static endpoint as it's not relevant for API consumers
        if rule.endpoint != 'static':
            endpoints.append({
                'url': str(rule),
                'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
                'endpoint': rule.endpoint,
                'description': app.view_functions.get(rule.endpoint).__doc__
            })
    
    return jsonify({
        'status': 'success',
        'endpoints': endpoints,
        'count': len(endpoints)
    })

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

# =============================================================================
# ADDITIONAL HELPER ENDPOINTS
# =============================================================================

@app.route('/api/session/startup', methods=['GET'])
def session_startup():
    """
    Endpoint to return all available routes on the Flask server.
    Helps frontend and concierge understand what endpoints are available.
    """
    routes = []
    for rule in app.url_map.iter_rules():
        # Skip static routes if desired, or include all
        if rule.endpoint == 'static':
            continue
        methods = sorted([method for method in rule.methods if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']])
        routes.append({
            "endpoint": rule.endpoint,
            "methods": methods,
            "rule": str(rule)
        })
    return jsonify({"routes": routes})

@app.route('/api/documents/<document_id>/reprocess', methods=['POST'])
def reprocess_document(document_id):
    """Reprocess a document (useful after embedding model changes)."""
    try:
        # First, get document info
        if hasattr(rag_manager.chroma_service, 'collection') and rag_manager.chroma_service.collection:
            results = rag_manager.chroma_service.collection.get(
                where={"file_hash": document_id}
            )
            
            if results and 'metadatas' in results and results['metadatas']:
                metadata = results['metadatas'][0]
                file_path = metadata.get('file_path')
                filename = metadata.get('filename')
                
                if file_path and os.path.exists(file_path):
                    # Delete existing chunks
                    delete_result = rag_manager.chroma_service.delete_documents(ids=results['ids'])
                    
                    if delete_result:
                        # Reprocess the file
                        process_result = document_processor.process_file(file_path, filename)
                        
                        if process_result.get('success'):
                            return jsonify({
                                "success": True,
                                "message": "Document reprocessed successfully",
                                "document_id": document_id,
                                "chunks_created": process_result.get('chunks_created', 0)
                            })
                        else:
                            return jsonify({
                                "success": False,
                                "error": f"Reprocessing failed: {process_result.get('error', 'Unknown error')}"
                            }), 500
                    else:
                        return jsonify({
                            "success": False,
                            "error": "Failed to delete existing document chunks"
                        }), 500
                else:
                    return jsonify({
                        "success": False,
                        "error": "Original file not found"
                    }), 404
            else:
                return jsonify({
                    "success": False,
                    "error": "Document not found"
                }), 404
        
        return jsonify({
            "success": False,
            "error": "ChromaDB collection not available"
        }), 500
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/search/filters', methods=['GET'])
def get_search_filters():
    """Get available filters for search operations."""
    try:
        # Get sample metadata to determine available filters
        filters = {
            "filename": [],
            "source": [],
            "chunk_type": [],
            "file_extensions": []
        }
        
        if hasattr(rag_manager.chroma_service, 'collection') and rag_manager.chroma_service.collection:
            try:
                # Sample some documents to get filter options
                results = rag_manager.chroma_service.collection.get(limit=100)
                
                if results and 'metadatas' in results:
                    for metadata in results['metadatas']:
                        if metadata:
                            # Collect unique values for filters
                            if 'filename' in metadata:
                                filename = metadata['filename']
                                if filename not in filters['filename']:
                                    filters['filename'].append(filename)
                                
                                # Extract file extension
                                ext = os.path.splitext(filename)[1].lower()
                                if ext and ext not in filters['file_extensions']:
                                    filters['file_extensions'].append(ext)
                            
                            if 'source' in metadata and metadata['source'] not in filters['source']:
                                filters['source'].append(metadata['source'])
                            
                            if 'chunk_type' in metadata and metadata['chunk_type'] not in filters['chunk_type']:
                                filters['chunk_type'].append(metadata['chunk_type'])
                
            except Exception as e:
                print(f"Warning: Could not retrieve filter options: {e}")
        
        return jsonify({
            "success": True,
            "filters": filters,
            "filter_descriptions": {
                "filename": "Filter by specific filename",
                "source": "Filter by document source (e.g., startup_upload, manual_upload)",
                "chunk_type": "Filter by chunk type (e.g., content, header, table)",
                "file_extensions": "Available file extensions in the collection"
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get comprehensive system status."""
    try:
        # Get all service statuses
        chroma_stats = rag_manager.get_collection_stats()
        
        from src.services.model_discovery import get_model_discovery_service
        model_service = get_model_discovery_service()
        available_models = model_service.discover_available_models()
        
        # Get startup results if available
        global startup_results
        
        status = {
            "system": "PocketPro:SBA Edition",
            "version": "1.0.0",
            "status": "operational",
            "timestamp": str(datetime.now()),
            "services": {
                "chromadb": {
                    "status": "connected" if chroma_stats.get("success") else "disconnected",
                    "document_count": chroma_stats.get("document_count", 0),
                    "collection_name": config.CHROMA_COLLECTION_NAME
                },
                "llm": {
                    "status": "connected" if config.GEMINI_API_KEY else "not_configured",
                    "current_model": config.LLM_MODEL,
                    "available_models": len(available_models)
                },
                "model_discovery": {
                    "status": "active",
                    "models_found": len(available_models)
                }
            },
            "capabilities": {
                "document_upload": True,
                "semantic_search": chroma_stats.get("success", False),
                "rag_query": bool(config.GEMINI_API_KEY),
                "assistant_chat": True,
                "file_processing": True
            },
            "startup_results": startup_results if 'startup_results' in globals() else None
        }
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            "system": "PocketPro:SBA Edition",
            "status": "error",
            "error": str(e),
            "timestamp": str(datetime.now())
        }), 500

# =============================================================================
# BATCH OPERATIONS
# =============================================================================

@app.route('/api/documents/batch', methods=['POST'])
def batch_upload_documents():
    """Upload multiple documents at once."""
    try:
        if 'files' not in request.files:
            return jsonify({
                "success": False,
                "error": "No files part in request"
            }), 400
        
        files = request.files.getlist('files')
        if not files:
            return jsonify({
                "success": False,
                "error": "No files selected"
            }), 400
        
        results = []
        successful_uploads = 0
        failed_uploads = 0
        
        for file in files:
            if file.filename == '':
                continue
            
            try:
                filename = secure_filename(file.filename)
                
                # Check if file type is supported
                if not document_processor.is_supported_file(filename):
                    results.append({
                        "filename": filename,
                        "success": False,
                        "error": f"File type not supported"
                    })
                    failed_uploads += 1
                    continue
                
                # Save file
                upload_folder = config.UPLOAD_FOLDER
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                
                # Process file
                result = document_processor.process_file(file_path, filename)
                
                if result.get('success'):
                    results.append({
                        "filename": filename,
                        "success": True,
                        "document_id": result.get('file_hash', str(uuid.uuid4())),
                        "chunks_created": result.get('chunks_created', 0)
                    })
                    successful_uploads += 1
                else:
                    results.append({
                        "filename": filename,
                        "success": False,
                        "error": result.get('error', 'Processing failed')
                    })
                    failed_uploads += 1
                    
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(e)
                })
                failed_uploads += 1
        
        return jsonify({
            "success": successful_uploads > 0,
            "total_files": len(files),
            "successful_uploads": successful_uploads,
            "failed_uploads": failed_uploads,
            "results": results
        }), 201 if successful_uploads > 0 else 400
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/documents/batch', methods=['DELETE'])
def batch_delete_documents():
    """Delete multiple documents at once."""
    try:
        data = request.get_json()
        if not data or 'document_ids' not in data:
            return jsonify({
                "success": False,
                "error": "document_ids array is required"
            }), 400
        
        document_ids = data.get('document_ids', [])
        if not document_ids:
            return jsonify({
                "success": False,
                "error": "No document IDs provided"
            }), 400
        
        results = []
        successful_deletions = 0
        failed_deletions = 0
        
        for doc_id in document_ids:
            try:
                # Get document chunks
                if hasattr(rag_manager.chroma_service, 'collection') and rag_manager.chroma_service.collection:
                    doc_results = rag_manager.chroma_service.collection.get(
                        where={"file_hash": doc_id}
                    )
                    
                    if doc_results and 'ids' in doc_results and doc_results['ids']:
                        # Delete all chunks
                        delete_result = rag_manager.chroma_service.delete_documents(ids=doc_results['ids'])
                        
                        if delete_result:
                            results.append({
                                "document_id": doc_id,
                                "success": True,
                                "chunks_deleted": len(doc_results['ids'])
                            })
                            successful_deletions += 1
                        else:
                            results.append({
                                "document_id": doc_id,
                                "success": False,
                                "error": "Failed to delete from database"
                            })
                            failed_deletions += 1
                    else:
                        results.append({
                            "document_id": doc_id,
                            "success": False,
                            "error": "Document not found"
                        })
                        failed_deletions += 1
                        
            except Exception as e:
                results.append({
                    "document_id": doc_id,
                    "success": False,
                    "error": str(e)
                })
                failed_deletions += 1
        
        return jsonify({
            "success": successful_deletions > 0,
            "total_documents": len(document_ids),
            "successful_deletions": successful_deletions,
            "failed_deletions": failed_deletions,
            "results": results
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/concierge/edit_application', methods=['POST'])
def concierge_edit_application():
    """
    Allows the concierge to make edits to the RAG application based on user requests.
    This endpoint processes code modification requests and applies them if appropriate.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required"
            }), 400
        
        edit_request = data.get('edit_request', '').strip()
        target_file = data.get('target_file', '').strip()
        proposed_changes = data.get('proposed_changes', '').strip()
        
        if not edit_request:
            return jsonify({
                "success": False,
                "error": "Edit request description is required"
            }), 400
            
        # Security validation - only allow edits to certain files
        allowed_edit_paths = [
            os.path.join(os.path.dirname(__file__), 'src', 'assistants'),
            os.path.join(os.path.dirname(__file__), 'src', 'utils'),
            os.path.join(os.path.dirname(__file__), 'static', 'js'),
            os.path.join(os.path.dirname(__file__), 'static', 'css'),
            os.path.join(os.path.dirname(__file__), 'templates')
        ]
        
        # Validate target file path
        valid_target = False
        absolute_target_path = os.path.abspath(target_file)
        for allowed_path in allowed_edit_paths:
            if absolute_target_path.startswith(os.path.abspath(allowed_path)):
                valid_target = True
                break
                
        if not valid_target and target_file:
            return jsonify({
                "success": False,
                "error": "Target file location not allowed for editing",
                "allowed_paths": [p.replace(os.path.dirname(__file__), '') for p in allowed_edit_paths]
            }), 403
            
        # Process the edit request using the concierge
        # This could use a specialized method in the concierge service
        edit_response = concierge.process_application_edit(
            edit_request=edit_request,
            target_file=target_file,
            proposed_changes=proposed_changes
        )
        
        # If the concierge returns information about changes that were made
        if edit_response.get('changes_applied', False):
            # Log the successful application edit
            print(f"🔧 Application edit applied: {edit_request} to {target_file}")
            
            # Return success with details
            return jsonify({
                "success": True,
                "message": "Application edit applied successfully",
                "edit_details": edit_response
            })
        else:
            # Return the explanation from the concierge about why the edit wasn't applied
            return jsonify({
                "success": False,
                "message": "Application edit was not applied",
                "reason": edit_response.get('reason', 'Unknown reason'),
                "suggestions": edit_response.get('suggestions', [])
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to process application edit request: {str(e)}"
        }), 500
