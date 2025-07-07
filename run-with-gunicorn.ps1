# Run the Flask application with Gunicorn locally
# This simulates how Render.com will run the application

# Ensure Gunicorn is installed
if (-not (Get-Command gunicorn -ErrorAction SilentlyContinue)) {
    Write-Host "Gunicorn not found. Installing..." -ForegroundColor Yellow
    pip install gunicorn
}

# Set environment variables
$env:PORT = 5000
$env:FLASK_ENV = "production"
$env:FLASK_APP = "minimal_app.py"
$env:PYTHONUNBUFFERED = "1"

Write-Host "Starting Flask application with Gunicorn..." -ForegroundColor Cyan
Write-Host "This simulates how Render.com will run the application" -ForegroundColor Cyan
Write-Host "Binding to 0.0.0.0:$($env:PORT)" -ForegroundColor Cyan

# Start Gunicorn with the same configuration as Render.com
gunicorn --bind 0.0.0.0:$env:PORT --config=gunicorn.render.conf.py minimal_app:app
