# Comprehensive project verification script

Write-Host "===== PocketPro:SBA Project Verification =====" -ForegroundColor Cyan
Write-Host "Checking for project consistency and detecting possible regressions" -ForegroundColor Yellow
Write-Host ""

# Initialize tracking variables
$backendEndpoints = @()
$frontendApiCalls = @()
$issues = @()

# 1. Check project structure
Write-Host "1. Verifying Project Structure..." -ForegroundColor Cyan
$requiredDirs = @("frontend", "backend", "nginx")
$requiredFiles = @(
    "docker-compose.yml",
    "frontend/package.json", 
    "frontend/src/App.js",
    "backend/requirements.txt"
)

foreach ($dir in $requiredDirs) {
    if (Test-Path $dir -PathType Container) {
        Write-Host "  [√] $dir directory exists" -ForegroundColor Green
    } else {
        Write-Host "  [X] $dir directory missing" -ForegroundColor Red
        $issues += "Missing directory: $dir"
    }
}

foreach ($file in $requiredFiles) {
    if (Test-Path $file -PathType Leaf) {
        Write-Host "  [√] $file exists" -ForegroundColor Green
    } else {
        Write-Host "  [X] $file missing" -ForegroundColor Red
        $issues += "Missing file: $file"
    }
}
Write-Host ""

# 2. Check Backend API endpoints
Write-Host "2. Analyzing Backend API Endpoints..." -ForegroundColor Cyan
if (Test-Path "backend" -PathType Container) {
    $pythonFiles = Get-ChildItem -Path "backend" -Recurse -Filter "*.py"
    
    foreach ($file in $pythonFiles) {
        $content = Get-Content $file.FullName -Raw
        $routes = [regex]::Matches($content, '@app\.route\([''"]([^''"]+)[''"]')
        
        foreach ($route in $routes) {
            $endpoint = $route.Groups[1].Value
            $backendEndpoints += $endpoint
            Write-Host "  Found endpoint: $endpoint in $($file.Name)" -ForegroundColor Green
        }
    }
    
    if ($backendEndpoints.Count -eq 0) {
        Write-Host "  [!] No API endpoints found in backend code" -ForegroundColor Yellow
        $issues += "No API endpoints detected in backend Python files"
    } else {
        Write-Host "  [√] Found $($backendEndpoints.Count) API endpoints in backend code" -ForegroundColor Green
    }
} else {
    Write-Host "  [X] Cannot analyze backend endpoints - directory missing" -ForegroundColor Red
}
Write-Host ""

# 3. Check Frontend API calls
Write-Host "3. Analyzing Frontend API Calls..." -ForegroundColor Cyan
if (Test-Path "frontend" -PathType Container) {
    $jsFiles = Get-ChildItem -Path "frontend\src" -Recurse -Filter "*.js"
    
    foreach ($file in $jsFiles) {
        $content = Get-Content $file.FullName -Raw
        $fetchCalls = [regex]::Matches($content, '(?:fetch|axios\.get|axios\.post|axios\.put|axios\.delete)\([''"`]([^)]+?)[''"`]')
        
        foreach ($call in $fetchCalls) {
            $apiCall = $call.Groups[1].Value
            
            # Extract the endpoint path if it contains a full URL
            if ($apiCall -match "http[s]?://.*?(/api/[^\s'`"]+)") {
                $apiCall = $matches[1]
            }
            
            # Skip if it's not an API call
            if ($apiCall -match "/api/" -or $apiCall -eq "/health") {
                $frontendApiCalls += $apiCall
                Write-Host "  Found API call: $apiCall in $($file.Name)" -ForegroundColor Green
            }
        }
    }
    
    if ($frontendApiCalls.Count -eq 0) {
        Write-Host "  [!] No API calls found in frontend code" -ForegroundColor Yellow
        $issues += "No API calls detected in frontend JavaScript files"
    } else {
        Write-Host "  [√] Found $($frontendApiCalls.Count) API calls in frontend code" -ForegroundColor Green
    }
} else {
    Write-Host "  [X] Cannot analyze frontend API calls - directory missing" -ForegroundColor Red
}
Write-Host ""

# 4. Cross-reference endpoints and API calls
Write-Host "4. Cross-referencing Backend Endpoints with Frontend API Calls..." -ForegroundColor Cyan

