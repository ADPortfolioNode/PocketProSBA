"""
Windows-compatible server for local testing
Uses Flask's built-in development server instead of Gunicorn
"""
import os
import sys
from minimal_app import app

if __name__ == "__main__":
    # Get PORT from environment (critical for Render.com)
    PORT = int(os.environ.get('PORT', 5000))
    
    # Run the Flask app using the built-in server
    app.run(host='0.0.0.0', port=PORT, debug=True)
