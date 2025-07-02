from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)

# Configure CORS
# For development, we can allow all origins
if os.environ.get('FLASK_ENV') == 'development':
    CORS(app, resources={r"/api/*": {"origins": "*"}})
else:
    # For production, restrict to specific domains
    allowed_origins = [
        "https://your-app.render.com",  # Update with your Render domain
        "http://localhost:3000",        # Local React development server
        "http://localhost:10000"        # Docker setup
    ]
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

# ...existing code...