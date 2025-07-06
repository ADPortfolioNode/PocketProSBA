#!/usr/bin/env python3
"""
Minimal Flask app for Render.com deployment testing
This version strips down to essentials to ensure deployment works
"""
import os
import sys
from pathlib import Path
from flask import Flask, jsonify
from flask_cors import CORS

# Set up the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Create minimal Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')
CORS(app)

# Export for Gunicorn to find
application = app

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
        "port": os.environ.get('PORT', '5000')
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "PocketPro:SBA",
        "environment": os.environ.get('FLASK_ENV', 'unknown'),
        "port": os.environ.get('PORT', 'unknown')
    })

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

# For Gunicorn
application = app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))  # Default to 10000 for Render
    print(f"🚀 Starting minimal app on host=0.0.0.0, port={port}")
    app.run(host='0.0.0.0', port=port, debug=False)
