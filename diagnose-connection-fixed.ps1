Write-Host "PocketPro:SBA Edition Connection Diagnostics" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Function to test an endpoint
function Test-Endpoint {
    param (
        [string]$Uri,
        [string]$Description
    )
    Write-Host "Testing $Description at $Uri..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri $Uri -Method GET -TimeoutSec 5 -ErrorAction Stop
        Write-Host "✓ Successfully connected to $Uri" -ForegroundColor Green
        Write-Host "  Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "  Content Type: $($response.Headers['Content-Type'])" -ForegroundColor Green
        
        # Try to parse as JSON if it appears to be JSON
        if ($response.Headers['Content-Type'] -like "*application/json*") {
            try {
                $content = $response.Content | ConvertFrom-Json
                Write-Host "  Response preview: " -ForegroundColor Green -NoNewline
                Write-Host ($content | ConvertTo-Json -Depth 1 -Compress) -ForegroundColor White
            } catch {
                Write-Host "  (Content appears to be JSON but could not be parsed)" -ForegroundColor Yellow
            }
        } else {
            # Just show the first bit of content
            $preview = if ($response.Content.Length -gt 100) { $response.Content.Substring(0, 100) + "..." } else { $response.Content }
            Write-Host "  Response preview: $preview" -ForegroundColor White
        }
    } catch {
        Write-Host "✗ Failed to connect to $Uri" -ForegroundColor Red
        Write-Host "  Error: $_" -ForegroundColor Red
        
        # Try to provide more context for common errors
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode -eq 502) {
            Write-Host "  This is a 502 Bad Gateway error, likely indicating a proxy configuration issue" -ForegroundColor Yellow
        } elseif ($_.Exception.Response -and $_.Exception.Response.StatusCode -eq 404) {
            Write-Host "  This is a 404 Not Found error, the endpoint may not exist or be incorrectly routed" -ForegroundColor Yellow
        }
    }
    Write-Host ""
}

# Check local backend
Write-Host "Checking Local Backend API (Port 5000)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing -ErrorAction Stop
    Write-Host "✓ Local Backend API is running at http://localhost:5000" -ForegroundColor Green
    Write-Host "  Status: $($response.StatusCode)" -ForegroundColor Green
    
    try {
        $content = $response.Content | ConvertFrom-Json
        Write-Host "  Services:" -ForegroundColor Green
        foreach ($service in $content.services.PSObject.Properties) {
            Write-Host "    - $($service.Name): $($service.Value)" -ForegroundColor Green
        }
    } catch {
        Write-Host "  Could not parse JSON response" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Local Backend API is NOT running on port 5000" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
}

Write-Host ""

# Check Docker backend
Write-Host "Checking Docker Backend API (Port 10000)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:10000/health" -UseBasicParsing -ErrorAction Stop
    Write-Host "✓ Docker Backend API is running at http://localhost:10000" -ForegroundColor Green
    Write-Host "  Status: $($response.StatusCode)" -ForegroundColor Green
    
    try {
        $content = $response.Content | ConvertFrom-Json
        Write-Host "  Services:" -ForegroundColor Green
        foreach ($service in $content.services.PSObject.Properties) {
            Write-Host "    - $($service.Name): $($service.Value)" -ForegroundColor Green
        }
    } catch {
        Write-Host "  Could not parse JSON response" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Docker Backend API is NOT running or not accessible on port 10000" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    
    # Test alternate endpoint paths that might work with NGINX
    Write-Host "Attempting alternate endpoint paths with NGINX..." -ForegroundColor Yellow
    Test-Endpoint -Uri "http://localhost:10000/api/health" -Description "API health endpoint (alternate path)"
}

Write-Host ""

# Check additional API endpoints for Docker setup
Write-Host "Testing Additional API Endpoints (Docker setup)..." -ForegroundColor Yellow
Test-Endpoint -Uri "http://localhost:10000/api/info" -Description "API info endpoint"
Test-Endpoint -Uri "http://localhost:10000/api/models" -Description "API models endpoint"

Write-Host ""

# Check frontend configuration
Write-Host "Checking Frontend Configuration..." -ForegroundColor Yellow
$envPath = "$PSScriptRoot\frontend\.env"
$envDevPath = "$PSScriptRoot\frontend\.env.development"
$packageJsonPath = "$PSScriptRoot\frontend\package.json"

