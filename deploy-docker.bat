@echo off
REM Docker deployment script for PocketPro:SBA Edition (Windows)

echo === PocketPro:SBA Edition Docker Deployment ===

REM Check if .env file exists
if not exist .env (
    echo Creating .env file from template...
    copy .env.template .env
    echo Please edit .env file with your API keys and configuration
    echo Required: GEMINI_API_KEY
    exit /b 1
)

REM Create necessary directories
if not exist uploads mkdir uploads
if not exist chromadb_data mkdir chromadb_data

echo Building and starting containers...

REM Stop any existing containers
docker-compose down

REM Build and start services
docker-compose up --build -d

echo === Deployment Complete ===
echo Application: http://localhost:10000
echo Backend API: http://localhost:5000
echo ChromaDB: http://localhost:8000
echo.
echo To view logs: docker-compose logs -f
echo To stop: docker-compose down
pause
