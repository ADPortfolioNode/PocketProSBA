# Start Flask app and run verification in separate PowerShell windows
Write-Host "Starting Flask application in a new window..." -ForegroundColor Cyan

# Set environment variables
$env:PORT = 5000
$env:FLASK_ENV = "development"
$env:FLASK_APP = "minimal_app.py"
$env:PYTHONUNBUFFERED = "1"

# Start Flask in a new PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python run_windows.py"

# Wait for Flask to start
Write-Host "Waiting for Flask application to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Run verification in this window
Write-Host "Running verification script..." -ForegroundColor Cyan
python verify_render_port.py

Write-Host "Verification complete." -ForegroundColor Green
Write-Host "The Flask app is running in a separate window. Close that window when you're done." -ForegroundColor Yellow
