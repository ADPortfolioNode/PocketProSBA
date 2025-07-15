# PocketPro:SBA Final Production Test Menu
# Interactive menu for build, run, test, and readiness checks

function Show-Menu {
    Clear-Host
    Write-Host "================ PocketPro:SBA Final Production Test Menu ================" -ForegroundColor Cyan
    Write-Host "1. Build Frontend Docker Image"
    Write-Host "2. Build Backend Docker Image"
    Write-Host "3. Run Frontend Container"
    Write-Host "4. Run Backend Container"
    Write-Host "5. Run Frontend Health & Regression Tests"
    Write-Host "6. Run Backend Health & Regression Tests"
    Write-Host "7. Check Production Readiness (Config, Endpoints, Logs)"
    Write-Host "8. Show System-Generated Config Answers"
    Write-Host "9. Exit"
    Write-Host "==========================================================================="
}

function Build-Frontend {
    Write-Host "Building Frontend Docker Image..." -ForegroundColor Yellow
    docker build -f Dockerfile.frontend.prod -t pocketpro-frontend-prod .
}

function Build-Backend {
    Write-Host "Building Backend Docker Image..." -ForegroundColor Yellow
    docker build -f Dockerfile.backend.prod -t pocketpro-backend-prod .
}

function Run-Frontend {
    Write-Host "Running Frontend Container..." -ForegroundColor Yellow
    docker run -d --name pocketpro-frontend-prod-test -p 8080:80 pocketpro-frontend-prod
}

function Run-Backend {
    Write-Host "Running Backend Container..." -ForegroundColor Yellow
    docker run -d --name pocketpro-backend-prod-test -p 10000:10000 pocketpro-backend-prod
}

function Test-Frontend {
    Write-Host "Running Frontend Health & Regression Tests..." -ForegroundColor Yellow
    if (Test-Path "test-frontend-production.ps1") {
        .\test-frontend-production.ps1
    } else {
        Write-Host "test-frontend-production.ps1 not found!" -ForegroundColor Red
    }
}

function Test-Backend {
    Write-Host "Running Backend Health & Regression Tests..." -ForegroundColor Yellow
    if (Test-Path "test-backend-production.ps1") {
        .\test-backend-production.ps1
    } else {
        Write-Host "test-backend-production.ps1 not found!" -ForegroundColor Red
    }
}

function Check-Readiness {
    Write-Host "Checking Production Readiness..." -ForegroundColor Yellow
    if (Test-Path "verify_production_readiness.py") {
        python verify_production_readiness.py
    } else {
        Write-Host "verify_production_readiness.py not found!" -ForegroundColor Red
    }
    Write-Host "Checking Docker Compose status..." -ForegroundColor Yellow
    docker-compose ps
    Write-Host "Checking logs for errors..." -ForegroundColor Yellow
    docker-compose logs --tail=50
}

function Show-Config {
    Write-Host "System-Generated Config Answers:" -ForegroundColor Cyan
    Write-Host "Frontend Dockerfile: Dockerfile.frontend.prod"
    Write-Host "Backend Dockerfile: Dockerfile.backend.prod"
    Write-Host "Frontend Health Endpoint: http://localhost:8080/"
    Write-Host "Backend Health Endpoint: http://localhost:10000/health"
    Write-Host "Required ENV: GEMINI_API_KEY, FLASK_ENV, PORT, CHROMADB_URL"
    Write-Host "Nginx config: nginx.prod.conf routes /api/ to backend, /health to backend"
    Write-Host "Docker Compose: Maps ports, sets dependencies, healthchecks"
    Write-Host "Refer to INSTRUCTIONS.md for regression checklist and deployment steps"
}

while ($true) {
    Show-Menu
    $choice = Read-Host "Select an option (1-9)"
    switch ($choice) {
        "1" { Build-Frontend }
        "2" { Build-Backend }
        "3" { Run-Frontend }
        "4" { Run-Backend }
        "5" { Test-Frontend }
        "6" { Test-Backend }
        "7" { Check-Readiness }
        "8" { Show-Config }
        "9" { break }
        default { Write-Host "Invalid selection. Please choose 1-9." -ForegroundColor Red }
    }
    Write-Host "Press Enter to continue..."
    [void][System.Console]::ReadLine()
}
