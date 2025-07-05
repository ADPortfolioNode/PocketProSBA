#!/bin/bash
# Test script for PocketPro:SBA Render.com deployment
# This script verifies the Docker build and basic functionality
# Run from the project root directory

echo "==== PocketPro:SBA Render.com Deployment Test ===="
echo "Testing Dockerfile.render build and functionality"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

echo "🔍 Step 1: Building Docker image using Dockerfile.render..."
docker build -t pocketpro-sba-render -f Dockerfile.render .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    exit 1
fi
echo "✅ Docker build successful!"

echo ""
echo "🔍 Step 2: Starting container for testing..."
CONTAINER_ID=$(docker run -d -p 10000:10000 -e PORT=10000 -e FLASK_ENV=production -e GEMINI_API_KEY=dummy-key pocketpro-sba-render)

if [ -z "$CONTAINER_ID" ]; then
    echo "❌ Failed to start Docker container!"
    exit 1
fi

echo "✅ Container started with ID: $CONTAINER_ID"
echo "⏳ Waiting 10 seconds for application to initialize..."
sleep 10

echo ""
echo "🔍 Step 3: Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:10000/health)

if [ "$HEALTH_RESPONSE" != "200" ]; then
    echo "❌ Health check failed with status: $HEALTH_RESPONSE"
    docker logs $CONTAINER_ID
    docker stop $CONTAINER_ID
    exit 1
fi

echo "✅ Health check endpoint responded with status 200!"

echo ""
echo "🔍 Step 4: Checking API info endpoint..."
API_RESPONSE=$(curl -s http://localhost:10000/api/info)
echo "API info response: $API_RESPONSE"

echo ""
echo "🔍 Step 5: Checking logs for any errors..."
docker logs $CONTAINER_ID | grep -i error

echo ""
echo "🔍 Step 6: Cleanup..."
docker stop $CONTAINER_ID
docker rm $CONTAINER_ID

echo ""
echo "==== Test Summary ===="
echo "✅ Docker build: Successful"
echo "✅ Application startup: Successful"
echo "✅ Health check: Successful"
echo "✅ API check: Completed"
echo ""
echo "The Dockerfile.render appears to be ready for Render.com deployment!"
echo "Next steps: Deploy to Render.com using the provided render.yaml configuration."
