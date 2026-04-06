# PowerShell script to rebuild the frontend Docker container

Write-Host "Rebuilding frontend container..." -ForegroundColor Cyan

# Check if Docker is running
$docker = Get-Process -Name "docker" -ErrorAction SilentlyContinue
if ($docker) {
    # Rebuild and restart the frontend container
    Set-Location "e:\2024 RESET\PocketProSBA"
    docker-compose up -d --build frontend
    
    # Show running containers
    docker ps
} else {
    Write-Host "Docker Desktop is not running. Please start Docker Desktop first." -ForegroundColor Yellow
}

Write-Host "Frontend container updated!" -ForegroundColor Green
Write-Host "Access the application at: http://localhost:10000" -ForegroundColor Green
