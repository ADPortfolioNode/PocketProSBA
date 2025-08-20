@echo off
REM Production Deployment Script for PocketPro:SBA (Windows)
REM Validates and deploys the production Docker setup

echo 🚀 PocketPro:SBA Production Deployment
echo ======================================

REM Check prerequisites
echo Checking prerequisites...

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed
    pause
    exit /b 1
)

REM Check Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not installed
    pause
    exit /b 1
)

REM Check .env file
if not exist .env (
    echo ❌ .env file not found
    echo Please create .env file with required environment variables
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed

REM Build and start services
echo Building production Docker images...
docker-compose build --no-cache

echo Starting production services...
docker-compose up -d

REM Wait for services to be ready
echo Waiting for services to be ready...
timeout /t 30 /nobreak >nul

REM Health check
echo Performing health checks...

REM Check backend health
curl -s -o nul -w "%%{http_code}" http://localhost:5000/health > backend_health.txt
set /p backend_health=<backend_health.txt
del backend_health.txt

if "%backend_health%"=="200" (
    echo ✅ Backend health check passed
) else (
    echo ❌ Backend health check failed (HTTP %backend_health%)
)

REM Check ChromaDB health
curl -s -o nul -w "%%{http_code}" http://localhost:8000/api/v1/heartbeat > chroma_health.txt
set /p chroma_health=<chroma_health.txt
del chroma_health.txt

if "%chroma_health%"=="200" (
    echo ✅ ChromaDB health check passed
) else (
    echo ❌ ChromaDB health check failed (HTTP %chroma_health%)
)

REM Display service status
echo Service status:
docker-compose ps

REM Display logs
echo Recent logs:
docker-compose logs --tail=20

echo 🎉 Production deployment complete!
echo =====================================
echo Application is running at: http://localhost:5000
echo ChromaDB is running at: http://localhost:8000
echo.
echo To stop services: docker-compose down
echo To view logs: docker-compose logs -f
pause
