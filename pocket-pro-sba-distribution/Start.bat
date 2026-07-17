@echo off
echo ========================================
echo PocketPro SBA - Starting Application
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running.
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)
echo [OK] Docker is running
echo.

REM Create .env from .env.example if it doesn't exist
if not exist .env (
    echo Creating .env file from .env.example...
    copy .env.example .env >nul
    echo [OK] .env file created
    echo.
    echo IMPORTANT: Please edit .env and add your GEMINI_API_KEY
    echo Get your API key from: https://makersuite.google.com/app/apikey
    echo.
    echo Press any key to continue after adding your API key...
    pause >nul
) else (
    echo [OK] .env file exists
    echo.
)

REM Check for GEMINI_API_KEY
findstr /C:"GEMINI_API_KEY=" .env >nul
if %errorlevel% neq 0 (
    echo WARNING: GEMINI_API_KEY not found in .env file
    echo Please add your Gemini API key to .env:
    echo GEMINI_API_KEY=your_actual_api_key_here
    echo.
    echo Press any key to continue anyway...
    pause >nul
) else (
    findstr /C:"GEMINI_API_KEY=your_gemini_api_key_here" .env >nul
    if %errorlevel% equ 0 (
        echo WARNING: GEMINI_API_KEY is set to placeholder value
        echo Please edit .env and replace with your actual API key
        echo Get your API key from: https://makersuite.google.com/app/apikey
        echo.
        echo Press any key to continue anyway...
        pause >nul
    ) else (
        echo [OK] GEMINI_API_KEY is configured
    )
)
echo.

REM Determine which compose file to use for production
set "COMPOSE_FILE=docker-compose.yml"
if exist docker-compose.prod.yml (
    set "COMPOSE_FILE=docker-compose.prod.yml"
)

REM Build and start containers
echo Building and starting Docker containers using %COMPOSE_FILE%...
echo This may take several minutes on first run...
echo.
docker compose -f %COMPOSE_FILE% up --build -d

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start containers
    echo Run 'docker compose logs' to see error details
    pause
    exit /b 1
)

echo.
echo ========================================
echo Application Started Successfully!
echo ========================================
echo.
echo Access URLs:
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:5000
echo   ChromaDB: http://localhost:8000
echo.
echo Health Check:
echo   http://localhost:5000/api/health
echo.
echo To stop the application, double-click Stop.bat
echo.
echo Press any key to close this window...
pause >nul
