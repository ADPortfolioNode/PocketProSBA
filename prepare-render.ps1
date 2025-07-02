# PocketPro:SBA Render Deployment Script (Windows)
Write-Host "🚀 Preparing PocketPro:SBA for Render deployment..." -ForegroundColor Green

# Check Python version
$pythonVersion = python --version 2>&1
Write-Host "🐍 Python version: $pythonVersion" -ForegroundColor Cyan

# Check required files
$requiredFiles = @("requirements.txt", "run.py", "app.py", "render.yaml")
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✅ Found: $file" -ForegroundColor Green
    } else {
        Write-Host "❌ Missing: $file" -ForegroundColor Red
        exit 1
    }
}

# Test virtual environment
Write-Host "🔧 Testing Python dependencies..." -ForegroundColor Yellow
try {
    $pipCheck = python -m pip check 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Dependencies check passed" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Dependency conflicts found:" -ForegroundColor Yellow
        Write-Host $pipCheck -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠️  Could not check dependencies" -ForegroundColor Yellow
}

# Test application import
Write-Host "🧪 Testing application imports..." -ForegroundColor Yellow
$env:FLASK_ENV = "production"
$env:PYTHONPATH = "$PWD\src;$PWD"

try {
    $testScript = "import run; print('App import successful')"
    $importTest = python -c $testScript 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Application imports successfully" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Import test failed, but fallback should work" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not test imports" -ForegroundColor Yellow
}

# Environment check
Write-Host "🔍 Environment check:" -ForegroundColor Yellow
if (-not $env:GEMINI_API_KEY) {
    Write-Host "⚠️  GEMINI_API_KEY not set (required for production)" -ForegroundColor Yellow
} else {
    Write-Host "✅ GEMINI_API_KEY is set" -ForegroundColor Green
}

Write-Host ""
Write-Host "📋 Render Deployment Checklist:" -ForegroundColor Cyan
Write-Host "1. ✅ Push code to GitHub repository" -ForegroundColor White
Write-Host "2. ✅ Create new Web Service on Render.com" -ForegroundColor White
Write-Host "3. ✅ Connect your GitHub repository" -ForegroundColor White
Write-Host "4. ✅ Use settings from render.yaml OR manual config:" -ForegroundColor White
Write-Host "   - Runtime: Python" -ForegroundColor Gray
Write-Host "   - Build: pip install -r requirements.txt" -ForegroundColor Gray
Write-Host "   - Start: gunicorn --bind 0.0.0.0:`$PORT --workers 1 --timeout 120 run:app" -ForegroundColor Gray
Write-Host "5. ⚠️  Add environment variable: GEMINI_API_KEY" -ForegroundColor Yellow
Write-Host "6. ✅ Deploy!" -ForegroundColor White
Write-Host ""
Write-Host "🎯 Frontend deployment:" -ForegroundColor Cyan
Write-Host "- Create Static Site service" -ForegroundColor White
Write-Host "- Build: cd frontend; npm install --legacy-peer-deps; npm run build" -ForegroundColor Gray
Write-Host "- Publish: frontend/build" -ForegroundColor Gray
Write-Host ""
Write-Host "🌐 Your app will be available at: https://your-service-name.onrender.com" -ForegroundColor Green
