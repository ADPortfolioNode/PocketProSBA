Write-Host "PocketPro SBA Docker Configuration Check" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Check Docker installation
Write-Host "Checking Docker installation..." -ForegroundColor Cyan
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker installed: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed or not in PATH" -ForegroundColor Red
    exit
}

# Check Docker Compose installation
Write-Host "`nChecking Docker Compose installation..." -ForegroundColor Cyan
try {
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose installed: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose is not installed or not in PATH" -ForegroundColor Red
}

# Check running containers
Write-Host "`nChecking running containers..." -ForegroundColor Cyan
$containers = docker ps --filter "name=pocketprosba" --format "{{.Names}} ({{.Status}})"

if ($containers) {
    Write-Host "✅ Running containers:" -ForegroundColor Green
    $containers | ForEach-Object { Write-Host "   - $_" -ForegroundColor Green }
} else {
    Write-Host "❌ No PocketPro SBA containers are running" -ForegroundColor Red
}

# Check Docker Compose file
Write-Host "`nChecking Docker Compose configuration..." -ForegroundColor Cyan
if (Test-Path "docker-compose.yml") {
    Write-Host "✅ docker-compose.yml exists" -ForegroundColor Green
    
    # Check app ports in docker-compose.yml
    $composeContent = Get-Content "docker-compose.yml" -Raw
    
    if ($composeContent -match "backend.*?ports:.*?(\d+):5000") {
        $backendPort = $matches[1]
        Write-Host "   - Backend exposed on port $backendPort" -ForegroundColor Green
    } else {
        Write-Host "   - ⚠️ Backend port mapping not found" -ForegroundColor Yellow
    }
    
    if ($composeContent -match "frontend.*?ports:.*?(\d+):3000") {
        $frontendPort = $matches[1]
        Write-Host "   - Frontend exposed on port $frontendPort" -ForegroundColor Green
    } else {
        Write-Host "   - ⚠️ Frontend port mapping not found" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ docker-compose.yml not found" -ForegroundColor Red
}

# Check network connectivity between containers
Write-Host "`nChecking network connectivity..." -ForegroundColor Cyan
$networks = docker network ls --filter "name=pocketprosba" --format "{{.Name}}"

if ($networks) {
    Write-Host "✅ Docker networks:" -ForegroundColor Green
    $networks | ForEach-Object { Write-Host "   - $_" -ForegroundColor Green }
    
    # Check containers on the networks
    foreach ($network in $networks) {
        $networkInfo = docker network inspect $network --format "{{range .Containers}}{{.Name}} {{end}}"
        Write-Host "   - Containers on $network`: $networkInfo" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️ No PocketPro SBA networks found" -ForegroundColor Yellow
}

# Test connectivity to backend API
Write-Host "`nTesting backend API connectivity..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5000/api/health" -TimeoutSec 5
    Write-Host "✅ Backend API is responsive" -ForegroundColor Green
    Write-Host "   - Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Green
} catch {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:5000/api/info" -TimeoutSec 5
        Write-Host "✅ Backend API is responsive (using /api/info endpoint)" -ForegroundColor Green
        Write-Host "   - Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Green
    } catch {
        Write-Host "❌ Cannot connect to backend API at http://localhost:5000" -ForegroundColor Red
        Write-Host "   - Error: $_" -ForegroundColor Red
    }
}

# Provide troubleshooting steps
Write-Host "`nTroubleshooting Recommendations:" -ForegroundColor Cyan
Write-Host "1. If containers aren't running, try: docker-compose up -d" -ForegroundColor White
Write-Host "2. If backend isn't responsive, check logs: docker-compose logs backend" -ForegroundColor White
Write-Host "3. If frontend can't connect to backend, check network configuration" -ForegroundColor White
Write-Host "4. Try restarting containers: docker-compose restart" -ForegroundColor White
Write-Host "5. Rebuild with: docker-compose down && docker-compose build --no-cache && docker-compose up -d" -ForegroundColor White

Write-Host "`nConfiguration check complete!" -ForegroundColor Green
