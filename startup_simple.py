"""
Minimal startup script for Render deployment
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS

# Create minimal app for immediate startup
app = Flask(__name__)
CORS(app)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'PocketPro SBA'})

@app.route('/')
def home():
    return jsonify({'message': 'PocketPro SBA is running', 'status': 'operational'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
