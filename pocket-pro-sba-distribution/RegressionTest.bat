@echo off
echo ========================================
echo PocketPro SBA - Distribution Regression Test
echo ========================================
echo.

set "TESTS_PASSED=0"
set "TESTS_FAILED=0"

call :test_file_structure
echo TESTS_FAILED after 1: %TESTS_FAILED%
call :test_docker_setup
echo TESTS_FAILED after 2: %TESTS_FAILED%
call :test_configuration
echo TESTS_FAILED after 3: %TESTS_FAILED%
call :test_backend_integrity
echo TESTS_FAILED after 4: %TESTS_FAILED%
call :test_frontend_integrity
echo TESTS_FAILED after 5: %TESTS_FAILED%
call :test_executables
echo TESTS_FAILED after 6: %TESTS_FAILED%
call :test_documentation
echo TESTS_FAILED after 7: %TESTS_FAILED%
call :test_cleanliness
echo TESTS_FAILED after 8: %TESTS_FAILED%

echo.
echo ========================================
echo Regression Test Summary
echo ========================================
echo Tests Passed: %TESTS_PASSED%
echo Tests Failed: %TESTS_FAILED%
echo.

if %TESTS_FAILED% equ 0 (
    echo ✅ ALL REGRESSION TESTS PASSED
    echo Distribution is ready for production deployment!
) else (
    echo ❌ SOME REGRESSION TESTS FAILED
    echo Please review the failures above before deployment.
)

echo.
pause
exit /b

:test_file_structure
echo [TEST 1] File Structure Validation
echo ----------------------------------------
set "test_passed=1"

if not exist docker-compose.yml (
    echo [FAIL] docker-compose.yml missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] docker-compose.yml exists
)

if not exist Dockerfile.production (
    echo [FAIL] Dockerfile.production missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Dockerfile.production exists
)

if not exist Dockerfile.frontend (
    echo [FAIL] Dockerfile.frontend missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Dockerfile.frontend exists
)

if not exist nginx.conf (
    echo [FAIL] nginx.conf missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] nginx.conf exists
)

if not exist wsgi.py (
    echo [FAIL] wsgi.py missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] wsgi.py exists
)

if not exist run.py (
    echo [FAIL] run.py missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] run.py exists
)

if %test_passed% equ 1 (
    set /a TESTS_PASSED+=1
    echo [PASS] File structure test passed
)
echo.
exit /b

:test_docker_setup
echo [TEST 2] Docker Setup Validation
echo ----------------------------------------
set "test_passed=1"

REM Check if docker-compose.yml has required services
findstr /C:"backend:" docker-compose.yml >nul
if %errorlevel% neq 0 (
    echo [FAIL] Backend service not defined in docker-compose.yml
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Backend service defined
)

findstr /C:"chromadb:" docker-compose.yml >nul
if %errorlevel% neq 0 (
    echo [FAIL] ChromaDB service not defined in docker-compose.yml
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] ChromaDB service defined
)

findstr /C:"frontend:" docker-compose.yml >nul
if %errorlevel% neq 0 (
    echo [FAIL] Frontend service not defined in docker-compose.yml
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Frontend service defined
)

REM Check port mappings
findstr /C:"5000:5000" docker-compose.yml >nul
if %errorlevel% neq 0 (
    echo [WARN] Backend port mapping may be non-standard
) else (
    echo [PASS] Backend port mapping correct
)

findstr /C:"3000:80" docker-compose.yml >nul
if %errorlevel% neq 0 (
    echo [WARN] Frontend port mapping may be non-standard
) else (
    echo [PASS] Frontend port mapping correct
)

findstr /C:"8000:8000" docker-compose.yml >nul
if %errorlevel% neq 0 (
    echo [WARN] ChromaDB port mapping may be non-standard
) else (
    echo [PASS] ChromaDB port mapping correct
)

if %test_passed% equ 1 (
    set /a TESTS_PASSED+=1
    echo [PASS] Docker setup test passed
)
echo.
exit /b

:test_configuration
echo [TEST 3] Configuration Files Validation
echo ----------------------------------------
set "test_passed=1"

if not exist .env.example (
    echo [FAIL] .env.example missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] .env.example exists
)

REM Check for required environment variables in .env.example
findstr /C:"GEMINI_API_KEY" .env.example >nul
if %errorlevel% neq 0 (
    echo [FAIL] GEMINI_API_KEY not in .env.example
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] GEMINI_API_KEY in .env.example
)

findstr /C:"SECRET_KEY" .env.example >nul
if %errorlevel% neq 0 (
    echo [FAIL] SECRET_KEY not in .env.example
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] SECRET_KEY in .env.example
)

