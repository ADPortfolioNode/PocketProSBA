# PowerShell diagnostic script for PocketPro:SBA Docker setup
# Run this script when containers fail to start or connect properly

Write-Host "=== PocketPro:SBA Docker Diagnostics ===" -ForegroundColor Cyan

# Check if containers are running
Write-Host "Checking container status..." -ForegroundColor Yellow
docker ps -a

# Check if containers have the correct names
Write-Host "`nVerifying container names..." -ForegroundColor Yellow
docker ps -a --format "{{.Names}}" | Select-String "pocketprosba"

# Check networking
Write-Host "`nChecking network connectivity between containers..." -ForegroundColor Yellow
Write-Host "Backend to Frontend:" -ForegroundColor Green
docker exec pocketprosba-backend-1 curl -s -o /dev/null -w "%{http_code}" http://pocketprosba-frontend-1:3000
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to connect" -ForegroundColor Red
}

Write-Host "Nginx to Backend:" -ForegroundColor Green
docker exec pocketprosba-nginx-1 curl -s -o /dev/null -w "%{http_code}" http://pocketprosba-backend-1:5000/health
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to connect" -ForegroundColor Red
}

# Check logs
Write-Host "`nBackend logs (last 20 lines):" -ForegroundColor Yellow
docker logs pocketprosba-backend-1 --tail 20

Write-Host "`nFrontend logs (last 20 lines):" -ForegroundColor Yellow
docker logs pocketprosba-frontend-1 --tail 20

Write-Host "`nNginx logs (last 20 lines):" -ForegroundColor Yellow
docker logs pocketprosba-nginx-1 --tail 20

# Check nginx configuration
Write-Host "`nVerifying Nginx configuration:" -ForegroundColor Yellow
docker exec pocketprosba-nginx-1 cat /etc/nginx/conf.d/default.conf

# Cleanup instructions
Write-Host "`n=== Troubleshooting Steps ===" -ForegroundColor Cyan
Write-Host "1. If containers have wrong names:" -ForegroundColor Green
Write-Host "   - Stop and remove all containers: docker-compose down"
Write-Host "   - Rebuild: docker-compose up --build"
Write-Host ""
Write-Host "2. If nginx can't connect to backend:" -ForegroundColor Green
Write-Host "   - Verify service names in nginx.conf match container names"
Write-Host "   - Check if backend is healthy: docker exec pocketprosba-backend-1 curl localhost:5000/health"
Write-Host ""
Write-Host "3. If backend has Python errors:" -ForegroundColor Green
Write-Host "   - Check app.py for syntax errors"
Write-Host "   - Verify dependencies are installed correctly"
Write-Host ""
Write-Host "4. To restart individual services:" -ForegroundColor Green
Write-Host "   - docker-compose restart backend"
Write-Host "   - docker-compose restart frontend"
Write-Host "   - docker-compose restart nginx"
