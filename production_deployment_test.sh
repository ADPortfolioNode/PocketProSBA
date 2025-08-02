#!/bin/bash
# Automated script for single point full production testing of Render.com deployment

# Set base URL of the deployed backend service
BASE_URL="http://your-production-backend-url"  # Replace with actual URL

echo "Starting full production deployment tests..."

# 1. Health check endpoint
echo "Testing health endpoint..."
curl -f "${BASE_URL}/health" && echo "Health check passed." || { echo "Health check failed!"; exit 1; }

# 2. Redis connectivity test (assuming an endpoint exists to verify Redis)
echo "Testing Redis connectivity..."
curl -f "${BASE_URL}/redis-test" && echo "Redis connectivity test passed." || { echo "Redis connectivity test failed!"; exit 1; }

# 3. ChromaDB connectivity test (assuming an endpoint exists to verify ChromaDB)
echo "Testing ChromaDB connectivity..."
curl -f "${BASE_URL}/chromadb-test" && echo "ChromaDB connectivity test passed." || { echo "ChromaDB connectivity test failed!"; exit 1; }

# 4. Environment variable validation (assuming an endpoint to dump env vars securely)
echo "Validating environment variables..."
curl -f "${BASE_URL}/env-check" && echo "Environment variable validation passed." || { echo "Environment variable validation failed!"; exit 1; }

echo "All production deployment tests passed successfully."
