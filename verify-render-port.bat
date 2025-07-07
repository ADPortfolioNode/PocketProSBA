@echo off
rem Verify Render.com port binding
echo Running Render.com port verification...

rem Set the PORT environment variable if not already set
if "%PORT%"=="" set PORT=5000

rem Run the verification script
python verify_render_port.py

echo.
echo Verification complete.
pause
