# PowerShell script to clean up and restart PocketPro:SBA

Write-Host "=== Clean up and restart PocketPro:SBA ===" -ForegroundColor Cyan

# Stop and remove all containers
Write-Host "Stopping and removing existing containers..." -ForegroundColor Yellow
docker-compose down

# Remove any stale images
Write-Host "Removing stale images..." -ForegroundColor Yellow
$staleImages = docker images -q 'pocketprosba-*'
if ($staleImages) {
    docker rmi $staleImages
}

# Clean up any dangling volumes and networks
Write-Host "Cleaning up dangling resources..." -ForegroundColor Yellow
docker system prune -f

# Rebuild and start the application
Write-Host "Rebuilding and starting the application..." -ForegroundColor Green
docker-compose up --build -d

# Check container status
Write-Host "Checking container status..." -ForegroundColor Yellow
docker ps

Write-Host "=== Startup complete ===" -ForegroundColor Cyan
Write-Host "Access the application at: http://localhost:10000" -ForegroundColor Green
Write-Host "To check logs: docker-compose logs -f" -ForegroundColor Green
