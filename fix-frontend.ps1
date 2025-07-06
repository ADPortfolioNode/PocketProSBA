# PowerShell script to fix frontend syntax errors

Write-Host "Fixing frontend syntax errors..." -ForegroundColor Cyan

# Path to the frontend directory
$frontendDir = "e:\2024 RESET\PocketProSBA\frontend"

# Fix App.js
if (Test-Path "$frontendDir\src\App.js.fixed") {
    Write-Host "Replacing App.js with fixed version..." -ForegroundColor Yellow
    Copy-Item -Path "$frontendDir\src\App.js.fixed" -Destination "$frontendDir\src\App.js" -Force
    Remove-Item -Path "$frontendDir\src\App.js.fixed" -Force
}

# Check if docker is running
$docker = Get-Process -Name "docker" -ErrorAction SilentlyContinue
if ($docker) {
    Write-Host "Rebuilding and restarting frontend container..." -ForegroundColor Green
    docker-compose up -d --build frontend
} else {
    Write-Host "Docker Desktop is not running. Please start Docker Desktop and run 'docker-compose up -d --build frontend'" -ForegroundColor Yellow
}

Write-Host "Frontend fixes applied!" -ForegroundColor Cyan
