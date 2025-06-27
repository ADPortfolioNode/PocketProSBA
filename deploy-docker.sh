#!/bin/bash
# Docker deployment script for PocketPro:SBA Edition

echo "=== PocketPro:SBA Edition Docker Deployment ==="

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

echo "Building and starting containers..."

# Stop any existing containers
docker-compose down

# Build and start services
docker-compose up --build -d

echo "=== Deployment Complete ==="
echo "Application: http://localhost:10000"
echo "Backend API: http://localhost:5000"
echo "ChromaDB: http://localhost:8000"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
