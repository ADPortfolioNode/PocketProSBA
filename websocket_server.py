#!/usr/bin/env python3
"""
WebSocket server for PocketPro SBA
Provides real-time communication between frontend and backend
"""

import os
import logging
from flask import Flask, request
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Configure CORS for WebSocket
CORS(app, origins=[
    "http://localhost:3000",
    "http://localhost:5000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5000"
])

# Initialize SocketIO with CORS
socketio = SocketIO(app, 
    cors_allowed_origins=[
        "http://localhost:3000",
        "http://localhost:5000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5000"
    ],
    logger=True,
    engineio_logger=True
)

# Store connected clients
connected_clients = {}

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_id = request.sid
    connected_clients[client_id] = {
        'connected_at': datetime.utcnow().isoformat(),
        'ip': request.remote_addr
    }
    logger.info(f"Client {client_id} connected from {request.remote_addr}")
    
    # Send connection confirmation
    emit('status', {
        'status': 'connected',
        'client_id': client_id,
        'timestamp': datetime.utcnow().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid
    if client_id in connected_clients:
        del connected_clients[client_id]
    logger.info(f"Client {client_id} disconnected")

@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle chat messages from clients"""
    client_id = request.sid
    logger.info(f"Received message from {client_id}: {data}")
    
    try:
        message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        # Send processing status
        emit('status', {
            'status': 'processing',
            'message': 'Processing your request...',
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Simulate processing (replace with actual RAG processing)
        import time
        time.sleep(0.5)  # Simulate processing time
        
        # Send response
        response = f"Echo: {message}"
        emit('chat_response', {
            'response': response,
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Send completion status
        emit('status', {
            'status': 'completed',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        emit('status', {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        })

@socketio.on('health_check')
def handle_health_check():
    """Handle health check requests"""
    emit('health_status', {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'connected_clients': len(connected_clients)
    })

@app.route('/health')
def health_check():
    """HTTP health check endpoint"""
    return {
        'status': 'healthy',
        'websocket_clients': len(connected_clients),
        'timestamp': datetime.utcnow().isoformat()
    }

@app.route('/')
def index():
    """Root endpoint"""
    return "PocketPro SBA WebSocket Server is running"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    logger.info(f"Starting WebSocket server on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