findstr /C:"CHROMADB_HOST" .env.example >nul
if %errorlevel% neq 0 (
    echo [FAIL] CHROMADB_HOST not in .env.example
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] CHROMADB_HOST in .env.example
)

if not exist .dockerignore (
    echo [WARN] .dockerignore missing (recommended)
) else (
    echo [PASS] .dockerignore exists
)

if not exist .gitignore (
    echo [WARN] .gitignore missing (recommended)
) else (
    echo [PASS] .gitignore exists
)

if %test_passed% equ 1 (
    set /a TESTS_PASSED+=1
    echo [PASS] Configuration test passed
)
echo.
exit /b

:test_backend_integrity
echo [TEST 4] Backend Integrity Validation
echo ----------------------------------------
set "test_passed=1"

if not exist backend\app\__init__.py (
    echo [FAIL] backend/app/__init__.py missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Backend app module exists
)

if not exist backend\routes\__init__.py (
    echo [FAIL] backend/routes/__init__.py missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Backend routes module exists
)

if not exist backend\services\__init__.py (
    echo [FAIL] backend/services/__init__.py missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Backend services module exists
)

if not exist backend\assistants\__init__.py (
    echo [FAIL] backend/assistants/__init__.py missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Backend assistants module exists
)

if not exist backend\models\__init__.py (
    echo [FAIL] backend/models/__init__.py missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Backend models module exists
)

REM Check critical route files
if not exist backend\routes\api.py (
    echo [FAIL] backend/routes/api.py missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] API routes exist
)

if not exist backend\routes\chat.py (
    echo [FAIL] backend/routes/chat.py missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Chat routes exist
)

if not exist backend\routes\sba.py (
    echo [FAIL] backend/routes/sba.py missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] SBA routes exist
)

if not exist backend\routes\rag.py (
    echo [FAIL] backend/routes/rag.py missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] RAG routes exist
)

REM Check critical service files
if not exist backend\services\api_service.py (
    echo [FAIL] backend/services/api_service.py missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] API service exists
)

if not exist backend\services\chroma.py (
    echo [FAIL] backend/services/chroma.py missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Chroma service exists
)

if not exist backend\services\sba_rag_ingest.py (
    echo [FAIL] backend/services/sba_rag_ingest.py missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] SBA RAG ingest service exists
)

if not exist backend\requirements.txt (
    echo [FAIL] backend/requirements.txt missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Backend requirements.txt exists
)

if not exist backend\config.py (
    echo [FAIL] backend/config.py missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Backend config.py exists
)

if %test_passed% equ 1 (
    set /a TESTS_PASSED+=1
    echo [PASS] Backend integrity test passed
)
echo.
exit /b

:test_frontend_integrity
echo [TEST 5] Frontend Integrity Validation
echo ----------------------------------------
set "test_passed=1"

if not exist frontend\build (
    echo [FAIL] frontend/build directory missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Frontend build directory exists
)

if not exist frontend\build\index.html (
    echo [FAIL] frontend/build/index.html missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Frontend index.html exists
)

if not exist frontend\build\static (
    echo [FAIL] frontend/build/static directory missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Frontend static assets exist
)

if not exist frontend\public (
    echo [FAIL] frontend/public directory missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Frontend public directory exists
)

if not exist frontend\public\resources.html (
    echo [FAIL] frontend/public/resources.html missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Frontend resources.html exists
)

if not exist frontend\public\programs.html (
    echo [FAIL] frontend/public/programs.html missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Frontend programs.html exists
)

if not exist frontend\nginx.dev.conf (
    echo [FAIL] frontend/nginx.dev.conf missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Frontend nginx config exists
)

if %test_passed% equ 1 (
    set /a TESTS_PASSED+=1
    echo [PASS] Frontend integrity test passed
)
echo.
exit /b

:test_executables
echo [TEST 6] Executables Validation
echo ----------------------------------------
set "test_passed=1"

if not exist Start.bat (
    echo [FAIL] Start.bat missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Start.bat exists
)

if not exist Stop.bat (
    echo [FAIL] Stop.bat missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Stop.bat exists
)

if not exist Start.sh (
    echo [FAIL] Start.sh missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Start.sh exists
)

if not exist Stop.sh (
    echo [FAIL] Stop.sh missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Stop.sh exists
)

if not exist Start.command (
    echo [FAIL] Start.command missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Start.command exists
)

if not exist Stop.command (
    echo [FAIL] Stop.command missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Stop.command exists
)

if not exist Test.bat (
    echo [FAIL] Test.bat missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Test.bat exists
)

