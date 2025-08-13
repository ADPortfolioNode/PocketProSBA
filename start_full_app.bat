@echo off
echo Starting PocketPro SBA Full Application with RAG Operations...
echo.

:: Kill any existing processes on our ports
echo Cleaning up existing processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do taskkill /F /PID %%a 2>nul
timeout /t 2 /nobreak > nul

:: Start backend API
echo Starting Backend API...
start cmd /k "python app_simple.py"

:: Wait for backend to initialize
echo Waiting for backend to initialize...
timeout /t 5 /nobreak > nul

:: Start frontend
echo Starting Frontend...
start cmd /k "cd frontend && npm start"

:: Wait for frontend to initialize
echo Waiting for frontend to initialize...
timeout /t 10 /nobreak > nul

:: Launch browser for testing
echo Launching browser for testing...
start http://localhost:3000

echo.
echo ==========================================
echo Application Started Successfully!
echo Backend API: http://localhost:5000
echo Frontend: http://localhost:3000
echo ==========================================
echo.
echo Press any key to open test interface...
pause > nul

:: Open test interface
start http://localhost:3000
