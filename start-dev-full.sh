#!/bin/bash
echo "Starting PocketPro:SBA Edition (Backend and Frontend)..."

# Start the backend in the background
FLASK_ENV=development gunicorn wsgi:application --bind 0.0.0.0:5000 --reload --workers 1 --threads 4 --timeout 120 &
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
