@echo off
setlocal EnableExtensions
title PocketProSBA - Starting

cd /d "%~dp0"
if not exist "docker-compose.yml" if not exist "docker-compose.dev.yml" (
    echo [ERROR] docker-compose.yml not found.
    echo Please run this file from the project folder.
    goto :fail
)

echo.
echo ============================================================
echo   PocketProSBA - Starting
echo ============================================================
echo.

if exist ".env" (
    echo [OK] Using your existing .env file ^(unchanged^).
) else (
    if exist ".env.template" (
        echo [SETUP] First-time install: creating .env from .env.template ...
        copy /Y ".env.template" ".env" >nul
    ) else if exist ".env.example" (
        copy /Y ".env.example" ".env" >nul
    ) else (
        echo [ERROR] .env template missing. Cannot create .env.
        goto :fail
    )
    if errorlevel 1 (
        echo [ERROR] Could not create .env
        goto :fail
    )
    echo.
    echo  A new .env file was created. Set GEMINI_API_KEY for SBA chat.
    echo  Opening .env in Notepad - save and close when done, then press any key.
    notepad ".env"
    pause >nul
)

if exist "backend\.env.example" if not exist "backend\.env" (
    copy /Y "backend\.env.example" "backend\.env" >nul
)

:env_ready

echo.
echo [START] Docker check and PocketProSBA stack startup via PowerShell ...
echo         ^(first dev build may take 10-20 minutes^)
echo.

if not exist "%~dp0start-windows.ps1" (
    echo [ERROR] Missing start-windows.ps1 in %~dp0
    goto :fail
)
where powershell >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PowerShell is not on your PATH.
    goto :fail
)
set "START_ARGS=-Build -OpenBrowser"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-windows.ps1" %START_ARGS%
if errorlevel 1 (
    echo.
    echo [ERROR] Startup did not complete successfully.
    echo Try: start Docker Desktop, wait until it is running,
    echo then run this script again.
    goto :fail
)

echo.
echo ============================================================
echo   PocketProSBA is running. Your browser should open automatically.
echo   If not, open:  http://127.0.0.1:3000
echo   To stop:      StopPocketProSBA.bat
echo ============================================================
echo.
pause
exit /b 0

:fail
echo.
pause
exit /b 1
