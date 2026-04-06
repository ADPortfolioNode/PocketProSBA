@echo off
echo Checking React setup in frontend folder...
cd /d "%~dp0frontend"
npm list react
echo.
echo If no errors appeared, the frontend setup looks good! Ready to run with npm start
