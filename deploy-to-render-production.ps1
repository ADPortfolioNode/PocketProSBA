# Deploy to Render.com - Production
# This script verifies readiness and deploys to Render.com

# Verify production readiness
Write-Host "Verifying production readiness..." -ForegroundColor Cyan
python verify_production_readiness.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Production readiness verification failed. Aborting deployment." -ForegroundColor Red
    exit 1
}

# Ask for confirmation before deployment
$confirmation = Read-Host "Are you sure you want to deploy to production? (y/n)"
if ($confirmation -ne "y") {
    Write-Host "Deployment aborted." -ForegroundColor Yellow
    exit 0
}

# Check if render CLI is installed
$renderInstalled = $null
try {
    $renderInstalled = Get-Command render -ErrorAction SilentlyContinue
} catch {
    $renderInstalled = $null
}

if (-not $renderInstalled) {
    Write-Host "Render CLI not found. Would you like to install it? (y/n)" -ForegroundColor Yellow
    $installRender = Read-Host
    
    if ($installRender -eq "y") {
        Write-Host "Installing Render CLI..." -ForegroundColor Cyan
        # Instructions for installing Render CLI - may need adjustment
        Write-Host "Please visit https://render.com/docs/cli for installation instructions" -ForegroundColor Cyan
        Write-Host "After installing, please run this script again." -ForegroundColor Cyan
        exit 0
    } else {
        Write-Host "Render CLI is required for automated deployment. Please install it manually." -ForegroundColor Yellow
        Write-Host "You can still deploy through the Render dashboard." -ForegroundColor Yellow
        exit 0
    }
}

# Ask which deployment method to use
Write-Host "Select deployment method:" -ForegroundColor Cyan
Write-Host "1. Standard Python Web Service (render.production.yaml)" -ForegroundColor White
Write-Host "2. Docker-based Deployment (render.docker.yaml)" -ForegroundColor White
$deploymentMethod = Read-Host "Enter selection (1 or 2)"

# Deploy based on selection
if ($deploymentMethod -eq "1") {
    Write-Host "Deploying with render.production.yaml..." -ForegroundColor Cyan
    render blueprint render render.production.yaml
} elseif ($deploymentMethod -eq "2") {
    Write-Host "Deploying with render.docker.yaml..." -ForegroundColor Cyan
    render blueprint render render.docker.yaml
} else {
    Write-Host "Invalid selection. Aborting deployment." -ForegroundColor Red
    exit 1
}

# Check deployment status
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Deployment initiated successfully!" -ForegroundColor Green
    Write-Host "You can monitor the deployment status in the Render dashboard." -ForegroundColor Cyan
} else {
    Write-Host "❌ Deployment failed. Please check the output above for details." -ForegroundColor Red
}

# Final instructions
Write-Host "`nOnce deployed, verify the application at:" -ForegroundColor Cyan
Write-Host "https://pocketpro-sba-production.onrender.com/" -ForegroundColor White
Write-Host "`nCheck the health endpoint at:" -ForegroundColor Cyan
Write-Host "https://pocketpro-sba-production.onrender.com/health" -ForegroundColor White