$unmatchedFrontendCalls = @()
foreach ($call in $frontendApiCalls) {
    $found = $false
    
    # Clean up the API call to match backend endpoint format
    $cleanCall = $call -replace '\?.*$', '' # Remove query parameters
    
    foreach ($endpoint in $backendEndpoints) {
        # Direct match
        if ($cleanCall -eq $endpoint) {
            $found = $true
            break
        }
        
        # Check for parameterized routes
        if ($endpoint -match '<[^>]+>') {
            $pattern = $endpoint -replace '<[^>]+>', '[^/]+'
            if ($cleanCall -match "^$pattern$") {
                $found = $true
                break
            }
        }
    }
    
    if (-not $found) {
        $unmatchedFrontendCalls += $call
        Write-Host "  [!] Frontend API call '$call' has no matching backend endpoint" -ForegroundColor Yellow
        $issues += "Unmatched frontend API call: $call"
    }
}

$unmatchedBackendEndpoints = @()
foreach ($endpoint in $backendEndpoints) {
    $found = $false
    
    # Skip /health endpoint as it might be used only for monitoring
    if ($endpoint -eq "/health") {
        continue
    }
    
    # Skip routes with parameters as they will be handled differently
    if ($endpoint -match '<[^>]+>') {
        # Convert to regex pattern
        $pattern = $endpoint -replace '<[^>]+>', '[^/]+'
        
        foreach ($call in $frontendApiCalls) {
            $cleanCall = $call -replace '\?.*$', '' # Remove query parameters
            if ($cleanCall -match "^$pattern$") {
                $found = $true
                break
            }
        }
    } else {
        foreach ($call in $frontendApiCalls) {
            $cleanCall = $call -replace '\?.*$', '' # Remove query parameters
            if ($cleanCall -eq $endpoint) {
                $found = $true
                break
            }
        }
    }
    
    if (-not $found) {
        $unmatchedBackendEndpoints += $endpoint
        Write-Host "  [!] Backend endpoint '$endpoint' is not called from frontend" -ForegroundColor Yellow
        $issues += "Unused backend endpoint: $endpoint"
    }
}

if ($unmatchedFrontendCalls.Count -eq 0 -and $unmatchedBackendEndpoints.Count -eq 0) {
    Write-Host "  [√] All frontend API calls have corresponding backend endpoints" -ForegroundColor Green
}
Write-Host ""

# 5. Check for ESLint issues in the frontend
Write-Host "5. Checking for ESLint Issues in Frontend..." -ForegroundColor Cyan
$appJsPath = "frontend\src\App.js"

if (Test-Path $appJsPath) {
    $content = Get-Content $appJsPath -Raw
    $lines = $content -split "`n"
    $eslintIssues = @()
    
    for ($i = 0; $i -lt $lines.Length; $i++) {
        if ($lines[$i] -match "^\s*try\s*\{") {
            # Look ahead for a matching catch or finally
            $hasCatchOrFinally = $false
            $braceCount = 1  # Start with 1 for the opening brace of try
            $tryLineNumber = $i + 1
            
            for ($j = $i + 1; $j -lt $lines.Length; $j++) {
                # Count braces to track nested blocks
                $openBraces = ([regex]::Matches($lines[$j], "\{")).Count
                $closeBraces = ([regex]::Matches($lines[$j], "\}")).Count
                $braceCount += $openBraces - $closeBraces
                
                # If we're back to the same level, check for catch/finally
                if ($braceCount -eq 0) {
                    if ($j + 1 -lt $lines.Length -and ($lines[$j + 1] -match "^\s*catch" -or $lines[$j + 1] -match "^\s*finally")) {
                        $hasCatchOrFinally = $true
                    }
                    break
                }
            }
            
            # If we didn't find a matching catch/finally, flag it
            if (-not $hasCatchOrFinally) {
                $eslintIssues += "Line $tryLineNumber: Missing catch or finally clause"
                Write-Host "  [X] ESLint issue at line $tryLineNumber: Missing catch or finally clause" -ForegroundColor Red
                $issues += "ESLint issue in App.js at line $tryLineNumber: Missing catch or finally clause"
            }
        }
    }
    
    if ($eslintIssues.Count -eq 0) {
        Write-Host "  [√] No obvious ESLint issues found in App.js" -ForegroundColor Green
    }
} else {
    Write-Host "  [X] Cannot check for ESLint issues - App.js not found" -ForegroundColor Red
}
Write-Host ""

# 6. Check Docker configuration
Write-Host "6. Verifying Docker Configuration..." -ForegroundColor Cyan
$dockerComposePath = "docker-compose.yml"

