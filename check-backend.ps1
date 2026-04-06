Write-Host "===== PocketPro:SBA Backend Connectivity Check =====" -ForegroundColor Cyan
Write-Host ""

# Check local development backend (port 5000)
Write-Host "Checking if the local backend API is running on port 5000..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "[√] Local backend API is running at http://localhost:5000" -ForegroundColor Green
    Write-Host "    Status: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "[X] Local backend API is NOT running or not accessible on port 5000" -ForegroundColor Red
    Write-Host "    Make sure to start the local backend with 'python run.py'" -ForegroundColor Red
}
Write-Host ""

# Check Docker-based backend (port 10000)
Write-Host "Checking if the Docker backend API is running on port 10000..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:10000/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "[√] Docker backend API is running at http://localhost:10000" -ForegroundColor Green
    Write-Host "    Status: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "[X] Docker backend API is NOT running or not accessible on port 10000" -ForegroundColor Red
    Write-Host "    Make sure your Docker containers are running with 'docker-compose up'" -ForegroundColor Red
    Write-Host "    Error: $_" -ForegroundColor Red
}
Write-Host ""

# Add Docker build diagnostics
Write-Host "===== Docker Build Diagnostics =====" -ForegroundColor Cyan
Write-Host ""

# Check frontend App.js for ESLint errors
Write-Host "Checking frontend App.js for ESLint errors..." -ForegroundColor Yellow
$appJsPath = "frontend\src\App.js"

if (Test-Path $appJsPath) {
    $content = Get-Content $appJsPath -Raw
    $lines = $content -split "`n"
    $hasEslintIssue = $false
    
    for ($i = 0; $i -lt $lines.Length; $i++) {
        if ($lines[$i] -match "^\s*try\s*\{") {
            # Look ahead for a matching catch or finally
            $hasCatchOrFinally = $false
            $braceCount = 1  # Start with 1 for the opening brace of try
            $tryLineNumber = $i + 1;
            
            for ($j = $i + 1; $j -lt $lines.Length; $j++) {
                # Count braces to track nested blocks
                $openBraces = ([regex]::Matches($lines[$j], "\{")).Count
                $closeBraces = ([regex]::Matches($lines[$j], "\}")).Count
                $braceCount += $openBraces - $closeBraces
                
                # If we're back to the same level and found a catch/finally, we're good
                if ($braceCount -eq 0) {
                    if ($j + 1 -lt $lines.Length -and ($lines[$j + 1] -match "^\s*catch" -or $lines[$j + 1] -match "^\s*finally")) {
                        $hasCatchOrFinally = $true
                    }
                    break
                }
            }
            
            # If we didn't find a matching catch/finally, flag it
            if (-not $hasCatchOrFinally) {
                Write-Host "[X] ESLint Error: Missing catch or finally clause around line $tryLineNumber" -ForegroundColor Red
                Write-Host "    Code: $($lines[$tryLineNumber-1].Trim())" -ForegroundColor Yellow
                $hasEslintIssue = $true
                
                # If we're near line 66 (the reported error location)
                if ([Math]::Abs($tryLineNumber - 66) -lt 5) {
                    Write-Host "    This appears to be the error reported in the build logs (line 66)" -ForegroundColor Magenta
                    Write-Host "    Showing context around line 66:" -ForegroundColor Yellow
                    $startLine = [Math]::Max(60, $tryLineNumber - 5)
                    $endLine = [Math]::Min($lines.Length, $tryLineNumber + 10)
                    
                    for ($k = $startLine - 1; $k -lt $endLine; $k++) {
                        $lineNum = $k + 1
                        if ($lineNum -eq $tryLineNumber) {
                            Write-Host "    $lineNum: $($lines[$k])" -ForegroundColor Red
                        } else {
                            Write-Host "    $lineNum: $($lines[$k])" -ForegroundColor Gray
                        }
                    }
                    
                    # Provide specific fix instructions for line 66
                    Write-Host "`n    DIRECT FIX INSTRUCTIONS:" -ForegroundColor Green
                    Write-Host "    1. Run the automatic fix script: .\fix-eslint-line66.ps1" -ForegroundColor Green
                    Write-Host "    2. Or manually add a catch block right after the closing brace of this try block" -ForegroundColor Green
                }
            }
        }
    }
    
    if (-not $hasEslintIssue) {
        Write-Host "[?] No obvious ESLint issues found in App.js" -ForegroundColor Yellow
        Write-Host "    The issue may be in another file or more complex than a missing catch clause" -ForegroundColor Yellow
    }
} else {
    Write-Host "[X] App.js not found at $appJsPath" -ForegroundColor Red
}
Write-Host ""

