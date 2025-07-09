# Test Render.com deployment configuration locally
# This script simulates how Render.com would run your application

Write-Host "🚀 Testing Render.com deployment configuration" -ForegroundColor Cyan

# Set the PORT environment variable to what Render.com would use
$env:PORT = "5000"
Write-Host "Setting PORT environment variable to $env:PORT" -ForegroundColor Yellow

# Check if gunicorn is installed
try {
    $gunicornVersion = python -m pip show gunicorn
    Write-Host "Gunicorn is installed:" -ForegroundColor Green
    Write-Host $gunicornVersion -ForegroundColor Gray
}
catch {
    Write-Host "❌ Gunicorn is not installed. Installing it now..." -ForegroundColor Red
    python -m pip install gunicorn
}

# Verify the Procfile configuration
$procfileContent = Get-Content -Path "./Procfile" -Raw
Write-Host "`nProcfile configuration:" -ForegroundColor Yellow
Write-Host $procfileContent -ForegroundColor Gray

# Check gunicorn_render_fixed.py
$gunicornConfigExists = Test-Path -Path "./gunicorn_render_fixed.py"
if ($gunicornConfigExists) {
    Write-Host "✅ gunicorn_render_fixed.py exists" -ForegroundColor Green
}
else {
    Write-Host "❌ gunicorn_render_fixed.py not found!" -ForegroundColor Red
    exit 1
}

# Run the port binding test
Write-Host "`nRunning port binding test..." -ForegroundColor Cyan
python test_render_port_binding.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Port binding test PASSED! Your application should work on Render.com" -ForegroundColor Green
}
else {
    Write-Host "`n❌ Port binding test FAILED! Please fix the issues before deploying to Render.com" -ForegroundColor Red
}

# Run the app with Render.com configuration for manual testing
Write-Host "`nStarting application with Render.com configuration for manual testing..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the application" -ForegroundColor Yellow
gunicorn app:app --config=gunicorn_render_fixed.py
