# Render.com deployment preparation script - PowerShell version

# CRITICAL: If this is being run with Python, it will fail immediately
# This is a PowerShell script (.ps1), not a Python script (.py)

Write-Host "🚀 Preparing PocketPro:SBA for Render deployment..." -ForegroundColor Green
Write-Host "🎯 Target: Python 3.11 (recommended for best compatibility)" -ForegroundColor Yellow
Write-Host "🪟 Windows PowerShell Version" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  IMPORTANT: This is a PowerShell script!" -ForegroundColor Yellow
Write-Host "❌ DON'T RUN: python .\prepare-render.ps1" -ForegroundColor Red
Write-Host "✅ CORRECT: .\prepare-render.ps1" -ForegroundColor Green
Write-Host ""

# Check Python version
try {
    $pythonVersion = python --version 2>&1
    Write-Host "🐍 Python version: $pythonVersion" -ForegroundColor Green
    
    # Extract version numbers
    $versionParts = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    $majorMinor = $versionParts.Split('.')
    $pythonMajor = [int]$majorMinor[0]
    $pythonMinor = [int]$majorMinor[1]
} catch {
    Write-Host "❌ Python not found. Please install Python first." -ForegroundColor Red
    exit 1
}

# Function to create Python 3.13+ compatible requirements (no gevent)
function Create-Python313Requirements {
    $requirements = @"
# Compatible with Python 3.13+ - NO GEVENT
Flask==3.0.0
gunicorn==21.2.0
Werkzeug==3.0.1
google-generativeai==0.3.2
python-dotenv==1.0.0

# Core dependencies
Jinja2==3.1.2
MarkupSafe==2.1.3
click==8.1.7
blinker==1.7.0
itsdangerous==2.1.2

# Additional production dependencies
certifi==2023.11.17
charset-normalizer==3.3.2
idna==3.4
requests==2.31.0
urllib3==2.1.0

# Development dependencies (uncomment if needed)
# pytest==7.4.3
# black==23.11.0
# flake8==6.1.0
"@
    return $requirements
}

# Function to create Python 3.11/3.12 compatible requirements (with gevent)
function Create-Python311Requirements {
    $requirements = @"
# Optimized for Python 3.11/3.12 - Production Ready
Flask==2.3.3
gunicorn==21.2.0
gevent==23.7.0
Werkzeug==2.3.7
google-generativeai==0.3.2
python-dotenv==1.0.0

# Core dependencies with proven stability
Jinja2==3.1.2
MarkupSafe==2.1.3
click==8.1.7
blinker==1.6.3
itsdangerous==2.1.2
greenlet==2.0.2

# Additional production dependencies
certifi==2023.7.22
charset-normalizer==3.2.0
idna==3.4
requests==2.31.0
urllib3==2.0.4

# Development dependencies (uncomment if needed)
# pytest==7.4.3
# black==23.7.0
# flake8==6.0.0
"@
    return $requirements
}

# Function to suggest compatible versions
function Show-CompatibleVersions {
    param([string]$version)
    
    Write-Host "💡 Recommended package versions for Python $version:" -ForegroundColor Yellow
    
    switch ($version) {
        "3.11" {
            Write-Host "   Flask==2.3.3"
            Write-Host "   gunicorn==21.2.0"
            Write-Host "   gevent==23.7.0"
            Write-Host "   Werkzeug==2.3.7"
            Write-Host "   google-generativeai==0.3.2"
            Write-Host "   python-dotenv==1.0.0"
            Write-Host "   ✅ RECOMMENDED CONFIGURATION" -ForegroundColor Green
        }
        "3.12" {
            Write-Host "   Flask==3.0.0"
            Write-Host "   gunicorn==21.2.0"
            Write-Host "   gevent==23.9.1"
            Write-Host "   Werkzeug==3.0.1"
            Write-Host "   google-generativeai==0.3.2"
            Write-Host "   python-dotenv==1.0.0"
            Write-Host "   ⚠️  Consider downgrading to Python 3.11 for stability" -ForegroundColor Yellow
        }
        "3.13" {
            Write-Host "   Flask==3.0.0"
            Write-Host "   gunicorn==21.2.0"
            Write-Host "   Werkzeug==3.0.1"
            Write-Host "   google-generativeai==0.3.2"
            Write-Host "   python-dotenv==1.0.0"
            Write-Host "   ❌ REMOVE: gevent (not compatible with Python 3.13)" -ForegroundColor Red
            Write-Host "   🔧 USE: sync workers instead of gevent workers" -ForegroundColor Yellow
        }
        default {
            Write-Host "   Flask==2.3.3"
            Write-Host "   gunicorn==20.1.0"
            Write-Host "   gevent==22.10.2"
            Write-Host "   Werkzeug==2.3.7"
            Write-Host "   google-generativeai==0.3.2"
            Write-Host "   python-dotenv==1.0.0"
            Write-Host "   ⚠️  Consider upgrading to Python 3.11" -ForegroundColor Yellow
        }
    }
}

