# Verify Render.com port binding
Write-Host "Running Render.com port verification..." -ForegroundColor Cyan

# Set the PORT environment variable if not already set
if (-not $env:PORT) {
    $env:PORT = 5000
    Write-Host "Setting PORT environment variable to 5000" -ForegroundColor Yellow
}

# Run the verification script
Write-Host "Running verification script..." -ForegroundColor Cyan
python verify_render_port.py

Write-Host "`nVerification complete." -ForegroundColor Green
Read-Host "Press Enter to continue..."
