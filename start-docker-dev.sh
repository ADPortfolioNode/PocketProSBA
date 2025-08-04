#!/bin/bash

# Enable Docker BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Clean up any existing containers
echo "Cleaning up existing containers..."
docker-compose down --remove-orphans

# Build and start services
echo "Building and starting services..."
docker-compose build --no-cache
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check service status
echo "Checking service status..."
docker-compose ps

# Show logs
echo "Showing recent logs..."
docker-compose logs --tail=50

echo "Services started!"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:5000"
echo "Nginx Proxy: http://localhost:10000"
