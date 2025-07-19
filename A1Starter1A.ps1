
# A1Starter1A.ps1
# Automated deployment verification and fix workflow for PocketPro:SBA
# Single entry point script

param (
    [string]$domain = "localhost",
    [string]$protocol = "http"
)

$ErrorActionPreference = "Continue"
$baseUrl = if ($domain -eq "localhost") {
    "http://localhost:10000"
} else {
    "$protocol://$domain"
}

Write-Host "===== PocketPro:SBA Automated Deployment Workflow =====" -ForegroundColor Cyan
Write-Host "Target: $baseUrl" -ForegroundColor Yellow
Write-Host ""

Write-Host "Press Enter to begin the automated deployment verification and fix workflow..." -ForegroundColor Magenta
[void][System.Console]::ReadLine()

# Step 1: Run verification
Write-Host "[1/4] Running deployment verification..." -ForegroundColor Yellow
try {
    pwsh .\verify-deployment.ps1 -domain $domain -protocol $protocol
} catch {
    Write-Host "[X] Error running verify-deployment.ps1: $_" -ForegroundColor Red
}

# Step 2: Run Python verification (cross-platform)
Write-Host "[2/4] Running Python deployment checks..." -ForegroundColor Yellow
try {
    python verify_render_deployment.py $baseUrl
} catch {
    Write-Host "[X] Error running verify_render_deployment.py: $_" -ForegroundColor Red
}

# Step 3: Run final checks and fixes recursively
Write-Host "[3/4] Running final checks and fixes..." -ForegroundColor Yellow
$fixScripts = @(
    'final_deployment_check.py',
    'final_port_fix_check.py',
    'final_rag_test.py',
    'fix-all.ps1',
    'fix-docker-build.ps1',
    'fix-frontend.ps1',
    'fix-network-config.ps1',
    'fix-chromadb.py',
    'fix-frontend-container.ps1',
    'fix-app-eslint.ps1',
    'fix-app-no-bootstrap.ps1',
    'fix-eslint-line66.ps1',
    'fix-react-bootstrap.ps1',
    'fix-startup.py',
    'fix_frontend_issues.py'
)
foreach ($script in $fixScripts) {
    if (Test-Path $script) {
        Write-Host "Running $script..." -ForegroundColor Cyan
        if ($script -like '*.ps1') {
            try { pwsh .\$script } catch { Write-Host "[X] Error running $script: $_" -ForegroundColor Red }
        } elseif ($script -like '*.py') {
            try { python $script } catch { Write-Host "[X] Error running $script: $_" -ForegroundColor Red }
        }
    }
}

# Step 4: Report summary
Write-Host "[4/4] Workflow complete. See above for results." -ForegroundColor Green
Write-Host "===== PocketPro:SBA Automated Report =====" -ForegroundColor Cyan
Write-Host "1. All verification and fix scripts executed recursively." -ForegroundColor White
Write-Host "2. Review any errors or warnings above." -ForegroundColor White
Write-Host "3. Test document upload and RAG functionality manually if needed." -ForegroundColor White
Write-Host "4. Monitor logs with: docker-compose logs -f" -ForegroundColor Green
Write-Host "\nWorkflow finished!" -ForegroundColor Cyan
