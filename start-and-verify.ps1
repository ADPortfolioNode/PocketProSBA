# Start Flask application and run verification
Write-Host "Starting Flask application..." -ForegroundColor Cyan

# Set environment variables
$env:PORT = 5000
$env:FLASK_ENV = "development"
$env:FLASK_APP = "minimal_app.py"

# Start Flask in background
$flaskProcess = Start-Process -FilePath "python" -ArgumentList "minimal_app.py" -PassThru -WindowStyle Normal

# Wait for Flask to start
Write-Host "Waiting for Flask application to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Run verification
Write-Host "Running verification script..." -ForegroundColor Cyan
python verify_render_port.py

# Check if we want to stop the Flask app
$stopApp = Read-Host "Do you want to stop the Flask application? (y/n)"
if ($stopApp -eq "y" -or $stopApp -eq "Y") {
    Write-Host "Stopping Flask application..." -ForegroundColor Yellow
    Stop-Process -Id $flaskProcess.Id -Force
    Write-Host "Flask application stopped." -ForegroundColor Green
} else {
    Write-Host "Flask application is still running. Process ID: $($flaskProcess.Id)" -ForegroundColor Yellow
    Write-Host "You can stop it manually using: Stop-Process -Id $($flaskProcess.Id) -Force" -ForegroundColor Yellow
}

Write-Host "Verification complete." -ForegroundColor Green
