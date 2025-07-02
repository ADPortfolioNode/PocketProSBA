@echo off
echo Checking if backend is running...
curl -s -o nul -w "%%{http_code}" http://localhost:10000/health

if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Backend API is NOT running or not accessible
    echo The frontend will start but may not function correctly without the backend
    echo Start the backend with 'docker-compose up' or 'deploy-docker.bat' in a separate terminal
    echo.
    timeout /t 3
)

echo Starting PocketPro:SBA Edition Frontend...
cd /d "%~dp0frontend"
npm start
