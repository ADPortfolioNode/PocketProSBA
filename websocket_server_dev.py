# WebSocket server for Flask (development only)
# This file should be used only in local/dev environments

from flask import Flask, request
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return "WebSocket server running on Flask dev port 5000"

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('message', {'data': 'Connected to Flask WebSocket server'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('message')
def handle_message(data):
    print('Received message:', data)
    emit('message', {'data': f"Echo: {data}"})

if __name__ == '__main__':
    # Only run in development
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
