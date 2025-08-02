# PowerShell script for single point full production testing of Render.com deployment

# Set base URL of the deployed backend service
$BASE_URL = "http://your-production-backend-url"  # Replace with actual URL

Write-Host "Starting full production deployment tests..."

# 1. Health check endpoint
Write-Host "Testing health endpoint..."
try {
    Invoke-RestMethod -Uri "$BASE_URL/health" -Method Get -ErrorAction Stop
    Write-Host "Health check passed."
} catch {
    Write-Error "Health check failed!"
    exit 1
}

# 2. Redis connectivity test (assuming an endpoint exists to verify Redis)
Write-Host "Testing Redis connectivity..."
try {
    Invoke-RestMethod -Uri "$BASE_URL/redis-test" -Method Get -ErrorAction Stop
    Write-Host "Redis connectivity test passed."
} catch {
    Write-Error "Redis connectivity test failed!"
    exit 1
}

# 3. ChromaDB connectivity test (assuming an endpoint exists to verify ChromaDB)
Write-Host "Testing ChromaDB connectivity..."
try {
    Invoke-RestMethod -Uri "$BASE_URL/chromadb-test" -Method Get -ErrorAction Stop
    Write-Host "ChromaDB connectivity test passed."
} catch {
    Write-Error "ChromaDB connectivity test failed!"
    exit 1
}

# 4. Environment variable validation (assuming an endpoint to dump env vars securely)
Write-Host "Validating environment variables..."
try {
    Invoke-RestMethod -Uri "$BASE_URL/env-check" -Method Get -ErrorAction Stop
    Write-Host "Environment variable validation passed."
} catch {
    Write-Error "Environment variable validation failed!"
    exit 1
}

Write-Host "All production deployment tests passed successfully."
