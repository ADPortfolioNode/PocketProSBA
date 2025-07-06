"""
Minimal application for Render.com deployment testing
"""
import os
from flask import Flask, jsonify

# Create the application
app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "message": "PocketPro SBA API is running",
        "status": "online",
        "port": os.environ.get("PORT", "not set")
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy", 
        "success": True
    })

@app.route('/env')
def env():
    """Return environment information for debugging"""
    env_vars = {
        "PORT": os.environ.get("PORT", "not set"),
        "FLASK_ENV": os.environ.get("FLASK_ENV", "not set"),
        "PYTHONPATH": os.environ.get("PYTHONPATH", "not set"),
        "FLASK_APP": os.environ.get("FLASK_APP", "not set")
    }
    return jsonify(env_vars)

# For Gunicorn
application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting minimal app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
