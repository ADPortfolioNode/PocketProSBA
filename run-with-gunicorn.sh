#!/bin/bash
# Run the Flask application with Gunicorn locally
# This simulates how Render.com will run the application

echo "Starting Flask application with Gunicorn..."
echo "This simulates how Render.com will run the application"

# Ensure Gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo "Gunicorn not found. Installing..."
    pip install gunicorn
fi

# Set environment variables
export PORT=5000
export FLASK_ENV=production
export FLASK_APP=minimal_app.py
export PYTHONUNBUFFERED=1

echo "Binding to 0.0.0.0:$PORT"

# Start Gunicorn with the same configuration as Render.com
gunicorn --bind 0.0.0.0:$PORT --config=gunicorn.render.conf.py minimal_app:app