if not exist Test.sh (
    echo [FAIL] Test.sh missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Test.sh exists
)

if %test_passed% equ 1 (
    set /a TESTS_PASSED+=1
    echo [PASS] Executables test passed
)
echo.
exit /b

:test_documentation
echo [TEST 7] Documentation Validation
echo ----------------------------------------
set "test_passed=1"

if not exist README.md (
    echo [FAIL] README.md missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] README.md exists
)

REM Check README content
findstr /C:"Quick Start" README.md >nul
if %errorlevel% neq 0 (
    echo [WARN] README.md may be missing Quick Start section
) else (
    echo [PASS] README.md contains Quick Start
)

findstr /C:"Docker" README.md >nul
if %errorlevel% neq 0 (
    echo [WARN] README.md may be missing Docker instructions
) else (
    echo [PASS] README.md contains Docker instructions
)

findstr /C:"GEMINI_API_KEY" README.md >nul
if %errorlevel% neq 0 (
    echo [WARN] README.md may be missing API key instructions
) else (
    echo [PASS] README.md contains API key instructions
)

if not exist LICENSE.txt (
    echo [FAIL] LICENSE.txt missing
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] LICENSE.txt exists
)

findstr /C:"MIT" LICENSE.txt >nul
if %errorlevel% neq 0 (
    echo [WARN] LICENSE.txt may not be MIT license
) else (
    echo [PASS] LICENSE.txt contains MIT license
)

if %test_passed% equ 1 (
    set /a TESTS_PASSED+=1
    echo [PASS] Documentation test passed
)
echo.
exit /b

:test_cleanliness
echo [TEST 8] Distribution Cleanliness Validation
echo ----------------------------------------
set "test_passed=1"

REM Check for test files (should not exist)
dir /s /b backend\test_*.py >nul 2>&1
if %errorlevel% equ 0 (
    echo [FAIL] Test files found in backend (should be removed)
    dir /s /b backend\test_*.py
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] No test files in backend
)
echo AFTER Check 1: TESTS_FAILED=%TESTS_FAILED%, test_passed=%test_passed%

REM Check for diagnostic files
if exist backend\diagnostic.py (
    echo [FAIL] diagnostic.py found (should be removed)
    set "test_passed=0"
    set /a TESTS_FAILED+=1
    goto :skip_diag_pass
)
echo [PASS] No diagnostic files
:skip_diag_pass
echo AFTER Check 2: TESTS_FAILED=%TESTS_FAILED%, test_passed=%test_passed%

REM Check for temporary files (excluding requirements.txt)
dir /b backend\*.txt 2>nul | findstr /i /v "requirements.txt" >nul
if %errorlevel% equ 0 (
    echo [FAIL] Temporary .txt files found in backend
    dir /b backend\*.txt | findstr /i /v "requirements.txt"
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] No temporary .txt files
)
echo AFTER Check 3: TESTS_FAILED=%TESTS_FAILED%, test_passed=%test_passed%

REM Check for backup files
dir /s /b backend\*.bak 2>nul | findstr /r "." >nul
if %errorlevel% equ 0 (
    echo [FAIL] Backup files found in backend
    dir /s /b backend\*.bak
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] No backup files
)
echo AFTER Check 4: TESTS_FAILED=%TESTS_FAILED%, test_passed=%test_passed%

REM Check for __pycache__ directories
if exist backend\__pycache__ (
    echo [WARN] __pycache__ directories found (should be removed)
    dir /s /b backend\__pycache__
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] No __pycache__ directories
)
echo AFTER Check 5: TESTS_FAILED=%TESTS_FAILED%, test_passed=%test_passed%

REM Check data directories (should not exist initially)
if exist uploads (
    echo [WARN] uploads directory exists (should be created at runtime)
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] uploads directory does not exist (will be created)
)
echo AFTER Check 6: TESTS_FAILED=%TESTS_FAILED%, test_passed=%test_passed%

if exist chromadb_data (
    echo [WARN] chromadb_data directory exists (should be created at runtime)
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] chromadb_data directory does not exist (will be created)
)
echo AFTER Check 7: TESTS_FAILED=%TESTS_FAILED%, test_passed=%test_passed%

if exist logs (
    echo [WARN] logs directory exists (should be created at runtime)
    set "test_passed=0"
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] logs directory does not exist (will be created)
)
echo AFTER Check 8: TESTS_FAILED=%TESTS_FAILED%, test_passed=%test_passed%

if %test_passed% equ 1 (
    set /a TESTS_PASSED+=1
    echo [PASS] Cleanliness test passed
)
echo.
exit /b
