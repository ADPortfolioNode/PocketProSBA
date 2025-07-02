#!/bin/bash
echo "Starting PocketPro:SBA Edition (Backend and Frontend)..."

# Start the backend in the background
python run.py &
BACKEND_PID=$!

# Wait a moment for the backend to initialize
echo "Waiting for backend to initialize..."
sleep 5

# Start the frontend
cd frontend
echo "Starting frontend..."
npm start

# Clean up backend process when frontend is closed
trap "kill $BACKEND_PID" EXIT
