import os
import logging
from dotenv import load_dotenv
from app import app, socketio
from flask import send_from_directory, abort, jsonify
from flask_cors import CORS

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Enable CORS for React dev server
CORS(app, origins=["http://localhost:3000"])

# Path to React build directory (absolute path for reliability)
REACT_BUILD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build'))

# Serve React build files (only for non-API routes)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    # If the request is for an API route, return 404
    if path.startswith("api/"):
        abort(404)
    # Serve static files if they exist
    file_path = os.path.join(REACT_BUILD_DIR, path)
    if path != "" and os.path.exists(file_path):
        return send_from_directory(REACT_BUILD_DIR, path)
    # Serve index.html for all other routes (SPA fallback)
    index_path = os.path.join(REACT_BUILD_DIR, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(REACT_BUILD_DIR, "index.html")
    else:
        return "Build directory not found. Please build the frontend.", 500

# Example API endpoint (replace or expand as needed)
@app.route('/api/api', methods=['GET'])
def api_registry():
    return jsonify({"status": "ok", "message": "API registry endpoint working"}), 200

if __name__ == "__main__":
    # Get port from environment variable (for Render.com compatibility)
    port = int(os.environ.get("PORT", 5000))
    
    # Set debug mode based on environment (default to production)
    debug = os.environ.get("FLASK_ENV", "production") == "development"
    
    logger.info(f"🚀 Starting PocketPro SBA RAG Application on port {port}")
    logger.info(f"Environment: {'development' if debug else 'production'}")
    
    # Start the application with SocketIO
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
