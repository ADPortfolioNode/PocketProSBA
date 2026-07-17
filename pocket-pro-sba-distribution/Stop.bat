@echo off
echo ========================================
echo PocketPro SBA - Stopping Application
echo ========================================
echo.

REM Stop containers
echo Stopping Docker containers...
docker compose down

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to stop containers
    pause
    exit /b 1
)

echo.
echo ========================================
echo Application Stopped Successfully!
echo ========================================
echo.
echo All containers have been stopped and removed.
echo Your data in uploads/, chromadb_data/, and logs/ is preserved.
echo.
pause
