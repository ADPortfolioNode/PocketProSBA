#!/bin/bash
# A1Starter1A.sh
# Automated deployment verification and fix workflow for PocketPro:SBA (Bash version)

DOMAIN="localhost"
PROTOCOL="http"
BASEURL="http://localhost:10000"

if [ "$1" != "" ]; then
  DOMAIN="$1"
fi
if [ "$2" != "" ]; then
  PROTOCOL="$2"
fi
if [ "$DOMAIN" != "localhost" ]; then
  BASEURL="$PROTOCOL://$DOMAIN"
fi

echo "===== PocketPro:SBA Automated Deployment Workflow ====="
echo "Target: $BASEURL"
echo ""
read -p "Press Enter to begin the automated deployment verification and fix workflow..."

# Step 1: Run verification
echo "[1/4] Running deployment verification..."
if [ -f verify-deployment.ps1 ]; then
  pwsh ./verify-deployment.ps1 -domain "$DOMAIN" -protocol "$PROTOCOL"
fi

# Step 2: Run Python verification (cross-platform)
echo "[2/4] Running Python deployment checks..."
if [ -f verify_render_deployment.py ]; then
  python3 verify_render_deployment.py "$BASEURL"
fi

# Step 3: Run final checks and fixes recursively
echo "[3/4] Running final checks and fixes..."
fixScripts=(
  "final_deployment_check.py"
  "final_port_fix_check.py"
  "final_rag_test.py"
  "fix-all.ps1"
  "fix-docker-build.ps1"
  "fix-frontend.ps1"
  "fix-network-config.ps1"
  "fix-chromadb.py"
  "fix-frontend-container.ps1"
  "fix-app-eslint.ps1"
  "fix-app-no-bootstrap.ps1"
  "fix-eslint-line66.ps1"
  "fix-react-bootstrap.ps1"
  "fix-startup.py"
  "fix_frontend_issues.py"
)
for script in "${fixScripts[@]}"; do
  if [ -f "$script" ]; then
    echo "Running $script..."
    case "$script" in
      *.ps1)
        pwsh ./$script
        ;;
      *.py)
        python3 $script
        ;;
    esac
  fi
done


# Step 4: Report summary
echo "[4/4] Workflow complete. See above for results."
echo "===== PocketPro:SBA Automated Report ====="
echo "1. All verification and fix scripts executed recursively."
echo "2. Review any errors or warnings above."
echo "3. Test document upload and RAG functionality manually if needed."
echo "4. Monitor logs with: docker-compose logs -f"
echo "\nWorkflow finished!"

# Start Flask server (optimal for Render)
if [ -f app.py ]; then
  echo "Starting Flask server..."
  export FLASK_APP=app.py
  export FLASK_ENV=production
  export PORT=5000
  python3 -m flask run --host=0.0.0.0 --port=5000 &
fi

# Start React frontend (optimal for Render)
if [ -f frontend/package.json ]; then
  echo "Starting React frontend..."
  cd frontend
  npm install
  npm run build
  npm start &
  cd ..
fi
