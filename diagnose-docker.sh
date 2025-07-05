#!/bin/bash
# Docker container diagnostics script for PocketPro:SBA
# Run this script when containers fail to start or connect properly

echo "=== PocketPro:SBA Docker Diagnostics ==="

# Check if containers are running
echo "Checking container status..."
docker ps -a

# Check if containers have the correct names
echo -e "\nVerifying container names..."
docker ps -a --format "{{.Names}}" | grep pocketprosba

# Check networking
echo -e "\nChecking network connectivity between containers..."
echo "Backend to Frontend:"
docker exec pocketprosba-backend-1 curl -s -o /dev/null -w "%{http_code}" http://pocketprosba-frontend-1:3000 || echo "Failed to connect"

echo "Nginx to Backend:"
docker exec pocketprosba-nginx-1 curl -s -o /dev/null -w "%{http_code}" http://pocketprosba-backend-1:5000/health || echo "Failed to connect"

# Check logs
echo -e "\nBackend logs (last 20 lines):"
docker logs pocketprosba-backend-1 --tail 20

echo -e "\nFrontend logs (last 20 lines):"
docker logs pocketprosba-frontend-1 --tail 20

echo -e "\nNginx logs (last 20 lines):"
docker logs pocketprosba-nginx-1 --tail 20

# Check nginx configuration
echo -e "\nVerifying Nginx configuration:"
docker exec pocketprosba-nginx-1 cat /etc/nginx/conf.d/default.conf

# Cleanup instructions
echo -e "\n=== Troubleshooting Steps ==="
echo "1. If containers have wrong names:"
echo "   - Stop and remove all containers: docker-compose down"
echo "   - Rebuild: docker-compose up --build"
echo ""
echo "2. If nginx can't connect to backend:"
echo "   - Verify service names in nginx.conf match container names"
echo "   - Check if backend is healthy: docker exec pocketprosba-backend-1 curl localhost:5000/health"
echo ""
echo "3. If backend has Python errors:"
echo "   - Check app.py for syntax errors"
echo "   - Verify dependencies are installed correctly"
echo ""
echo "4. To restart individual services:"
echo "   - docker-compose restart backend"
echo "   - docker-compose restart frontend"
echo "   - docker-compose restart nginx"
