#!/bin/bash
# Render.com start script for PocketPro SBA Assistant

echo "Starting PocketPro SBA Assistant..."

# Get port from environment or default to 5000
PORT=${PORT:-5000}

# Start the application with gunicorn
gunicorn app:app \
  --bind 0.0.0.0:$PORT \
  --workers 2 \
  --timeout 120 \
  --keepalive 2 \
  --max-requests 1000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
