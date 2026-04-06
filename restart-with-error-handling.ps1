Write-Host "Restarting PocketPro SBA Application..." -ForegroundColor Green

# Stop running containers
Write-Host "Stopping containers..." -ForegroundColor Cyan
docker-compose down

# Check if previous command was successful
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ Warning: Issues stopping containers. Proceeding anyway..." -ForegroundColor Yellow
}

# Build containers with no cache to ensure latest changes
Write-Host "Rebuilding containers..." -ForegroundColor Cyan
docker-compose build --no-cache

# Check if previous command was successful
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Build failed. See above for details." -ForegroundColor Red
    exit $LASTEXITCODE
}

# Start containers
Write-Host "Starting containers..." -ForegroundColor Cyan
docker-compose up -d

# Check if previous command was successful
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Failed to start containers. See above for details." -ForegroundColor Red
    exit $LASTEXITCODE
}

# Wait for services to start
Write-Host "Waiting for services to initialize..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# Check if backend is running
Write-Host "Checking backend status..." -ForegroundColor Cyan
try {
    $healthCheck = Invoke-RestMethod -Uri "http://localhost:5000/api/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
    Write-Host "✅ Backend is running and responsive!" -ForegroundColor Green
} catch {
    try {
        $infoCheck = Invoke-RestMethod -Uri "http://localhost:5000/api/info" -TimeoutSec 5 -ErrorAction SilentlyContinue
        Write-Host "✅ Backend is running and responsive (via info endpoint)!" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Warning: Backend may not be fully initialized. Check logs with 'docker-compose logs backend'" -ForegroundColor Yellow
    }
}

# Check if frontend is running
Write-Host "Checking frontend status..." -ForegroundColor Cyan
try {
    $frontendCheck = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -ErrorAction SilentlyContinue
    Write-Host "✅ Frontend is running and responsive!" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Warning: Frontend may not be fully initialized. Check logs with 'docker-compose logs frontend'" -ForegroundColor Yellow
}

Write-Host "`nApplication restarted! The modernized UI with error handling is now available." -ForegroundColor Green
Write-Host "Access the application at http://localhost:3000" -ForegroundColor Cyan
Write-Host "`nIf you experience any issues, run './check-docker-config.ps1' to diagnose problems." -ForegroundColor Yellow
