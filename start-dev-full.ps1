Write-Host "Starting PocketPro:SBA Edition (Backend and Frontend)..." -ForegroundColor Cyan

# Start the backend in a new window
# Same entrypoint as production (wsgi:application); gunicorn has no Windows build.
Start-Process powershell -ArgumentList "-Command `$env:FLASK_ENV='development'; `$env:PORT='5000'; python wsgi.py" -WindowStyle Normal

# Wait a moment for the backend to initialize
Write-Host "Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start the frontend
Set-Location -Path "$PSScriptRoot\frontend"
Write-Host "Starting frontend..." -ForegroundColor Green
npm start
