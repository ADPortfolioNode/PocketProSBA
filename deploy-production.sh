#!/bin/bash
# Production Deployment Script for PocketPro:SBA
# Validates and deploys the production Docker setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 PocketPro:SBA Production Deployment${NC}"
echo "======================================"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi

# Check .env file
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo "Please create .env file with required environment variables"
    exit 1
fi

# Check required environment variables
required_vars=("GEMINI_API_KEY" "SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}❌ $var is not set in .env${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Build and start services
echo -e "${YELLOW}Building production Docker images...${NC}"
docker-compose build --no-cache

echo -e "${YELLOW}Starting production services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 30

# Health check
echo -e "${YELLOW}Performing health checks...${NC}"

# Check backend health
backend_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health || echo "000")
if [ "$backend_health" = "200" ]; then
    echo -e "${GREEN}✅ Backend health check passed${NC}"
else
    echo -e "${RED}❌ Backend health check failed (HTTP $backend_health)${NC}"
fi

# Check ChromaDB health
chroma_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/heartbeat || echo "000")
if [ "$chroma_health" = "200" ]; then
    echo -e "${GREEN}✅ ChromaDB health check passed${NC}"
else
    echo -e "${RED}❌ ChromaDB health check failed (HTTP $chroma_health)${NC}"
fi

# Display service status
echo -e "${YELLOW}Service status:${NC}"
docker-compose ps

# Display logs
echo -e "${YELLOW}Recent logs:${NC}"
docker-compose logs --tail=20

echo -e "${GREEN}🎉 Production deployment complete!${NC}"
echo "====================================="
echo "Application is running at: http://localhost:5000"
echo "ChromaDB is running at: http://localhost:8000"
echo ""
echo "To stop services: docker-compose down"
echo "To view logs: docker-compose logs -f"
