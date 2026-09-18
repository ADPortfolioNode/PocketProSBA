@echo off
setlocal EnableExtensions
title PocketPro:SBA - Stopping

cd /d "%~dp0"
if not exist "docker-compose.yml" if not exist "docker-compose.dev.yml" (
    echo [ERROR] docker-compose.yml not found.
    echo Please run this file from the PocketProSBA project folder.
    goto :fail
)

echo.
echo ============================================================
echo   PocketPro:SBA - Stopping
echo ============================================================
echo.

where docker >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not on your PATH.
    goto :fail
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [WARN] Docker Desktop does not appear to be running.
    echo Containers may already be stopped.
    goto :done
)

echo [STOP] Shutting down PocketPro:SBA containers ...
if exist "docker-compose.dev.yml" (
    docker compose -f docker-compose.dev.yml down --timeout 30
)
if exist "docker-compose.yml" (
    docker compose -f docker-compose.yml down --timeout 30
)
if errorlevel 1 (
    echo [ERROR] docker compose down failed.
    goto :fail
)

:done
echo.
echo [OK] PocketPro:SBA has been stopped.
echo      Data is saved in uploads/ and chromadb_data/.
echo.
pause
exit /b 0

:fail
echo.
pause
exit /b 1
