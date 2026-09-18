@echo off
setlocal EnableExtensions
title PocketPro:SBA - Starting

cd /d "%~dp0"
if not exist "docker-compose.yml" if not exist "docker-compose.dev.yml" (
    echo [ERROR] docker-compose.yml not found.
    echo Please run this file from the PocketProSBA project folder.
    goto :fail
)

echo.
echo ============================================================
echo   PocketPro:SBA - Starting
echo ============================================================
echo.

if exist ".env" (
    echo [OK] Using your existing .env file.
) else (
    if exist ".env.template" (
        echo [SETUP] First-time install: creating .env from .env.template ...
        copy /Y ".env.template" ".env" >nul
    ) else if exist ".env.example" (
        echo [SETUP] First-time install: creating .env from .env.example ...
        copy /Y ".env.example" ".env" >nul
    ) else (
        echo [ERROR] Missing .env.template / .env.example. Cannot create .env.
        goto :fail
    )
    if errorlevel 1 (
        echo [ERROR] Could not create .env
        goto :fail
    )
    echo.
    echo  A new .env file was created. Set GEMINI_API_KEY before chat will work.
    echo.
)

if exist "backend\.env.example" if not exist "backend\.env" (
    echo [SETUP] Creating backend\.env from backend\.env.example ...
    copy /Y "backend\.env.example" "backend\.env" >nul
)

echo [START] Docker check and PocketPro:SBA stack startup via PowerShell ...
if not exist "%~dp0start-windows.ps1" (
    echo [ERROR] Missing start-windows.ps1 in %~dp0
    goto :fail
)
where powershell >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PowerShell is not on your PATH.
    goto :fail
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-windows.ps1" -Build -OpenBrowser
if errorlevel 1 (
    echo.
    echo [ERROR] Startup did not complete successfully.
    echo Try: start Docker Desktop, wait until it is running, then retry.
    echo Or:  recover_stack.ps1
    goto :fail
)

echo.
echo ============================================================
echo   PocketPro:SBA is running.
echo   Open:  http://127.0.0.1:3000
echo   API:   http://127.0.0.1:5000/api/health
echo   Stop:  StopPocketProSBA.bat
echo ============================================================
echo.
pause
exit /b 0

:fail
echo.
pause
exit /b 1