if (Test-Path $dockerComposePath) {
    $content = Get-Content $dockerComposePath -Raw
    
    # Check for version (obsolete attribute)
    if ($content -match "version\s*:") {
        Write-Host "  [!] docker-compose.yml contains obsolete 'version' attribute" -ForegroundColor Yellow
        $issues += "docker-compose.yml contains obsolete 'version' attribute"
    }
    
    # Check for essential services
    $services = @("frontend", "backend", "nginx")
    foreach ($service in $services) {
        if ($content -match "^\s*$service\s*:") {
            Write-Host "  [√] docker-compose.yml contains $service service" -ForegroundColor Green
        } else {
            Write-Host "  [X] docker-compose.yml is missing $service service" -ForegroundColor Red
            $issues += "docker-compose.yml is missing $service service"
        }
    }
    
    # Check for ESLint bypass
    if ($content -match "CI=false") {
        Write-Host "  [√] ESLint bypass configured in docker-compose.yml" -ForegroundColor Green
    } else {
        Write-Host "  [!] ESLint bypass not found in docker-compose.yml" -ForegroundColor Yellow
        $issues += "ESLint bypass not configured in docker-compose.yml"
    }
} else {
    Write-Host "  [X] docker-compose.yml not found" -ForegroundColor Red
    $issues += "Missing docker-compose.yml"
}
Write-Host ""

# 7. Check nginx configuration
Write-Host "7. Checking Nginx Configuration..." -ForegroundColor Cyan
$nginxConfigPath = "nginx\nginx.conf"

if (Test-Path $nginxConfigPath) {
    $content = Get-Content $nginxConfigPath -Raw
    
    # Check for health endpoint configuration
    if ($content -match "location\s+/health") {
        Write-Host "  [√] Nginx configured to proxy /health endpoint" -ForegroundColor Green
    } else {
        Write-Host "  [X] Nginx missing configuration for /health endpoint" -ForegroundColor Red
        $issues += "Nginx configuration missing /health endpoint proxy"
    }
    
    # Check for API proxy
    if ($content -match "location\s+/api") {
        Write-Host "  [√] Nginx configured to proxy /api endpoints" -ForegroundColor Green
    } else {
        Write-Host "  [X] Nginx missing configuration for /api proxy" -ForegroundColor Red
        $issues += "Nginx configuration missing /api proxy"
    }
} else {
    Write-Host "  [!] nginx.conf not found at expected location" -ForegroundColor Yellow
    $issues += "nginx.conf not found at expected location"
}
Write-Host ""

# Summary
Write-Host "===== Verification Summary =====" -ForegroundColor Cyan

if ($issues.Count -eq 0) {
    Write-Host "`nAll checks passed! No issues found." -ForegroundColor Green
} else {
    Write-Host "`nFound $($issues.Count) issues that need attention:" -ForegroundColor Yellow
    foreach ($issue in $issues) {
        Write-Host "  • $issue" -ForegroundColor Yellow
    }
    
    Write-Host "`nSuggested fixes:" -ForegroundColor Cyan
    
    # ESLint fixes
    $hasEslintIssues = $issues | Where-Object { $_ -match "ESLint" }
    if ($hasEslintIssues) {
        Write-Host "  1. Fix ESLint issues:" -ForegroundColor White
        Write-Host "     • Run: .\fix-eslint-line66.ps1" -ForegroundColor White
        Write-Host "     • Or add CI=false to frontend environment in docker-compose.yml" -ForegroundColor White
    }
    
    # Docker compose fixes
    $hasDockerIssues = $issues | Where-Object { $_ -match "docker-compose" }
    if ($hasDockerIssues) {
        Write-Host "  2. Fix Docker configuration:" -ForegroundColor White
        Write-Host "     • Remove 'version' attribute from docker-compose.yml" -ForegroundColor White
        Write-Host "     • Add CI=false to frontend environment" -ForegroundColor White
    }
    
    # Endpoint mismatch fixes
    $hasEndpointIssues = $issues | Where-Object { $_ -match "API call|endpoint" }
    if ($hasEndpointIssues) {
        Write-Host "  3. Fix API endpoint mismatches:" -ForegroundColor White
        Write-Host "     • Ensure frontend calls match backend endpoints" -ForegroundColor White
        Write-Host "     • Update frontend API URLs or backend routes as needed" -ForegroundColor White
    }
}

Write-Host "`nRun backend connectivity check with: .\check-backend.ps1" -ForegroundColor Cyan
