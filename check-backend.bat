@echo off
echo ===== PocketPro:SBA Backend Connectivity Check =====
echo.

REM Check local development backend (port 5000)
echo Checking if the local backend API is running on port 5000...
curl -s -o nul -w "%%{http_code}" http://localhost:5000/health
if %ERRORLEVEL% NEQ 0 (
    echo [X] Local backend API is NOT running or not accessible on port 5000
    echo     Make sure to start the local backend with 'python run.py'
) else (
    echo [√] Local backend API is running at http://localhost:5000
)
echo.

REM Check Docker-based backend (port 10000)
echo Checking if the Docker backend API is running on port 10000...
curl -s -o nul -w "%%{http_code}" http://localhost:10000/health
if %ERRORLEVEL% NEQ 0 (
    echo [X] Docker backend API is NOT running or not accessible on port 10000
    echo     Make sure your Docker containers are running with 'docker-compose up'
) else (
    echo [√] Docker backend API is running at http://localhost:10000
)
echo.

REM Check which backend the frontend is configured to use
echo Checking frontend configuration...
if exist "frontend\.env" (
    findstr "REACT_APP_BACKEND_URL" frontend\.env > nul
    if %ERRORLEVEL% EQU 0 (
        echo Frontend configuration (.env file):
        findstr "REACT_APP_BACKEND_URL" frontend\.env
    ) else (
        echo No API URL found in frontend\.env
    )
) else (
    echo No .env file found in frontend directory
)

if exist "frontend\.env.development" (
    findstr "REACT_APP_BACKEND_URL" frontend\.env.development > nul
    if %ERRORLEVEL% EQU 0 (
        echo Frontend development configuration (.env.development file):
        findstr "REACT_APP_BACKEND_URL" frontend\.env.development
    ) else (
        echo No API URL found in frontend\.env.development
    )
) else (
    echo No .env.development file found in frontend directory
)
echo.

echo ===== Troubleshooting Tips =====
echo 1. For local development:
echo    - Start backend: python run.py
echo    - Start frontend: cd frontend ^& npm start
echo.
echo 2. For Docker setup:
echo    - Start all containers: docker-compose up
echo    - Check logs: docker-compose logs
echo.
echo 3. Check your frontend .env files to ensure they point to the correct backend URL
echo    - For local: REACT_APP_BACKEND_URL=http://localhost:5000
echo    - For Docker: REACT_APP_BACKEND_URL=http://localhost:10000
echo.
