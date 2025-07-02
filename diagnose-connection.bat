@echo off
echo ===== PocketPro:SBA Connection Diagnostics =====
echo.

:: Check local backend (port 5000)
echo Checking Local Backend API (Port 5000)...
curl -s -o backend-local-health.tmp http://localhost:5000/health
if %ERRORLEVEL% EQU 0 (
    echo [OK] Local Backend API is running at http://localhost:5000
    type backend-local-health.tmp
    del backend-local-health.tmp
) else (
    echo [ERROR] Local Backend API is NOT running or not accessible
    echo         Make sure to start the local backend with 'python run.py'
)
echo.

:: Check Docker backend (port 10000)
echo Checking Docker Backend API (Port 10000)...
curl -s -o backend-docker-health.tmp http://localhost:10000/health
if %ERRORLEVEL% EQU 0 (
    echo [OK] Docker Backend API is running at http://localhost:10000
    type backend-docker-health.tmp
    del backend-docker-health.tmp
) else (
    echo [ERROR] Docker Backend API is NOT running or not accessible on port 10000
    echo.
    echo Attempting alternate endpoint paths with NGINX...
    curl -s -o backend-docker-api-health.tmp http://localhost:10000/api/health
    if %ERRORLEVEL% EQU 0 (
        echo [OK] API health endpoint is accessible at http://localhost:10000/api/health
        type backend-docker-api-health.tmp
        del backend-docker-api-health.tmp
    ) else (
        echo [ERROR] API health endpoint is NOT accessible at http://localhost:10000/api/health
    )
)
echo.

:: Check additional API endpoints
echo Testing Additional API Endpoints (Docker setup)...
curl -s -o backend-docker-api-info.tmp http://localhost:10000/api/info
if %ERRORLEVEL% EQU 0 (
    echo [OK] API info endpoint is accessible
    del backend-docker-api-info.tmp
) else (
    echo [ERROR] API info endpoint is NOT accessible
)

curl -s -o backend-docker-api-models.tmp http://localhost:10000/api/models
if %ERRORLEVEL% EQU 0 (
    echo [OK] API models endpoint is accessible
    del backend-docker-api-models.tmp
) else (
    echo [ERROR] API models endpoint is NOT accessible
)
echo.

:: Check frontend configuration
echo Checking Frontend Configuration...
if exist "frontend\.env" (
    echo [OK] .env file exists
    findstr "REACT_APP_BACKEND_URL" frontend\.env
) else (
    echo [ERROR] .env file not found
    echo         Create a .env file in the frontend directory with REACT_APP_BACKEND_URL=http://localhost:10000
)

if exist "frontend\.env.development" (
    echo [OK] .env.development file exists
    findstr "REACT_APP_BACKEND_URL" frontend\.env.development
) else (
    echo [INFO] .env.development file not found
)

if exist "frontend\package.json" (
    echo [OK] package.json exists
    findstr "proxy" frontend\package.json
) else (
    echo [ERROR] package.json not found
)
echo.

:: Check Docker status if available
echo Checking Docker Status...
docker info > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Docker is running
    
    echo Checking containers...
    docker ps | findstr "backend" > nul
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Backend container is running
    ) else (
        echo [ERROR] Backend container is NOT running
        echo         Start with: docker-compose up -d
    )
    
    docker ps | findstr "frontend" > nul
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Frontend container is running
    ) else (
        echo [ERROR] Frontend container is NOT running
        echo         Start with: docker-compose up -d
    )
    
    docker ps | findstr "chromadb" > nul
    if %ERRORLEVEL% EQU 0 (
        echo [OK] ChromaDB container is running
    ) else (
        echo [ERROR] ChromaDB container is NOT running
        echo         Start with: docker-compose up -d
    )
) else (
    echo [INFO] Docker is NOT running or not installed
    echo       To use Docker setup, start Docker Desktop before continuing
)
echo.

:: Check network connectivity
echo Checking Network Connectivity...
netstat -an | findstr ":5000" > nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Port 5000 is in use (likely by the local backend)
) else (
    echo [INFO] Port 5000 is not in use - local backend may not be running
)

netstat -an | findstr ":10000" > nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Port 10000 is in use (likely by the Docker frontend/NGINX)
) else (
    echo [INFO] Port 10000 is not in use - Docker setup may not be running
)

netstat -an | findstr ":8000" > nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Port 8000 is in use (likely by ChromaDB)
) else (
    echo [INFO] Port 8000 is not in use - ChromaDB may not be running
)
echo.

echo ===== Recommended Fixes =====
echo 1. Update the nginx.conf to properly proxy the /health endpoint:
echo.
echo     location /health {
echo         proxy_pass http://backend:5000/health;
echo         proxy_set_header Host $host;
echo         proxy_set_header X-Real-IP $remote_addr;
echo         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
echo         proxy_set_header X-Forwarded-Proto $scheme;
echo     }
echo.
echo 2. OR Update your App.js to use the API prefix for health checks:
echo.
echo     // Instead of:
echo     const healthCheck = await fetch(`${backendUrl}/health`);
echo.
echo     // Use:
echo     const healthCheck = await fetch(`${backendUrl}/api/health`);
echo.
echo 3. Restart your Docker containers with:
echo     docker-compose down
echo     docker-compose up -d
echo.

echo Diagnostics Complete
echo ===================
