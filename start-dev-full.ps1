Write-Host "Starting PocketPro:SBA Edition (Backend and Frontend)..." -ForegroundColor Cyan

# Start the backend in a new window
Start-Process powershell -ArgumentList "-Command python run.py" -WindowStyle Normal

# Wait a moment for the backend to initialize
Write-Host "Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start the frontend
Set-Location -Path "$PSScriptRoot\frontend"
Write-Host "Starting frontend..." -ForegroundColor Green
npm start
