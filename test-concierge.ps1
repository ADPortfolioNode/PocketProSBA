# PocketProSBA Test and Restart Script
Write-Host "===== PocketProSBA Test and Restart Script =====" -ForegroundColor Cyan
Write-Host ""

function Test-Backend {
    Write-Host "Testing backend connectivity..." -ForegroundColor Yellow
    
    $endpoints = @(
        "http://localhost:8080/health",
        "http://localhost:8080/api/health",
        "http://localhost:5000/health",
        "http://localhost:5000/api/health"
    )
    
    $anySuccess = $false
    
    foreach ($endpoint in $endpoints) {
        try {
            $response = Invoke-WebRequest -Uri $endpoint -Method GET -TimeoutSec 3 -ErrorAction Stop
            Write-Host "[✓] Successfully connected to $endpoint" -ForegroundColor Green
            Write-Host "    Status: $($response.StatusCode)" -ForegroundColor Green
            $anySuccess = $true
        } catch {
            Write-Host "[✗] Failed to connect to $endpoint" -ForegroundColor Red
            Write-Host "    Error: $_" -ForegroundColor Red
        }
    }
    
    return $anySuccess
}

function Start-Docker {
    Write-Host "`nStarting Docker containers..." -ForegroundColor Yellow
    
    try {
        docker-compose down
        Write-Host "[✓] Successfully stopped any existing containers" -ForegroundColor Green
    } catch {
        Write-Host "[!] Warning when stopping containers: $_" -ForegroundColor Yellow
    }
    
    try {
        docker-compose up -d
        Write-Host "[✓] Successfully started Docker containers" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "[✗] Failed to start Docker containers" -ForegroundColor Red
        Write-Host "    Error: $_" -ForegroundColor Red
        return $false
    }
}

function Test-Concierge {
    Write-Host "`nTesting concierge functionality..." -ForegroundColor Yellow
    
    try {
        python verify_concierge.py
        Write-Host "[✓] Concierge verification script completed" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "[✗] Failed to run concierge verification script" -ForegroundColor Red
        Write-Host "    Error: $_" -ForegroundColor Red
        return $false
    }
}

# Main script flow
$backendRunning = Test-Backend

if (-not $backendRunning) {
    Write-Host "`nBackend is not running. Would you like to start the Docker containers? (Y/n)" -ForegroundColor Yellow
    $response = Read-Host
    
    if ($response -eq "" -or $response -eq "y" -or $response -eq "Y") {
        $dockerStarted = Start-Docker
        
        if ($dockerStarted) {
            # Wait for containers to initialize
            Write-Host "`nWaiting 10 seconds for containers to initialize..." -ForegroundColor Yellow
            Start-Sleep -Seconds 10
            
            # Test again
            $backendRunning = Test-Backend
        }
    }
}

if ($backendRunning) {
    Write-Host "`nBackend is running. Would you like to test the concierge functionality? (Y/n)" -ForegroundColor Yellow
    $response = Read-Host
    
    if ($response -eq "" -or $response -eq "y" -or $response -eq "Y") {
        Test-Concierge
    }
} else {
    Write-Host "`nBackend is still not running. Please check Docker logs for more information:" -ForegroundColor Red
    Write-Host "docker-compose logs" -ForegroundColor Yellow
}

Write-Host "`n===== Script Complete =====" -ForegroundColor Cyan
