@echo off
rem Run Flask application using the built-in development server
rem This is for Windows development only - Render.com will use Gunicorn

echo Starting Flask application for Windows development...

rem Set environment variables
set PORT=5000
set FLASK_ENV=development
set FLASK_APP=minimal_app.py
set PYTHONUNBUFFERED=1

echo Binding to 0.0.0.0:%PORT%
echo Note: Using Flask's built-in server instead of Gunicorn for Windows compatibility

rem Run the Windows-compatible server
python run_windows.py

pause
