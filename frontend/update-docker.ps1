# PowerShell script to update frontend Docker container

Write-Host "Rebuilding and restarting frontend container..." -ForegroundColor Cyan

# Check if docker is running
$docker = Get-Process -Name "docker" -ErrorAction SilentlyContinue
if ($docker) {
    # Rebuild and restart just the frontend container
    docker-compose up -d --build frontend
    
    # Show running containers
    docker ps
} else {
    Write-Host "Docker Desktop is not running. Please start Docker Desktop and run 'docker-compose up -d --build frontend'" -ForegroundColor Yellow
}

Write-Host "Frontend container has been updated!" -ForegroundColor Green
Write-Host "Access the application at: http://localhost:10000" -ForegroundColor Green
