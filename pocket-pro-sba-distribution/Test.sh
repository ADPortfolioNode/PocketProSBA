#!/bin/bash

echo "========================================"
echo "PocketPro SBA - Product Test"
echo "========================================"
echo ""

echo "Testing Distribution Structure..."
echo ""

# Check essential files exist
echo "[1/8] Checking essential files..."
if [ -f docker-compose.yml ]; then
    echo "[OK] docker-compose.yml exists"
else
    echo "[FAIL] docker-compose.yml missing"
    exit 1
fi

if [ -f Dockerfile.production ]; then
    echo "[OK] Dockerfile.production exists"
else
    echo "[FAIL] Dockerfile.production missing"
    exit 1
fi

if [ -f Dockerfile.frontend ]; then
    echo "[OK] Dockerfile.frontend exists"
else
    echo "[FAIL] Dockerfile.frontend missing"
    exit 1
fi

if [ -f .env.example ]; then
    echo "[OK] .env.example exists"
else
    echo "[FAIL] .env.example missing"
    exit 1
fi

if [ -f README.md ]; then
    echo "[OK] README.md exists"
else
    echo "[FAIL] README.md missing"
    exit 1
fi

echo ""
echo "[2/8] Checking executables..."
if [ -f Start.sh ]; then
    echo "[OK] Start.sh exists"
else
    echo "[FAIL] Start.sh missing"
    exit 1
fi

if [ -f Stop.sh ]; then
    echo "[OK] Stop.sh exists"
else
    echo "[FAIL] Stop.sh missing"
    exit 1
fi

echo ""
echo "[3/8] Checking backend structure..."
if [ -f backend/app/__init__.py ]; then
    echo "[OK] backend/app/__init__.py exists"
else
    echo "[FAIL] backend structure incomplete"
    exit 1
fi

if [ -f backend/routes/api.py ]; then
    echo "[OK] backend/routes/api.py exists"
else
    echo "[FAIL] backend routes incomplete"
    exit 1
fi

if [ -f backend/services/api_service.py ]; then
    echo "[OK] backend/services/api_service.py exists"
else
    echo "[FAIL] backend services incomplete"
    exit 1
fi

echo ""
echo "[4/8] Checking frontend structure..."
if [ -f frontend/build/index.html ]; then
    echo "[OK] frontend/build/index.html exists"
else
    echo "[FAIL] frontend build incomplete"
    exit 1
fi

if [ -f frontend/public/resources.html ]; then
    echo "[OK] frontend/public/resources.html exists"
else
    echo "[FAIL] frontend public incomplete"
    exit 1
fi

echo ""
echo "[5/8] Checking Docker availability..."
if docker info > /dev/null 2>&1; then
    echo "[OK] Docker is running"
else
    echo "[WARN] Docker is not running - will be required for startup"
fi

echo ""
echo "[6/8] Checking for test files (should not exist)..."
if ls backend/test_*.py 1> /dev/null 2>&1; then
    echo "[FAIL] Test files found in backend - should be removed"
    ls backend/test_*.py
    exit 1
else
    echo "[OK] No test files in backend"
fi

if [ -f backend/diagnostic.py ]; then
    echo "[FAIL] Diagnostic files found - should be removed"
    exit 1
else
    echo "[OK] No diagnostic files"
fi

echo ""
echo "[7/8] Checking for temporary files (should not exist)..."
if ls backend/*.txt 1> /dev/null 2>&1; then
    echo "[WARN] Temporary .txt files found in backend"
    ls backend/*.txt
fi

if ls backend/*.bak 1> /dev/null 2>&1; then
    echo "[WARN] Backup files found in backend"
    ls backend/*.bak
fi

echo ""
echo "[8/8] Checking data directories (will be created at runtime)..."
if [ ! -d uploads ]; then
    echo "[OK] uploads directory does not exist (will be created)"
fi

if [ ! -d chromadb_data ]; then
    echo "[OK] chromadb_data directory does not exist (will be created)"
fi

if [ ! -d logs ]; then
    echo "[OK] logs directory does not exist (will be created)"
fi

echo ""
echo "========================================"
echo "Product Test PASSED"
echo "========================================"
echo ""
echo "Distribution is ready for deployment!"
echo ""
echo "Next steps:"
echo "1. Run ./Start.sh to test startup"
echo "2. Verify .env configuration"
echo "3. Test application functionality"
echo ""
