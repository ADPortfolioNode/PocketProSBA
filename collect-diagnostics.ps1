# PowerShell script to collect diagnostic information for PocketPro:SBA deployment
# This script gathers information about the environment and application configuration
# Run from the project root directory before deploying to Render.com

Write-Host "=== PocketPro:SBA Deployment Diagnostics ===" -ForegroundColor Cyan
Write-Host "Collecting diagnostic information for troubleshooting..."
Write-Host ""

# Create diagnostics directory
$DIAG_DIR = "deployment_diagnostics"
if (-not (Test-Path $DIAG_DIR)) {
    New-Item -ItemType Directory -Path $DIAG_DIR | Out-Null
}

# Function to check if a command exists
function Test-CommandExists {
    param($command)
    $exists = $null -ne (Get-Command $command -ErrorAction SilentlyContinue)
    return $exists
}

# Collect system information
Write-Host "Collecting system information..." -ForegroundColor Yellow
$SYS_INFO = "$(Get-Date) - System Information`n"
$SYS_INFO += "OS: $([System.Environment]::OSVersion.VersionString)`n"
$SYS_INFO += "PowerShell: $($PSVersionTable.PSVersion)`n"
$SYS_INFO += "Architecture: $([System.Environment]::Is64BitOperatingSystem ? '64-bit' : '32-bit')`n"

# Check for required tools
$SYS_INFO += "`nRequired Tools:`n"
$TOOLS = @("python", "pip", "docker", "git", "npm", "node")
foreach ($tool in $TOOLS) {
    $exists = Test-CommandExists $tool
    $SYS_INFO += "$tool: $(if ($exists) { 'Installed' } else { 'Not installed' })`n"
    
    if ($exists) {
        try {
            $version = Invoke-Expression "$tool --version 2>&1"
            $SYS_INFO += "  Version: $version`n"
        } catch {
            $SYS_INFO += "  Version: Error getting version`n"
        }
    }
}

# Save system info
$SYS_INFO | Out-File -FilePath "$DIAG_DIR\system_info.txt"

# Check Python environment
Write-Host "Checking Python environment..." -ForegroundColor Yellow
if (Test-CommandExists "python") {
    # Get Python version and installed packages
    python --version 2>&1 | Out-File -FilePath "$DIAG_DIR\python_version.txt"
    pip list | Out-File -FilePath "$DIAG_DIR\pip_packages.txt"
    
    # Try to import key modules
    $MODULES = @("flask", "google.generativeai", "numpy", "chromadb")
    $MODULE_INFO = "Python Module Availability:`n"
    foreach ($module in $MODULES) {
        try {
            $result = python -c "import $module; print(f'$module: Available (version: {$module.__version__})')" 2>&1
            $MODULE_INFO += "$result`n"
        } catch {
            $MODULE_INFO += "$module: Not available or error importing`n"
        }
    }
    $MODULE_INFO | Out-File -FilePath "$DIAG_DIR\python_modules.txt"
}

# Check frontend environment
Write-Host "Checking frontend environment..." -ForegroundColor Yellow
if (Test-Path "frontend\package.json") {
    Copy-Item "frontend\package.json" -Destination "$DIAG_DIR\package.json"
    
    if (Test-CommandExists "npm") {
        Set-Location "frontend"
        npm list --depth=0 | Out-File -FilePath "..\$DIAG_DIR\npm_packages.txt"
        Set-Location ".."
    }
}

# Check Docker
Write-Host "Checking Docker..." -ForegroundColor Yellow
if (Test-CommandExists "docker") {
    docker version | Out-File -FilePath "$DIAG_DIR\docker_version.txt"
    docker info | Out-File -FilePath "$DIAG_DIR\docker_info.txt"
}

# Check configuration files
Write-Host "Collecting configuration files..." -ForegroundColor Yellow
$CONFIG_FILES = @(
    "render.yaml",
    "Dockerfile.render",
    "wsgi.py",
    "gunicorn.conf.py",
    "requirements-render-minimal.txt",
    ".env"
)

foreach ($file in $CONFIG_FILES) {
    if (Test-Path $file) {
        Copy-Item $file -Destination "$DIAG_DIR\$file"
    }
}

# Create deployment checklist
$CHECKLIST = @"
# Render.com Deployment Checklist

## Pre-Deployment
- [ ] Requirements file contains all necessary dependencies
- [ ] Docker build completes successfully
- [ ] Application runs locally with Docker
- [ ] Environment variables are properly set
- [ ] Dockerfile.render is properly configured

## Deployment
- [ ] GitHub repository is up to date
- [ ] Render.com account is set up
- [ ] GEMINI_API_KEY is ready to use
- [ ] Blueprint deployment or manual service configuration ready

## Post-Deployment
- [ ] Backend service starts successfully
- [ ] Frontend connects to backend
- [ ] Health check endpoint returns 200
- [ ] Application functionality works
"@

$CHECKLIST | Out-File -FilePath "$DIAG_DIR\deployment_checklist.md"

# Create a zip file with all diagnostics
Write-Host "Creating diagnostics archive..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$zipFile = "pocketpro_diagnostics_$timestamp.zip"

if (Test-CommandExists "Compress-Archive") {
    Compress-Archive -Path $DIAG_DIR -DestinationPath $zipFile
    Write-Host "Diagnostics archive created: $zipFile" -ForegroundColor Green
} else {
    Write-Host "Unable to create zip archive. Please manually zip the $DIAG_DIR directory." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Diagnostics Complete ===" -ForegroundColor Cyan
Write-Host "Diagnostic information has been collected in the $DIAG_DIR directory"
Write-Host "If you encounter deployment issues, please include this information when seeking assistance."