if (Test-Path $envPath) {
    Write-Host "✓ .env file exists" -ForegroundColor Green
    $envContent = Get-Content $envPath
    $backendUrl = $envContent | Where-Object { $_ -match "REACT_APP_BACKEND_URL" }
    
    if ($backendUrl) {
        Write-Host "  Backend URL configured: $backendUrl" -ForegroundColor Green
        
        # Check if the configured URL is actually responding
        $configuredUrl = ($backendUrl -split "=")[1].Trim()
        try {
            $null = Invoke-WebRequest -Uri "$configuredUrl/api/info" -UseBasicParsing -ErrorAction Stop -TimeoutSec 2
            Write-Host "  ✓ Configured backend URL is responding" -ForegroundColor Green
        } catch {
            Write-Host "  ✗ Configured backend URL is NOT responding" -ForegroundColor Red
        }
    } else {
        Write-Host "✗ Backend URL not found in .env file" -ForegroundColor Red
        Write-Host "  Add REACT_APP_BACKEND_URL=http://localhost:10000 to your .env file" -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ .env file not found" -ForegroundColor Red
    Write-Host "  Create a .env file in the frontend directory with REACT_APP_BACKEND_URL=http://localhost:10000" -ForegroundColor Yellow
}

if (Test-Path $envDevPath) {
    Write-Host "✓ .env.development file exists" -ForegroundColor Green
    $envDevContent = Get-Content $envDevPath
    $backendDevUrl = $envDevContent | Where-Object { $_ -match "REACT_APP_BACKEND_URL" }
    
    if ($backendDevUrl) {
        Write-Host "  Development Backend URL configured: $backendDevUrl" -ForegroundColor Green
    } else {
        Write-Host "✗ Backend URL not found in .env.development file" -ForegroundColor Red
        Write-Host "  Add REACT_APP_BACKEND_URL=http://localhost:5000 to your .env.development file" -ForegroundColor Yellow
    }
}

if (Test-Path $packageJsonPath) {
    Write-Host "✓ package.json exists" -ForegroundColor Green
    $packageJson = Get-Content $packageJsonPath -Raw | ConvertFrom-Json
    
    if ($packageJson.proxy) {
        Write-Host "  Proxy configured: $($packageJson.proxy)" -ForegroundColor Green
    } else {
        Write-Host "✗ Proxy not configured in package.json" -ForegroundColor Red
        Write-Host '  Add "proxy": "http://localhost:5000" to your package.json for local development' -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ package.json not found" -ForegroundColor Red
}

Write-Host ""

# Check Docker status
Write-Host "Checking Docker Status..." -ForegroundColor Yellow
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker is running" -ForegroundColor Green
        
        # Check if the containers are running
        $containers = docker ps --filter "name=pocketprosba" 2>&1
        if ($LASTEXITCODE -eq 0) {
            if ($containers -match "backend") {
                Write-Host "✓ Backend container is running" -ForegroundColor Green
            } else {
                Write-Host "✗ Backend container is NOT running" -ForegroundColor Red
                Write-Host "  Start with: docker-compose up -d" -ForegroundColor Yellow
            }
            
            if ($containers -match "frontend") {
                Write-Host "✓ Frontend container is running" -ForegroundColor Green
            } else {
                Write-Host "✗ Frontend container is NOT running" -ForegroundColor Red
                Write-Host "  Start with: docker-compose up -d" -ForegroundColor Yellow
            }
            
            if ($containers -match "chromadb") {
                Write-Host "✓ ChromaDB container is running" -ForegroundColor Green
            } else {
                Write-Host "✗ ChromaDB container is NOT running" -ForegroundColor Red
                Write-Host "  Start with: docker-compose up -d" -ForegroundColor Yellow
            }
        } else {
            Write-Host "✗ Error checking container status" -ForegroundColor Red
            Write-Host "  $containers" -ForegroundColor Red
        }
    } else {
        Write-Host "✗ Docker is NOT running" -ForegroundColor Red
        Write-Host "  Start Docker Desktop or Docker service before continuing" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Docker is NOT installed or not in PATH" -ForegroundColor Red
    Write-Host "  Install Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
}

Write-Host ""

# Check network connectivity
Write-Host "Checking Network Connectivity..." -ForegroundColor Yellow
try {
    $netstat5000 = netstat -an | findstr ":5000"
    if ($netstat5000) {
        Write-Host "✓ Port 5000 is in use (likely by the local backend)" -ForegroundColor Green
        Write-Host "  $netstat5000" -ForegroundColor Gray
    } else {
        Write-Host "✗ Port 5000 is not in use - local backend may not be running" -ForegroundColor Yellow
    }
    
    $netstat10000 = netstat -an | findstr ":10000"
    if ($netstat10000) {
        Write-Host "✓ Port 10000 is in use (likely by the Docker frontend/NGINX)" -ForegroundColor Green
        Write-Host "  $netstat10000" -ForegroundColor Gray
    } else {
        Write-Host "✗ Port 10000 is not in use - Docker setup may not be running" -ForegroundColor Yellow
    }
    
    $netstat8000 = netstat -an | findstr ":8000"
    if ($netstat8000) {
        Write-Host "✓ Port 8000 is in use (likely by ChromaDB)" -ForegroundColor Green
    }
} catch {
    Write-Host "  Could not check network ports" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "===== Recommended Fixes =====" -ForegroundColor Cyan
Write-Host "1. Update the nginx.conf to properly proxy the /health endpoint:" -ForegroundColor White
Write-Host @"
    location /health {
        proxy_pass http://backend:5000/health;
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
        proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto `$scheme;
    }
"@ -ForegroundColor Yellow
Write-Host ""

Write-Host "2. OR Update your App.js to use the API prefix for health checks:" -ForegroundColor White
Write-Host @"
    // Instead of:
    const healthCheck = await fetch(`${backendUrl}/health`);
    
    // Use:
    const healthCheck = await fetch(`${backendUrl}/api/health`);
"@ -ForegroundColor Yellow
Write-Host "   And add a corresponding route in your Flask app.py" -ForegroundColor White
Write-Host ""

Write-Host "3. Restart your Docker containers with:" -ForegroundColor White
Write-Host "   docker-compose down" -ForegroundColor Yellow
Write-Host "   docker-compose up -d" -ForegroundColor Yellow
Write-Host ""

Write-Host "Diagnostics Complete" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