# Check Docker containers status
Write-Host "Checking Docker container status..." -ForegroundColor Yellow
try {
    $dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
    if ($dockerInstalled) {
        $containersOutput = & docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        Write-Host "Docker containers:" -ForegroundColor Cyan
        Write-Host $containersOutput -ForegroundColor White
        
        # Check if there are frontend and backend containers
        $hasFrontend = $containersOutput -match "frontend"
        $hasBackend = $containersOutput -match "backend"
        
        if (-not $hasFrontend) {
            Write-Host "[X] No frontend container found running" -ForegroundColor Red
        }
        
        if (-not $hasBackend) {
            Write-Host "[X] No backend container found running" -ForegroundColor Red
        }
    } else {
        Write-Host "[X] Docker not found or not in PATH" -ForegroundColor Red
    }
} catch {
    Write-Host "[X] Error checking Docker status: $_" -ForegroundColor Red
}
Write-Host ""

# Check frontend environment configuration
Write-Host "Checking frontend configuration..." -ForegroundColor Yellow
$envPath = "frontend\.env"
$envDevPath = "frontend\.env.development"

if (Test-Path $envPath) {
    $envContent = Get-Content $envPath | Select-String "REACT_APP_API_URL"
    if ($envContent) {
        Write-Host "Frontend configuration (.env file):" -ForegroundColor Cyan
        Write-Host $envContent -ForegroundColor White
    } else {
        Write-Host "No API URL found in frontend\.env" -ForegroundColor Yellow
    }
} else {
    Write-Host "No .env file found in frontend directory" -ForegroundColor Yellow
}

if (Test-Path $envDevPath) {
    $envDevContent = Get-Content $envDevPath | Select-String "REACT_APP_API_URL"
    if ($envDevContent) {
        Write-Host "Frontend development configuration (.env.development file):" -ForegroundColor Cyan
        Write-Host $envDevContent -ForegroundColor White
    } else {
        Write-Host "No API URL found in frontend\.env.development" -ForegroundColor Yellow
    }
} else {
    Write-Host "No .env.development file found in frontend directory" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "===== Quick Fix Solutions =====" -ForegroundColor Cyan
Write-Host "1. Fix ESLint error in App.js:" -ForegroundColor White
Write-Host "   - Open frontend/src/App.js" -ForegroundColor White
Write-Host "   - Look for the try block around line 66" -ForegroundColor White
Write-Host "   - Add a catch block after the try block:" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "     try {" -ForegroundColor Green
Write-Host "       // existing code" -ForegroundColor Green
Write-Host "     } catch (error) {" -ForegroundColor Green
Write-Host "       console.error('Error:', error);" -ForegroundColor Green
Write-Host "     }" -ForegroundColor Green
Write-Host ""

Write-Host "2. Or bypass ESLint in Docker build:" -ForegroundColor White
Write-Host "   - Create a docker-compose.override.yml file with:" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "     version: '3'" -ForegroundColor Yellow
Write-Host "     services:" -ForegroundColor Yellow
Write-Host "       frontend:" -ForegroundColor Yellow
Write-Host "         environment:" -ForegroundColor Yellow
Write-Host "           - CI=false" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. To automatically create the override file and rebuild:" -ForegroundColor White
Write-Host "   - Run: .\fix-docker-build.ps1" -ForegroundColor White
Write-Host ""

# Create fix-docker-build.ps1 script
$fixScript = @'
# Auto-created Docker build fix script
Write-Host "Creating docker-compose.override.yml to bypass ESLint errors..." -ForegroundColor Cyan
@"
version: '3'
services:
  frontend:
    environment:
      - CI=false
      - ESLINT_NO_DEV_ERRORS=true
"@ | Out-File -FilePath "docker-compose.override.yml" -Encoding utf8

Write-Host "Restarting Docker containers with the fix..." -ForegroundColor Cyan
docker-compose down
docker-compose up -d --build

Write-Host "Fix applied! The build should now complete successfully." -ForegroundColor Green
Write-Host "Note: This is a temporary fix. You should still fix the ESLint error in App.js." -ForegroundColor Yellow
'@

# Create the fix script file if it doesn't exist
$fixScriptPath = "fix-docker-build.ps1"
if (-not (Test-Path $fixScriptPath)) {
    Set-Content -Path $fixScriptPath -Value $fixScript
    Write-Host "Created $fixScriptPath to help fix Docker build issues" -ForegroundColor Green
}

Write-Host "===== Troubleshooting Tips =====" -ForegroundColor Cyan
Write-Host "1. For local development:" -ForegroundColor White
Write-Host "   - Start backend: python run.py" -ForegroundColor White
Write-Host "   - Start frontend: cd frontend & npm start" -ForegroundColor White
Write-Host ""
Write-Host "2. For Docker setup:" -ForegroundColor White
Write-Host "   - Start all containers: docker-compose up" -ForegroundColor White
Write-Host "   - Check logs: docker-compose logs" -ForegroundColor White
Write-Host ""
Write-Host "3. Check your frontend .env files to ensure they point to the correct backend URL" -ForegroundColor White
Write-Host "   - For local: REACT_APP_API_URL=http://localhost:5000" -ForegroundColor White
Write-Host "   - For Docker: REACT_APP_API_URL=http://localhost:10000" -ForegroundColor White
