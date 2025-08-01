# Production deployment script for PocketPro:SBA Edition
# Usage: ./deploy-production.ps1

param (
    [string]$environment = "local"
)

$ErrorActionPreference = "Stop"

Write-Host "===== PocketPro:SBA Production Deployment =====" -ForegroundColor Cyan
Write-Host "Environment: $environment" -ForegroundColor Yellow
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check Docker
try {
    $dockerVersion = docker --version
    Write-Host "[√] Docker is installed: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "[X] Docker is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check Docker Compose
try {
    $composeVersion = docker-compose --version
    Write-Host "[√] Docker Compose is installed: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "[X] Docker Compose is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check environment file
if (Test-Path ".env") {
    Write-Host "[√] Environment file exists" -ForegroundColor Green
    
    # Check for required environment variables
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "GEMINI_API_KEY=AIzaSy") {
        Write-Host "[√] GEMINI_API_KEY is configured" -ForegroundColor Green
    } else {
        Write-Host "[!] WARNING: GEMINI_API_KEY may not be properly configured" -ForegroundColor Yellow
    }
} else {
    Write-Host "[X] .env file not found. Creating from template..." -ForegroundColor Red
    if (Test-Path ".env.template") {
        Copy-Item ".env.template" ".env"
        Write-Host "Please edit .env file with your configuration" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "Starting production deployment..." -ForegroundColor Yellow

# Stop any existing containers
Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml down

# Build and start production containers
Write-Host "Building and starting production containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml up --build -d

# Wait for services to start
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Run health checks
Write-Host "Running health checks..." -ForegroundColor Yellow
$healthCheck = $false
$maxRetries = 10
$retryCount = 0

while (-not $healthCheck -and $retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/correction/api/health" -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            $healthCheck = $true
            Write-Host "[√] Backend health check passed" -ForegroundColor Green
        }
    } catch {
        $retryCount++
        Write-Host "[!] Health check attempt $retryCount failed, retrying..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    }
}

if ($healthCheck) {
    Write-Host ""
    Write-Host "===== Deployment Successful =====" -ForegroundColor Green
    Write-Host "Application is running at:" -ForegroundColor White
    Write-Host "Frontend: http://localhost" -ForegroundColor Green
    Write-Host "Backend API: http://localhost:5000" -ForegroundColor Green
    Write-Host "ChromaDB: http://localhost:8000" -ForegroundColor Green
    Write-Host ""
    Write-Host "To view logs: docker-compose -f docker-compose.prod.yml logs -f" -ForegroundColor White
    Write-Host "To stop: docker-compose -f docker-compose.prod.yml down" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "===== Deployment Failed =====" -ForegroundColor Red
    Write-Host "Health checks failed. Check logs:" -ForegroundColor Red
    Write-Host "docker-compose -f docker-compose.prod.yml logs" -ForegroundColor Yellow
    exit 1
}
