@echo off
REM Development startup script for PocketPro:SBA Edition (Windows)

echo === PocketPro:SBA Edition Development Setup ===

REM Check if .env file exists
if not exist .env (
    echo Creating .env file from template...
    copy .env.template .env
    echo Please edit .env file with your API keys and configuration
    echo Required: GEMINI_API_KEY
    exit /b 1
)

REM Create necessary directories
if not exist uploads mkdir uploads
if not exist chromadb_data mkdir chromadb_data
if not exist logs mkdir logs

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

REM Install frontend dependencies
echo Installing frontend dependencies...
cd frontend
npm install
cd ..

echo === Starting Development Servers ===

REM Start backend server
echo Starting backend server...
start "PocketPro Backend" python run.py

REM Wait for backend to start
timeout /t 5 /nobreak

REM Start frontend development server
echo Starting frontend development server...
cd frontend
start "PocketPro Frontend" npm start
cd ..

echo === Servers Started ===
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
echo Check the separate terminal windows for server logs
pause
