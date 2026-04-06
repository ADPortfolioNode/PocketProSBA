Write-Host "Checking if backend is running..." -ForegroundColor Cyan

try {
    $response = Invoke-WebRequest -Uri "http://localhost:10000/health" -UseBasicParsing -ErrorAction Stop
    Write-Host "Backend API is running at http://localhost:10000" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Backend API is NOT running or not accessible" -ForegroundColor Red
    Write-Host "The frontend will start but may not function correctly without the backend" -ForegroundColor Yellow
    Write-Host "Start the backend with 'docker-compose up' or 'deploy-docker.bat' in a separate terminal" -ForegroundColor Yellow
    Start-Sleep -Seconds 3
}

Write-Host "Starting PocketPro:SBA Edition Frontend..." -ForegroundColor Cyan
Set-Location -Path "$PSScriptRoot\frontend"
npm start
