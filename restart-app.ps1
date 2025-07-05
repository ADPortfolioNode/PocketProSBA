# PowerShell script to restart PocketPro:SBA with fixed settings

Write-Host "=== Restarting PocketPro:SBA with fixed settings ===" -ForegroundColor Cyan

# Stop and remove all containers
Write-Host "Stopping and removing existing containers..." -ForegroundColor Yellow
docker-compose down

# Clean up any dangling volumes and networks
Write-Host "Cleaning up dangling resources..." -ForegroundColor Yellow
docker system prune -f

# Rebuild and start the application
Write-Host "Rebuilding and starting the application..." -ForegroundColor Yellow
docker-compose up --build -d

# Check container status
Write-Host "Checking container status..." -ForegroundColor Yellow
docker ps

Write-Host "=== Startup complete ===" -ForegroundColor Green
Write-Host "Access the application at: http://localhost:10000"
Write-Host "To check logs: docker-compose logs -f"
Write-Host "To run diagnostics: ./diagnose-docker.ps1"
