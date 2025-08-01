import os
import logging
import sys
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Logging Configuration ---
# Direct logs to stdout for containerized environments like Render
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Dependency Availability Checks ---
try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError as e:
    logger.error("ChromaDB library not found. RAG features will be disabled.")
    CHROMADB_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    logger.error("Google Generative AI library not found. LLM features will be disabled.")
    GEMINI_AVAILABLE = False

# --- Flask App Initialization ---
# The static_folder is set to 'static', where the Dockerfile places the React build.
# The static_url_path='' makes the root URL serve files from the static folder.
app = Flask(__name__, static_folder='static', static_url_path='')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# --- Global Service Initialization ---
chroma_client = None
rag_collection = None
embedding_function = None
llm = None

if CHROMADB_AVAILABLE and GEMINI_AVAILABLE:
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    CHROMA_HOST = os.environ.get('CHROMA_HOST')
    CHROMA_PORT = os.environ.get('CHROMA_PORT')

    if not all([GEMINI_API_KEY, CHROMA_HOST, CHROMA_PORT]):
        logger.warning("Missing one or more environment variables (GEMINI_API_KEY, CHROMA_HOST, CHROMA_PORT). RAG system will be disabled.")
        CHROMADB_AVAILABLE = False # Disable RAG if config is missing
    else:
        try:
            # Configure the embedding function
            embedding_function = embedding_functions.GoogleGenerativeAiEmbeddingFunction(api_key=GEMINI_API_KEY)
            
            # Configure the LLM
            genai.configure(api_key=GEMINI_API_KEY)
            llm = genai.GenerativeModel('gemini-pro')

            # Connect to the remote ChromaDB service provided by Render
            logger.info(f"Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}...")
            chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
            
            # Get or create the collection for RAG
            rag_collection = chroma_client.get_or_create_collection(
                name="sba_documents",
                embedding_function=embedding_function
            )
            logger.info("✅ Successfully connected to ChromaDB and got collection.")
            logger.info(f"   Collection '{rag_collection.name}' contains {rag_collection.count()} documents.")

        except Exception as e:
            logger.error(f"Failed to initialize RAG system with ChromaDB and Gemini: {e}", exc_info=True)
            CHROMADB_AVAILABLE = False # Disable on failure

# --- API Endpoints ---

@app.route('/health', methods=['GET'])
def health_check():
    """
    Provides a health check for the service.
    For a robust check, it verifies the connection to ChromaDB.
    """
    if CHROMADB_AVAILABLE and chroma_client:
        try:
            # Heartbeat is a lightweight check to see if the service is up
            chroma_client.heartbeat()
            chroma_status = "connected"
        except Exception as e:
            logger.error(f"Health check failed to connect to ChromaDB: {e}")
            chroma_status = "disconnected"
    else:
        chroma_status = "disabled"

    return jsonify({
        "status": "healthy" if chroma_status in ["connected", "disabled"] else "unhealthy",
        "service": "PocketPro:SBA Backend",
        "dependencies": {
            "chromadb": chroma_status
        }
    })

@app.route('/api/info')
def get_info():
    """Returns basic information about the application state."""
    doc_count = rag_collection.count() if rag_collection else 0
    return jsonify({
        "service_name": "PocketPro:SBA",
        "version": "1.0.0",
        "rag_status": "enabled" if CHROMADB_AVAILABLE else "disabled",
        "document_count": doc_count
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Handles chat requests, performing RAG to answer questions based on documents.
    """
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Message is required"}), 400

    user_query = data['message']

    if not CHROMADB_AVAILABLE or not llm:
        return jsonify({
            "response": "I'm sorry, the RAG system is currently unavailable. I can only have a basic conversation.",
            "sources": []
        })
 
    try:
        # 1. Retrieve relevant documents from ChromaDB
        retrieved_docs = rag_collection.query(
            query_texts=[user_query],
            n_results=3
        )
 
        # 2. Build the context for the LLM
        context = ""
        sources = []
        if retrieved_docs and retrieved_docs.get('documents') and retrieved_docs['documents'][0]:
            context = "\n\n".join(retrieved_docs['documents'][0])
            sources = [
                {
                    "id": mid, 
                    "metadata": meta, 
                    "distance": f"{dist:.4f}" # Format distance for clarity
                } for mid, meta, dist in zip(retrieved_docs['ids'][0], retrieved_docs['metadatas'][0], retrieved_docs['distances'][0])
            ]
 
        # 3. Construct the prompt for the LLM
        prompt = f"""
        You are PocketPro, an expert assistant for the Small Business Administration (SBA).
        Answer the user's question based on the following context.
        If the context is not relevant, answer the question to the best of your ability but mention that the information is not from the provided documents.

        Context:
        ---
        {context if context else "No relevant documents found."}
        ---

        User Question: {user_query}
        """

        # 4. Generate response from the LLM
        llm_response = llm.generate_content(prompt)
        
        return jsonify({
            "response": llm_response.text,
            "sources": sources
        })

    except Exception as e:
        logger.error(f"Error during chat processing: {e}", exc_info=True)
        return jsonify({"error": "An error occurred while processing your request."}), 500

# --- Serve React Frontend ---
# This catch-all route should be registered LAST. It serves the React app's index.html
# for any path that is not an API route, allowing client-side routing to take over.
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# Note: The `if __name__ == '__main__':` block is removed because Gunicorn
# is used to run the application in production. The `app` object is the entry point.