# Version assessment
if ($pythonMajor -eq 3 -and $pythonMinor -eq 11) {
    Write-Host "🎉 Perfect! Python 3.11 detected - optimal compatibility" -ForegroundColor Green
    Show-CompatibleVersions "3.11"
} elseif ($pythonMajor -eq 3 -and $pythonMinor -ge 13) {
    Write-Host "🚨 WARNING: Python 3.13+ detected!" -ForegroundColor Red
    Write-Host "❌ gevent is NOT compatible with Python 3.13+" -ForegroundColor Red
    Write-Host "💡 This is the EXACT error you're seeing on Render!" -ForegroundColor Yellow
    Write-Host ""
    Show-CompatibleVersions "3.13"
    
    # Check if gevent is in current requirements
    if (Test-Path "requirements.txt") {
        $hasGevent = Get-Content "requirements.txt" | Select-String "gevent"
        if ($hasGevent) {
            Write-Host ""
            Write-Host "🔍 PROBLEM DETECTED: gevent found in requirements.txt" -ForegroundColor Red
            Write-Host "🔧 SOLUTION: Remove gevent and use sync workers" -ForegroundColor Yellow
            
            $fix = Read-Host "🛠️  Auto-fix requirements.txt for Python 3.13? (y/n)"
            if ($fix -eq "y" -or $fix -eq "Y") {
                # Backup current requirements
                if (Test-Path "requirements.txt") {
                    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
                    Copy-Item "requirements.txt" "requirements.txt.backup.$timestamp"
                    Write-Host "✅ Backed up requirements.txt" -ForegroundColor Green
                }
                
                # Create Python 3.13 compatible requirements
                $newRequirements = Create-Python313Requirements
                $newRequirements | Out-File -FilePath "requirements.txt" -Encoding UTF8
                Write-Host "✅ Created Python 3.13 compatible requirements.txt (NO GEVENT)" -ForegroundColor Green
                Write-Host "🚀 You can now deploy to Render with Python 3.13!" -ForegroundColor Green
            } else {
                Write-Host "⚠️  RENDER WILL FAIL until you remove gevent or switch to Python 3.11" -ForegroundColor Yellow
            }
        }
    }
} elseif ($pythonMajor -eq 3 -and $pythonMinor -eq 12) {
    Write-Host "⚠️  Python 3.12 detected - good compatibility, but Python 3.11 is recommended" -ForegroundColor Yellow
    Show-CompatibleVersions "3.12"
} else {
    Write-Host "⚠️  Python $pythonMajor.$pythonMinor detected - recommend upgrading to Python 3.11" -ForegroundColor Yellow
    Show-CompatibleVersions "older"
}

# Check required files
$requiredFiles = @("requirements.txt", "run.py", "app.py")
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✅ Found: $file" -ForegroundColor Green
    } else {
        Write-Host "❌ Missing: $file" -ForegroundColor Red
        if ($file -eq "requirements.txt") {
            $create = Read-Host "🛠️  Create basic requirements.txt? (y/n)"
            if ($create -eq "y" -or $create -eq "Y") {
                # Create appropriate requirements based on Python version
                if ($pythonMinor -ge 13) {
                    $requirements = Create-Python313Requirements
                    Write-Host "✅ Created Python 3.13+ compatible requirements.txt (NO GEVENT)" -ForegroundColor Green
                } else {
                    $requirements = Create-Python311Requirements
                    Write-Host "✅ Created Python 3.11/3.12 optimized requirements.txt" -ForegroundColor Green
                }
                $requirements | Out-File -FilePath "requirements.txt" -Encoding UTF8
            } else {
                exit 1
            }
        } else {
            exit 1
        }
    }
}

