#!/bin/bash
# Development startup script for PocketPro:SBA Edition

echo "=== PocketPro:SBA Edition Development Setup ==="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.template .env
    echo "Please edit .env file with your API keys and configuration"
    echo "Required: GEMINI_API_KEY"
    exit 1
fi

# Source environment variables
source .env

# Check for required environment variables
if [ -z "$GEMINI_API_KEY" ]; then
    echo "Error: GEMINI_API_KEY is required"
    echo "Please set it in your .env file"
    exit 1
fi

# Create necessary directories
mkdir -p uploads
mkdir -p chromadb_data
mkdir -p logs

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo "=== Starting Development Servers ==="

# Start backend in development mode
echo "Starting backend server..."
python run.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start frontend development server
echo "Starting frontend development server..."
cd frontend
npm start &
FRONTEND_PID=$!

echo "=== Servers Started ==="
echo "Backend: http://localhost:5000"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop all servers"

# Function to cleanup on exit
cleanup() {
    echo "Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit
}

# Trap Ctrl+C
trap cleanup INT

# Wait for processes
wait
