#!/bin/bash
# Render.com build script for PocketPro SBA Assistant

echo "Starting build process..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Run minimal deployment setup if needed
if [ -f "deploy_minimal.py" ]; then
    echo "Running minimal deployment setup..."
    python deploy_minimal.py
fi

echo "Build process complete!"
