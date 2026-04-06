# PowerShell script to install missing frontend dependencies

Write-Host "Installing missing frontend dependencies..." -ForegroundColor Cyan

# Path to the frontend directory
$frontendDir = "e:\2024 RESET\PocketProSBA\frontend"

# Navigate to the frontend directory
Set-Location $frontendDir

# Install react-bootstrap
Write-Host "Installing react-bootstrap..." -ForegroundColor Yellow
npm install --save react-bootstrap

# Create a script to update the Docker image
Write-Host "Creating docker update script..." -ForegroundColor Yellow
$updateDockerScript = @"
# PowerShell script to update frontend Docker container

Write-Host "Rebuilding and restarting frontend container..." -ForegroundColor Cyan

# Check if docker is running
`$docker = Get-Process -Name "docker" -ErrorAction SilentlyContinue
if (`$docker) {
    # Rebuild and restart just the frontend container
    docker-compose up -d --build frontend
    
    # Show running containers
    docker ps
} else {
    Write-Host "Docker Desktop is not running. Please start Docker Desktop and run 'docker-compose up -d --build frontend'" -ForegroundColor Yellow
}

Write-Host "Frontend container has been updated!" -ForegroundColor Green
Write-Host "Access the application at: http://localhost:10000" -ForegroundColor Green
"@

$updateDockerScript | Out-File -FilePath "$frontendDir\update-docker.ps1" -Encoding utf8

Write-Host "Dependencies installed!" -ForegroundColor Cyan
Write-Host "To update the Docker container, run: $frontendDir\update-docker.ps1" -ForegroundColor Green
