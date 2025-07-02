@echo off
echo Starting PocketPro:SBA Edition (Backend and Frontend)...

REM Start the backend in a new window
start "PocketPro Backend" cmd /c "python run.py"

REM Wait a moment for the backend to initialize
timeout /t 5

REM Start the frontend
cd /d "%~dp0frontend"
echo Starting frontend...
npm start
