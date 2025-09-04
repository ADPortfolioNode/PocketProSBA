@echo off
echo Running comprehensive test suite for PocketPro SBA...

REM Colors for output (Windows CMD)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "NC=[0m"

echo %YELLOW%Running backend tests...%NC%
cd backend

REM Check if virtual environment exists
if not exist "venv" (
    echo %RED%Virtual environment not found. Creating one...%NC%
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist "requirements.txt" (
    echo %RED%requirements.txt not found%NC%
    goto :error
)

pip install -r requirements.txt

REM Run pytest
python -m pytest tests/ -v --tb=short
if %errorlevel% neq 0 (
    echo %RED%Backend tests failed!%NC%
    goto :error
) else (
    echo %GREEN%Backend tests passed!%NC%
)

cd ..

echo %YELLOW%Running frontend tests...%NC%
cd frontend

REM Install dependencies if needed
if not exist "package.json" (
    echo %RED%package.json not found%NC%
    goto :error
)

npm install

REM Run Jest tests
npm test -- --watchAll=false --passWithNoTests
if %errorlevel% neq 0 (
    echo %RED%Frontend tests failed!%NC%
    goto :error
) else (
    echo %GREEN%Frontend tests passed!%NC%
)

cd ..

echo %YELLOW%Running integration tests...%NC%

REM Start backend server in background
cd backend
start /B python app.py
timeout /t 5 /nobreak > nul

REM Run integration tests
python -m pytest tests/test_integration.py -v --tb=short -m integration
set INTEGRATION_RESULT=%errorlevel%

REM Kill backend server (this is simplified - in production you'd want better process management)
taskkill /f /im python.exe > nul 2>&1

if %INTEGRATION_RESULT% neq 0 (
    echo %RED%Integration tests failed!%NC%
    goto :error
) else (
    echo %GREEN%Integration tests passed!%NC%
)

cd ..

echo.
echo %YELLOW%Test Summary:%NC%
echo Backend tests: %GREEN%PASSED%NC%
echo Frontend tests: %GREEN%PASSED%NC%
echo Integration tests: %GREEN%PASSED%NC%

echo.
echo %GREEN%All tests passed! 🎉%NC%
goto :end

:error
echo.
echo %RED%Some tests failed. Please review the output above.%NC%
exit /b 1

:end
exit /b 0
