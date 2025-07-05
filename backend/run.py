import os
import logging
from dotenv import load_dotenv
from app import app, socketio

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

if __name__ == "__main__":
    # Get port from environment variable (for Render.com compatibility)
    port = int(os.environ.get("PORT", 5000))
    
    # Set debug mode based on environment
    debug = os.environ.get("FLASK_ENV", "production") == "development"
    
    logger.info(f"🚀 Starting PocketPro SBA RAG Application on port {port}")
    logger.info(f"Environment: {'development' if debug else 'production'}")
    
    # Start the application with SocketIO
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
