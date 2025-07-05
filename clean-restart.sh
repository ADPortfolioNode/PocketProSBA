#!/bin/bash
# Script to clean up and restart PocketPro:SBA

echo "=== Clean up and restart PocketPro:SBA ==="

# Stop and remove all containers
echo "Stopping and removing existing containers..."
docker-compose down

# Remove any stale images
echo "Removing stale images..."
docker rmi $(docker images -q 'pocketprosba-*') 2>/dev/null || true

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
