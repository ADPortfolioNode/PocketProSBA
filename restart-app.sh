#!/bin/bash
# Script to restart PocketPro:SBA with fixed settings

echo "=== Restarting PocketPro:SBA with fixed settings ==="

# Stop and remove all containers
echo "Stopping and removing existing containers..."
docker-compose down

# Clean up any dangling volumes and networks
echo "Cleaning up dangling resources..."
docker system prune -f

# Rebuild and start the application
echo "Rebuilding and starting the application..."
docker-compose up --build -d

# Check container status
echo "Checking container status..."
docker ps

echo "=== Startup complete ==="
echo "Access the application at: http://localhost:10000"
echo "To check logs: docker-compose logs -f"
echo "To run diagnostics: ./diagnose-docker.sh"
