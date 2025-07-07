# PowerShell script to fix the frontend container

Write-Host "Fixing frontend container..." -ForegroundColor Cyan

# Replace the Dockerfile
Copy-Item -Path "e:\2024 RESET\PocketProSBA\frontend\Dockerfile.new" -Destination "e:\2024 RESET\PocketProSBA\frontend\Dockerfile" -Force

# Check if Docker is running
$docker = Get-Process -Name "docker" -ErrorAction SilentlyContinue
if ($docker) {
    # Stop and remove frontend container
    Write-Host "Stopping frontend container..." -ForegroundColor Yellow
    docker-compose stop frontend
    docker-compose rm -f frontend
    
    # Rebuild the frontend container
    Write-Host "Rebuilding frontend container..." -ForegroundColor Green
    docker-compose up -d --build frontend
    
    # Show running containers
    Write-Host "Container status:" -ForegroundColor Cyan
    docker ps
    
    Write-Host "Frontend has been rebuilt!" -ForegroundColor Green
    Write-Host "Please wait a moment and then access the application at: http://localhost:10000" -ForegroundColor Green
} else {
    Write-Host "Docker Desktop is not running. Please start Docker Desktop first." -ForegroundColor Yellow
}

Write-Host "Rebuilding frontend container..." -ForegroundColor Cyan

# Stop the frontend container
docker-compose stop frontend

# Remove the frontend container
docker-compose rm -f frontend

# Rebuild the frontend container
docker-compose up -d --build frontend

Write-Host "Frontend container has been rebuilt and restarted!" -ForegroundColor Green
