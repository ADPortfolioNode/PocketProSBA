@echo off
REM Render.com deployment preparation script for Windows

echo 🚀 Preparing PocketPro:SBA for Render deployment...
echo 🎯 Target: Python 3.11 (recommended for best compatibility)
echo 🪟 Windows Batch Version

REM Check Python version
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python first.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo 🐍 Python version: %python_version%

REM Check for required files
echo 📁 Checking required files...
if exist requirements.txt (echo ✅ Found: requirements.txt) else (echo ❌ Missing: requirements.txt)
if exist run.py (echo ✅ Found: run.py) else (echo ❌ Missing: run.py)
if exist app.py (echo ✅ Found: app.py) else (echo ❌ Missing: app.py)

REM Test requirements
echo 🔧 Testing requirements installation...
python -m pip install --dry-run -r requirements.txt >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Requirements check passed
) else (
    echo ❌ Requirements check failed
    echo 💡 Check your requirements.txt for Python version compatibility
)

REM Test imports
echo 🧪 Testing application imports...
python -c "import run; print('✅ Application imports successfully')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ Import test failed - check your app.py and run.py files
)

REM Environment check
echo 🔍 Environment check:
if "%GEMINI_API_KEY%"=="" (
    echo ⚠️ GEMINI_API_KEY not set (required for production)
) else (
    echo ✅ GEMINI_API_KEY is set
)

echo.
echo 📋 Render Deployment Checklist:
echo 1. ✅ Create a new Web Service on Render
echo 2. ✅ Connect your GitHub repository  
echo 3. 🎯 Set runtime to 'Python 3.11' (RECOMMENDED)
echo 4. ✅ Build command: 'pip install -r requirements.txt'
echo 5. 🚀 Start command: 'gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 run:app'
echo 6. ⚠️ Add environment variable: GEMINI_API_KEY
echo 7. 🌐 Set environment variable: PORT (auto-set by Render)
echo 8. ✅ Deploy!
echo.
echo 🎯 Your app will be available at: https://your-service-name.onrender.com
echo.
echo 💡 For full functionality, use: bash prepare-render.sh
pause