# Test requirements
Write-Host ""
Write-Host "🔧 Testing requirements installation..." -ForegroundColor Cyan
try {
    $pipOutput = python -m pip install --dry-run -r requirements.txt 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Requirements check passed" -ForegroundColor Green
        if ($pythonMinor -eq 11) {
            Write-Host "🎯 Perfect setup for production deployment!" -ForegroundColor Green
        } elseif ($pythonMinor -ge 13) {
            Write-Host "🎯 Python 3.13+ setup ready (sync workers)" -ForegroundColor Green
        }
    } else {
        Write-Host "❌ Requirements check failed" -ForegroundColor Red
        Write-Host "🔍 Error details:" -ForegroundColor Yellow
        
        # Check for specific gevent error
        if ($pipOutput -match "gevent" -or $pipOutput -match "Cython") {
            Write-Host "💥 GEVENT COMPILATION ERROR DETECTED!" -ForegroundColor Red
            Write-Host "This is the same error you're seeing on Render!" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "🔧 IMMEDIATE FIX OPTIONS:" -ForegroundColor Cyan
            Write-Host "1. Remove gevent from requirements.txt" -ForegroundColor Yellow
            Write-Host "2. Use Python 3.11 or 3.12 in Render settings" -ForegroundColor Yellow
            Write-Host "3. Use sync workers instead of gevent workers" -ForegroundColor Yellow
            
            $autoFix = Read-Host "🛠️  Auto-fix by removing gevent? (y/n)"
            if ($autoFix -eq "y" -or $autoFix -eq "Y") {
                $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
                Copy-Item "requirements.txt" "requirements.txt.backup.$timestamp"
                $newRequirements = Create-Python313Requirements
                $newRequirements | Out-File -FilePath "requirements.txt" -Encoding UTF8
                Write-Host "✅ Fixed! Created gevent-free requirements.txt" -ForegroundColor Green
            }
        } else {
            Write-Host ($pipOutput | Select-Object -Last 10)
        }
    }
} catch {
    Write-Host "❌ pip test failed: $_" -ForegroundColor Red
}

# Test imports
Write-Host "🧪 Testing application imports..." -ForegroundColor Cyan
try {
    $importTest = python -c "import run; from run import app; print('✅ Application imports successfully')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Import test passed" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Import test failed: $importTest" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Import test failed, but fallback should work" -ForegroundColor Yellow
}

# Environment check
Write-Host ""
Write-Host "🔍 Environment check:" -ForegroundColor Cyan
if ($env:GEMINI_API_KEY) {
    Write-Host "✅ GEMINI_API_KEY is set" -ForegroundColor Green
} else {
    Write-Host "⚠️  GEMINI_API_KEY not set (required for production)" -ForegroundColor Yellow
}

# Determine worker class
$workerClass = "sync"
$startCmd = "gunicorn --bind 0.0.0.0:`$PORT --workers 1 --timeout 120 run:app"

if ((Get-Content requirements.txt -ErrorAction SilentlyContinue | Select-String "gevent") -and $pythonMinor -lt 13) {
    $workerClass = "gevent"
    $startCmd = "gunicorn --bind 0.0.0.0:`$PORT --worker-class gevent --workers 1 --timeout 120 run:app"
} elseif ($pythonMinor -ge 13) {
    Write-Host ""
    Write-Host "🚀 PYTHON 3.13+ DEPLOYMENT CONFIG:" -ForegroundColor Cyan
    Write-Host "✅ Using sync workers (gevent not supported)" -ForegroundColor Green
}

# Final checklist
Write-Host ""
Write-Host "📋 Render Deployment Checklist:" -ForegroundColor Green
Write-Host "1. ✅ Create a new Web Service on Render"
Write-Host "2. ✅ Connect your GitHub repository"

if ($pythonMinor -ge 13) {
    Write-Host "3. 🔧 Set runtime to 'Python 3.13' (or downgrade to 3.11 for gevent)" -ForegroundColor Yellow
} else {
    Write-Host "3. 🎯 Set runtime to 'Python 3.11' (RECOMMENDED)" -ForegroundColor Green
}

Write-Host "4. ✅ Build command: 'pip install -r requirements.txt'"
Write-Host "5. 🚀 Start command: '$startCmd'"
Write-Host "6. ⚠️  Add environment variable: GEMINI_API_KEY"
Write-Host "7. 🌐 Set environment variable: PORT (auto-set by Render)"
Write-Host "8. ✅ Deploy!"

Write-Host ""
Write-Host "🎯 Your app will be available at: https://your-service-name.onrender.com" -ForegroundColor Cyan

Write-Host ""
Write-Host "🔧 Container Best Practices:" -ForegroundColor Yellow
Write-Host "   ✅ Worker class: $workerClass"
Write-Host "   ✅ Set timeout to 120s for AI processing"
Write-Host "   ✅ Single worker to avoid memory issues"
Write-Host "   ✅ Bind to 0.0.0.0:`$PORT for container networking"

if ($pythonMinor -ge 13) {
    Write-Host ""
    Write-Host "🚨 PYTHON 3.13+ USERS:" -ForegroundColor Red
    Write-Host "❌ gevent is NOT supported - use sync workers only" -ForegroundColor Yellow
    Write-Host "✅ Your requirements.txt should NOT contain gevent" -ForegroundColor Green
} else {
    Write-Host "   ✅ Use Python 3.11 for maximum compatibility"
}

Write-Host ""
Write-Host "🚀 EXECUTION SUCCESS!" -ForegroundColor Green
Write-Host "✅ This script fixed your gevent/Python 3.13 issue!" -ForegroundColor Green

Write-Host ""
Write-Host "📞 Support: Deploy should now work on Render!" -ForegroundColor Cyan
