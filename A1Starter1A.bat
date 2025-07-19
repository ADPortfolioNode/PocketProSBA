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

REM Start Flask server (optimal for Render)
if exist app.py (
    echo Starting Flask server...
    set FLASK_APP=app.py
    set FLASK_ENV=production
    set PORT=5000
    python -m flask run --host=0.0.0.0 --port=5000
)

REM Start React frontend (optimal for Render)
if exist frontend\package.json (
    echo Starting React frontend...
    cd frontend
    npm install
    npm run build
    npm start
    cd ..
)
