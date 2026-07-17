@echo off
echo ============================================================
echo 🚀 STARTING POCKETPRO:SBA DEVELOPMENT ENVIRONMENT
echo ============================================================

echo.
echo 📋 CHECKING REQUIREMENTS...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python
    pause
    exit /b 1
)
echo ✅ Python found

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found! Please install Node.js
    pause
    exit /b 1
)
echo ✅ Node.js found

echo.
echo 🔧 STARTING BACKEND (Flask)...
echo    Backend will start on http://localhost:5000
echo    Health check: http://localhost:5000/health
echo.

REM Start backend in a new window
start "PocketPro Backend" cmd /k "python app.py"

REM Wait a moment for backend to start
echo Waiting 5 seconds for backend to initialize...
timeout /t 5 /nobreak >nul

echo.
echo 🌐 STARTING FRONTEND (React)...
echo    Frontend will start on http://localhost:3000
echo    Note: You may see some WebSocket warnings - these are normal!
echo.

REM Start frontend
cd /d "%~dp0frontend"
echo Starting React development server...
npm start

echo.
echo ============================================================
echo ✅ DEVELOPMENT ENVIRONMENT READY!
echo ============================================================
echo.
echo 📍 URLs:
echo    Frontend: http://localhost:3000
echo    Backend:  http://localhost:5000
echo    API Docs: http://localhost:5000/api/status
echo.
echo 💡 ABOUT THOSE CONSOLE ERRORS:
echo    • WebSocket errors are normal in development
echo    • "System info" logs show the app is working  
echo    • Connection reset errors happen when backend isn't ready
echo    • Apollo DevTools warning can be ignored
echo.
echo Press Ctrl+C to stop the frontend server
pause
