@echo off
echo ========================================
echo PocketPro SBA - Product Test
echo ========================================
echo.

echo Testing Distribution Structure...
echo.

REM Check essential files exist
echo [1/8] Checking essential files...
if exist docker-compose.yml (
    echo [OK] docker-compose.yml exists
) else (
    echo [FAIL] docker-compose.yml missing
    goto :error
)

if exist Dockerfile.production (
    echo [OK] Dockerfile.production exists
) else (
    echo [FAIL] Dockerfile.production missing
    goto :error
)

if exist Dockerfile.frontend (
    echo [OK] Dockerfile.frontend exists
) else (
    echo [FAIL] Dockerfile.frontend missing
    goto :error
)

if exist .env.example (
    echo [OK] .env.example exists
) else (
    echo [FAIL] .env.example missing
    goto :error
)

if exist README.md (
    echo [OK] README.md exists
) else (
    echo [FAIL] README.md missing
    goto :error
)

echo.
echo [2/8] Checking executables...
if exist Start.bat (
    echo [OK] Start.bat exists
) else (
    echo [FAIL] Start.bat missing
    goto :error
)

if exist Stop.bat (
    echo [OK] Stop.bat exists
) else (
    echo [FAIL] Stop.bat missing
    goto :error
)

echo.
echo [3/8] Checking backend structure...
if exist backend\app\__init__.py (
    echo [OK] backend/app/__init__.py exists
) else (
    echo [FAIL] backend structure incomplete
    goto :error
)

if exist backend\routes\api.py (
    echo [OK] backend/routes/api.py exists
) else (
    echo [FAIL] backend routes incomplete
    goto :error
)

if exist backend\services\api_service.py (
    echo [OK] backend/services/api_service.py exists
) else (
    echo [FAIL] backend services incomplete
    goto :error
)

echo.
echo [4/8] Checking frontend structure...
if exist frontend\build\index.html (
    echo [OK] frontend/build/index.html exists
) else (
    echo [FAIL] frontend build incomplete
    goto :error
)

if exist frontend\public\resources.html (
    echo [OK] frontend/public/resources.html exists
) else (
    echo [FAIL] frontend public incomplete
    goto :error
)

echo.
echo [5/8] Checking Docker availability...
docker info >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Docker is running
) else (
    echo [WARN] Docker is not running - will be required for startup
)

echo.
echo [6/8] Checking for test files (should not exist)...
if exist backend\test_*.py (
    echo [FAIL] Test files found in backend - should be removed
    goto :error
) else (
    echo [OK] No test files in backend
)

if exist backend\diagnostic.py (
    echo [FAIL] Diagnostic files found - should be removed
    goto :error
) else (
    echo [OK] No diagnostic files
)

echo.
echo [7/8] Checking for temporary files (should not exist)...
dir /b backend\*.txt 2>nul | findstr /i /v "requirements.txt" >nul
if %errorlevel% equ 0 (
    echo [WARN] Non-requirements .txt files found in backend
    dir /b backend\*.txt | findstr /i /v "requirements.txt"
) else (
    if exist backend\requirements.txt (
        echo [OK] Only requirements.txt found ^(legitimate^)
    ) else (
        echo [OK] No .txt files found
    )
)

if exist backend\*.bak (
    echo [WARN] Backup files found in backend
    dir backend\*.bak
)

echo.
echo [8/8] Checking data directories (will be created at runtime)...
if not exist uploads (
    echo [OK] uploads directory does not exist (will be created)
)

if not exist chromadb_data (
    echo [OK] chromadb_data directory does not exist (will be created)
)

if not exist logs (
    echo [OK] logs directory does not exist (will be created)
)

echo.
echo ========================================
echo Product Test PASSED
echo ========================================
echo.
echo Distribution is ready for deployment!
echo.
echo Next steps:
echo 1. Double-click Start.bat to test startup
echo 2. Verify .env configuration
echo 3. Test application functionality
echo.
pause
exit /b 0

:error
echo.
echo ========================================
echo Product Test FAILED
echo ========================================
echo.
echo Please fix the issues above before deployment.
echo.
pause
exit /b 1
