# Deployment verification script for PocketPro:SBA
# Checks if all components are running correctly after deployment

param (
    [string]$domain = "localhost",
    [string]$protocol = "http"
)

$ErrorActionPreference = "Continue"
$baseUrl = if ($domain -eq "localhost") { 
    "http://localhost:10000" 
} else { 
    "${protocol}://${domain}" 
}

Write-Host "===== PocketPro:SBA Deployment Verification =====" -ForegroundColor Cyan
Write-Host "Target: $baseUrl" -ForegroundColor Yellow
Write-Host ""

# Verify Docker containers are running
Write-Host "Checking Docker containers..." -ForegroundColor Yellow
try {
    $containers = docker-compose ps --format json | ConvertFrom-Json
    
    foreach ($container in $containers) {
        $name = $container.Name
        $state = $container.State
        
        if ($state -eq "running") {
            Write-Host "[√] Container $name is running" -ForegroundColor Green
        } else {
            Write-Host "[X] Container $name is not running (State: $state)" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "[X] Error checking Docker containers: $_" -ForegroundColor Red
}

# Check health endpoint
Write-Host "`nChecking application health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/health" -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "[√] Health check passed (Status: $($response.StatusCode))" -ForegroundColor Green
    } else {
        Write-Host "[!] Health check returned unexpected status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[X] Health check failed: $_" -ForegroundColor Red
}

# Check API endpoints
Write-Host "`nChecking API endpoints..." -ForegroundColor Yellow

$endpoints = @(
    "/api/greeting",
    "/api/info"
)

foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl$endpoint" -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "[√] Endpoint $endpoint is accessible (Status: $($response.StatusCode))" -ForegroundColor Green
        } else {
            Write-Host "[!] Endpoint $endpoint returned unexpected status: $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[X] Endpoint $endpoint is not accessible: $_" -ForegroundColor Red
    }
}

# Check frontend static assets
Write-Host "`nChecking frontend static assets..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl" -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "[√] Frontend is accessible (Status: $($response.StatusCode))" -ForegroundColor Green
        
        # Check if it's actually our app by looking for characteristic strings in the HTML
        if ($response.Content -match "PocketPro:SBA" -or $response.Content -match "React") {
            Write-Host "[√] Frontend content verified" -ForegroundColor Green
        } else {
            Write-Host "[!] Frontend content may not be correct" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[!] Frontend returned unexpected status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[X] Frontend is not accessible: $_" -ForegroundColor Red
}

# SSL check if applicable
if ($protocol -eq "https") {
    Write-Host "`nChecking SSL certificate..." -ForegroundColor Yellow
    try {
        $cert = Invoke-Command -ScriptBlock {
            [Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
            $req = [Net.HttpWebRequest]::Create("https://$domain")
            $req.GetResponse() | Out-Null
            $cert = $req.ServicePoint.Certificate
            [Net.ServicePointManager]::ServerCertificateValidationCallback = $null
            return $cert
        }
        
        $certExpiration = [DateTime]::Parse($cert.GetExpirationDateString())
        $daysRemaining = ($certExpiration - (Get-Date)).Days
        
        if ($daysRemaining -gt 30) {
            Write-Host "[√] SSL certificate is valid (Expires in $daysRemaining days)" -ForegroundColor Green
        } elseif ($daysRemaining -gt 0) {
            Write-Host "[!] SSL certificate will expire soon in $daysRemaining days" -ForegroundColor Yellow
        } else {
            Write-Host "[X] SSL certificate has expired" -ForegroundColor Red
        }
    } catch {
        Write-Host "[X] Error checking SSL certificate: $_" -ForegroundColor Red
    }
}

Write-Host "`n===== Verification Summary =====" -ForegroundColor Cyan
Write-Host "1. Check all containers are running" -ForegroundColor White
Write-Host "2. Verify application health endpoint is accessible" -ForegroundColor White
Write-Host "3. Verify API endpoints are functioning" -ForegroundColor White
Write-Host "4. Verify frontend static assets are accessible" -ForegroundColor White
if ($protocol -eq "https") {
    Write-Host "5. Verify SSL certificate is valid" -ForegroundColor White
}

Write-Host "`nRecommended Next Steps:" -ForegroundColor Yellow
Write-Host "1. Test document upload functionality" -ForegroundColor White
Write-Host "2. Test RAG query functionality" -ForegroundColor White
Write-Host "3. Monitor application logs:" -ForegroundColor White
Write-Host "   docker-compose logs -f" -ForegroundColor Green
Write-Host "`nVerification complete!" -ForegroundColor Cyan
