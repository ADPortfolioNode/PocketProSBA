# PowerShell script to fix backend and frontend files

Write-Host "Fixing all application files..." -ForegroundColor Cyan

# Fix backend app.py
if (Test-Path "e:\2024 RESET\PocketProSBA\app.py.fixed") {
    Write-Host "Replacing app.py with fixed version..." -ForegroundColor Yellow
    Copy-Item -Path "e:\2024 RESET\PocketProSBA\app.py.fixed" -Destination "e:\2024 RESET\PocketProSBA\app.py" -Force
    Remove-Item -Path "e:\2024 RESET\PocketProSBA\app.py.fixed" -Force
}

# Fix frontend App.js
if (Test-Path "e:\2024 RESET\PocketProSBA\frontend\src\App.js.fixed") {
    Write-Host "Replacing App.js with fixed version..." -ForegroundColor Yellow
    Copy-Item -Path "e:\2024 RESET\PocketProSBA\frontend\src\App.js.fixed" -Destination "e:\2024 RESET\PocketProSBA\frontend\src\App.js" -Force
    Remove-Item -Path "e:\2024 RESET\PocketProSBA\frontend\src\App.js.fixed" -Force
}

# Check if docker is running
$docker = Get-Process -Name "docker" -ErrorAction SilentlyContinue
if ($docker) {
    Write-Host "Rebuilding and restarting containers..." -ForegroundColor Green
    
    # Move to the project directory
    Set-Location "e:\2024 RESET\PocketProSBA"
    
    # Stop containers
    docker-compose down
    
    # Rebuild and restart
    docker-compose up -d --build
    
    # Show running containers
    docker ps
} else {
    Write-Host "Docker Desktop is not running. Please start Docker Desktop and run 'docker-compose up -d --build'" -ForegroundColor Yellow
}

Write-Host "All fixes applied!" -ForegroundColor Cyan
Write-Host "Access the application at: http://localhost:10000" -ForegroundColor Green
