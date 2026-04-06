Write-Host "Checking Frontend Components..." -ForegroundColor Green

# Change to frontend directory
cd frontend

# Check react-bootstrap installation
Write-Host "Verifying react-bootstrap package..." -ForegroundColor Cyan
$reactBootstrap = npm list react-bootstrap
if ($reactBootstrap -match "react-bootstrap@") {
    Write-Host "✅ react-bootstrap is installed" -ForegroundColor Green
} else {
    Write-Host "⚠️ react-bootstrap not found, installing..." -ForegroundColor Yellow
    npm install --save react-bootstrap
}

# Check bootstrap css
Write-Host "Verifying bootstrap CSS imports..." -ForegroundColor Cyan
$appJsContent = Get-Content src\App.js -Raw
if ($appJsContent -match "bootstrap/dist/css/bootstrap.min.css") {
    Write-Host "✅ Bootstrap CSS is imported" -ForegroundColor Green
} else {
    Write-Host "⚠️ Bootstrap CSS import not found in App.js" -ForegroundColor Red
}

# Build the frontend
Write-Host "Building the frontend..." -ForegroundColor Cyan
npm run build

Write-Host "Frontend modernization verification complete!" -ForegroundColor Green
Write-Host "You can now run the application using 'npm start' in the frontend directory." -ForegroundColor Green
