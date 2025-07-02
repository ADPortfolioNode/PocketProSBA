#
# API Endpoint Verification Script
# This script checks all critical API endpoints for proper functionality
#

$dockerPort = 10000
$localPort = 5000
$endpoints = @(
    "/api/info",
    "/api/greeting",
    "/api/models",
    "/api/documents",
    "/api/collections/stats",
    "/api/search/filters",
    "/api/assistants",
    "/health"
)

function Test-Endpoint {
    param (
        [string]$baseUrl,
        [string]$endpoint
    )
    
    $url = "${baseUrl}${endpoint}"
    Write-Host "Testing endpoint: $url" -ForegroundColor Cyan
    
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -ErrorAction Stop
        $statusCode = $response.StatusCode
        
        if ($statusCode -eq 200) {
            Write-Host "  ✓ Status: $statusCode OK" -ForegroundColor Green
            try {
                $content = $response.Content | ConvertFrom-Json
                Write-Host "  ✓ Valid JSON response" -ForegroundColor Green
            } catch {
                Write-Host "  ✗ Invalid JSON response" -ForegroundColor Red
            }
        } else {
            Write-Host "  ✗ Status: $statusCode" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ✗ Error: $_" -ForegroundColor Red
    }
}

# Check Docker endpoints
Write-Host "`nTesting Docker deployment endpoints (port $dockerPort):" -ForegroundColor Blue
foreach ($endpoint in $endpoints) {
    Test-Endpoint -baseUrl "http://localhost:$dockerPort" -endpoint $endpoint
}

# Check Local development endpoints
Write-Host "`nTesting Local development endpoints (port $localPort):" -ForegroundColor Blue
foreach ($endpoint in $endpoints) {
    Test-Endpoint -baseUrl "http://localhost:$localPort" -endpoint $endpoint
}

# Summary
Write-Host "`nVerification complete. If any endpoints failed, check:" -ForegroundColor Magenta
Write-Host "1. Is the backend server running?" -ForegroundColor Magenta
Write-Host "2. Is the Docker container running? (docker-compose ps)" -ForegroundColor Magenta
Write-Host "3. Check server logs for errors (docker-compose logs backend)" -ForegroundColor Magenta
Write-Host "4. Verify CORS configuration in your Flask app" -ForegroundColor Magenta
