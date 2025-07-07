#!/bin/bash
# Script to ensure Gunicorn uses the correct PORT from environment variable
# Fix for Render.com deployment

# Print environment for debugging
echo "=== Environment Variables ==="
echo "PORT=$PORT"
echo "FLASK_APP=$FLASK_APP"
echo "FLASK_ENV=$FLASK_ENV"

# Run the port debugging script
python debug_port_binding.py

# Force Gunicorn to use the PORT environment variable
export GUNICORN_CMD_ARGS="--bind=0.0.0.0:$PORT --timeout=60 --workers=2 --access-logfile=- --error-logfile=-"

echo "=== Starting Gunicorn with fixed configuration ==="
echo "Using PORT: $PORT"

# Execute Gunicorn with our fixed configuration
exec gunicorn --config=gunicorn_render_fixed.py app:app
