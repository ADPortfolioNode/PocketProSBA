# PowerShell script for testing PocketPro:SBA Render.com deployment
# This script verifies the Docker build and basic functionality
# Run from the project root directory

Write-Host "==== PocketPro:SBA Render.com Deployment Test ====" -ForegroundColor Cyan
Write-Host "Testing Dockerfile.render build and functionality"
Write-Host ""

# Check if Docker is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "🔍 Step 1: Building Docker image using Dockerfile.render..." -ForegroundColor Yellow
docker build -t pocketpro-sba-render -f Dockerfile.render .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker build successful!" -ForegroundColor Green

Write-Host ""
Write-Host "🔍 Step 2: Starting container for testing..." -ForegroundColor Yellow
$CONTAINER_ID = docker run -d -p 10000:10000 -e PORT=10000 -e FLASK_ENV=production -e GEMINI_API_KEY=dummy-key pocketpro-sba-render

if (-not $CONTAINER_ID) {
    Write-Host "❌ Failed to start Docker container!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Container started with ID: $CONTAINER_ID" -ForegroundColor Green
Write-Host "⏳ Waiting 10 seconds for application to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "🔍 Step 3: Testing health endpoint..." -ForegroundColor Yellow
try {
    $HEALTH_RESPONSE = Invoke-WebRequest -Uri "http://localhost:10000/health" -UseBasicParsing
    $STATUS_CODE = $HEALTH_RESPONSE.StatusCode
} catch {
    $STATUS_CODE = $_.Exception.Response.StatusCode.value__
}

if ($STATUS_CODE -ne 200) {
    Write-Host "❌ Health check failed with status: $STATUS_CODE" -ForegroundColor Red
    docker logs $CONTAINER_ID
    docker stop $CONTAINER_ID
    exit 1
}

Write-Host "✅ Health check endpoint responded with status 200!" -ForegroundColor Green

Write-Host ""
Write-Host "🔍 Step 4: Checking API info endpoint..." -ForegroundColor Yellow
try {
    $API_RESPONSE = Invoke-WebRequest -Uri "http://localhost:10000/api/info" -UseBasicParsing
    Write-Host "API info response: $($API_RESPONSE.Content)" -ForegroundColor Cyan
} catch {
    Write-Host "⚠️ API info endpoint not available: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔍 Step 5: Checking logs for any errors..." -ForegroundColor Yellow
docker logs $CONTAINER_ID | Select-String -Pattern "error" -CaseSensitive:$false

Write-Host ""
Write-Host "🔍 Step 6: Cleanup..." -ForegroundColor Yellow
docker stop $CONTAINER_ID
docker rm $CONTAINER_ID

Write-Host ""
Write-Host "==== Test Summary ====" -ForegroundColor Cyan
Write-Host "✅ Docker build: Successful" -ForegroundColor Green
Write-Host "✅ Application startup: Successful" -ForegroundColor Green
Write-Host "✅ Health check: Successful" -ForegroundColor Green
Write-Host "✅ API check: Completed" -ForegroundColor Green
Write-Host ""
Write-Host "The Dockerfile.render appears to be ready for Render.com deployment!" -ForegroundColor Green
Write-Host "Next steps: Deploy to Render.com using the provided render.yaml configuration."
