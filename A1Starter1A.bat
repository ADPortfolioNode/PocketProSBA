@echo off
REM A1Starter1A.bat
REM Automated deployment verification and fix workflow for PocketPro:SBA (Batch version)

set DOMAIN=localhost
set PROTOCOL=http
set BASEURL=http://localhost:10000

if not "%1"=="" set DOMAIN=%1
if not "%2"=="" set PROTOCOL=%2
if not "%DOMAIN%"=="localhost" set BASEURL=%PROTOCOL%://%DOMAIN%

echo ===== PocketPro:SBA Automated Deployment Workflow =====
echo Target: %BASEURL%
echo.
pause

REM Step 1: Run verification
if exist verify-deployment.ps1 pwsh ./verify-deployment.ps1 -domain "%DOMAIN%" -protocol "%PROTOCOL%"

REM Step 2: Run Python verification
if exist verify_render_deployment.py python verify_render_deployment.py "%BASEURL%"

REM Step 3: Run final checks and fixes recursively

REM Step 3: Run final checks and fixes recursively
set fixScripts=final_deployment_check.py final_port_fix_check.py final_rag_test.py fix-all.ps1 fix-docker-build.ps1 fix-frontend.ps1 fix-network-config.ps1 fix-chromadb.py fix-frontend-container.ps1 fix-app-eslint.ps1 fix-app-no-bootstrap.ps1 fix-eslint-line66.ps1 fix-react-bootstrap.ps1 fix-startup.py fix_frontend_issues.py
for %%S in (%fixScripts%) do (
    if exist %%S (
        echo Running %%S...
        echo %%S | findstr /E ".ps1" >nul
        if not errorlevel 1 (
            pwsh ./%%S
        ) else (
            python %%S
        )
    )
)

REM Step 4: Report summary
echo [4/4] Workflow complete. See above for results.
echo ===== PocketPro:SBA Automated Report =====
echo 1. All verification and fix scripts executed recursively.
echo 2. Review any errors or warnings above.
echo 3. Test document upload and RAG functionality manually if needed.
echo 4. Monitor logs with: docker-compose logs -f
echo.
echo Workflow finished!

REM --- Server Startup & Encoding Check ---
echo "[A1] Checking for running Flask and React servers..."
FLASK_PID=$(pgrep -f "flask run")
REACT_PID=$(pgrep -f "npm start")
if [ ! -z "$FLASK_PID" ]; then
  echo "Stopping existing Flask server (PID: $FLASK_PID)..."
  kill $FLASK_PID
fi
if [ ! -z "$REACT_PID" ]; then
  echo "Stopping existing React server (PID: $REACT_PID)..."
  kill $REACT_PID
fi
echo "Starting fresh Flask and React servers for testing..."
export FLASK_APP=app.py
export FLASK_ENV=production
export PORT=5000
nohup python3 -m flask run --host=0.0.0.0 --port=5000 > flask.log 2>&1 &
if [ -f frontend/package.json ]; then
  cd frontend
  nohup npm start > react.log 2>&1 &
  cd ..
fi

REM --- Encoding Check Helper ---
echo "[A1] Checking Python scripts for encoding in file operations..."
ENCODING_WARN=false
for pyfile in *.py; do
  if grep -q "open(" "$pyfile"; then
    if ! grep -q "encoding=" "$pyfile"; then
      echo "[WARN] $pyfile: open() without encoding specified."
      ENCODING_WARN=true
    fi
  fi
done
if [ "$ENCODING_WARN" = true ]; then
  echo "[A1] Please update above Python scripts to use encoding='utf-8' for file operations."
else
  echo "[A1] All Python file operations use encoding."
fi

REM Start Flask backend
start "Flask Backend" python app_full.py

REM Start React frontend
cd frontend
start "React Frontend" npm start

REM To stop all Python processes (Flask):
REM taskkill /IM python.exe /F

REM To stop all Node processes (React):
REM taskkill /IM node.exe /F
