# PowerShell script to update Docker files and rebuild frontend

Write-Host "Updating frontend Docker configuration..." -ForegroundColor Cyan

# Path to the frontend directory
$frontendDir = "e:\2024 RESET\PocketProSBA\frontend"

# Backup the original Dockerfile
if (-not (Test-Path "$frontendDir\Dockerfile.backup")) {
    Write-Host "Backing up original Dockerfile..." -ForegroundColor Yellow
    Copy-Item -Path "$frontendDir\Dockerfile" -Destination "$frontendDir\Dockerfile.backup" -Force
}

# Use the updated Dockerfile
Write-Host "Applying updated Dockerfile..." -ForegroundColor Yellow
Copy-Item -Path "$frontendDir\Dockerfile.updated" -Destination "$frontendDir\Dockerfile" -Force

# Create a standalone update script
$rebuildScript = @"
# PowerShell script to rebuild the frontend Docker container

Write-Host "Rebuilding and restarting frontend container..." -ForegroundColor Cyan

# Check if Docker is running
`$docker = Get-Process -Name "docker" -ErrorAction SilentlyContinue
if (`$docker) {
    # Rebuild and restart the frontend container
    docker-compose up -d --build frontend
    
    # Show running containers
    docker ps
} else {
    Write-Host "Docker Desktop is not running. Please start Docker Desktop and run 'docker-compose up -d --build frontend'" -ForegroundColor Yellow
}

Write-Host "Frontend container has been updated!" -ForegroundColor Green
Write-Host "Access the application at: http://localhost:3000" -ForegroundColor Green
"@

$rebuildScript | Out-File -FilePath "e:\2024 RESET\PocketProSBA\rebuild-frontend.ps1" -Encoding utf8

Write-Host "Update complete!" -ForegroundColor Cyan
Write-Host "To rebuild the frontend container, run: e:\2024 RESET\PocketProSBA\rebuild-frontend.ps1" -ForegroundColor Green
Write-Host "To rebuild the frontend container, run: e:\2024 RESET\PocketProSBA\rebuild-frontend.ps1" -ForegroundColor Green
