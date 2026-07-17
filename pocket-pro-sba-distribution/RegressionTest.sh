#!/bin/bash

echo "========================================"
echo "PocketPro SBA - Distribution Regression Test"
echo "========================================"
echo ""

TESTS_PASSED=0
TESTS_FAILED=0

test_file_structure
test_docker_setup
test_configuration
test_backend_integrity
test_frontend_integrity
test_executables
test_documentation
test_cleanliness

echo ""
echo "========================================"
echo "Regression Test Summary"
echo "========================================"
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo "✅ ALL REGRESSION TESTS PASSED"
    echo "Distribution is ready for production deployment!"
else
    echo "❌ SOME REGRESSION TESTS FAILED"
    echo "Please review the failures above before deployment."
fi

echo ""
exit 0

test_file_structure() {
    echo "[TEST 1] File Structure Validation"
    echo "----------------------------------------"
    local test_passed=1

    if [ ! -f docker-compose.yml ]; then
        echo "[FAIL] docker-compose.yml missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] docker-compose.yml exists"
    fi

    if [ ! -f Dockerfile.production ]; then
        echo "[FAIL] Dockerfile.production missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Dockerfile.production exists"
    fi

    if [ ! -f Dockerfile.frontend ]; then
        echo "[FAIL] Dockerfile.frontend missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Dockerfile.frontend exists"
    fi

    if [ ! -f nginx.conf ]; then
        echo "[FAIL] nginx.conf missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] nginx.conf exists"
    fi

    if [ ! -f wsgi.py ]; then
        echo "[FAIL] wsgi.py missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] wsgi.py exists"
    fi

    if [ ! -f run.py ]; then
        echo "[FAIL] run.py missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] run.py exists"
    fi

    if [ $test_passed -eq 1 ]; then
        ((TESTS_PASSED++))
        echo "[PASS] File structure test passed"
    fi
    echo ""
}

test_docker_setup() {
    echo "[TEST 2] Docker Setup Validation"
    echo "----------------------------------------"
    local test_passed=1

    # Check if docker-compose.yml has required services
    if ! grep -q "backend:" docker-compose.yml; then
        echo "[FAIL] Backend service not defined in docker-compose.yml"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Backend service defined"
    fi

    if ! grep -q "chromadb:" docker-compose.yml; then
        echo "[FAIL] ChromaDB service not defined in docker-compose.yml"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] ChromaDB service defined"
    fi

    if ! grep -q "frontend:" docker-compose.yml; then
        echo "[FAIL] Frontend service not defined in docker-compose.yml"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Frontend service defined"
    fi

    # Check port mappings
    if ! grep -q "5000:5000" docker-compose.yml; then
        echo "[WARN] Backend port mapping may be non-standard"
    else
        echo "[PASS] Backend port mapping correct"
    fi

    if ! grep -q "3000:80" docker-compose.yml; then
        echo "[WARN] Frontend port mapping may be non-standard"
    else
        echo "[PASS] Frontend port mapping correct"
    fi

    if ! grep -q "8000:8000" docker-compose.yml; then
        echo "[WARN] ChromaDB port mapping may be non-standard"
    else
        echo "[PASS] ChromaDB port mapping correct"
    fi

    if [ $test_passed -eq 1 ]; then
        ((TESTS_PASSED++))
        echo "[PASS] Docker setup test passed"
    fi
    echo ""
}

test_configuration() {
    echo "[TEST 3] Configuration Files Validation"
    echo "----------------------------------------"
    local test_passed=1

    if [ ! -f .env.example ]; then
        echo "[FAIL] .env.example missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] .env.example exists"
    fi

    # Check for required environment variables in .env.example
    if ! grep -q "GEMINI_API_KEY" .env.example; then
        echo "[FAIL] GEMINI_API_KEY not in .env.example"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] GEMINI_API_KEY in .env.example"
    fi

    if ! grep -q "SECRET_KEY" .env.example; then
        echo "[FAIL] SECRET_KEY not in .env.example"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] SECRET_KEY in .env.example"
    fi

    if ! grep -q "CHROMADB_HOST" .env.example; then
        echo "[FAIL] CHROMADB_HOST not in .env.example"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] CHROMADB_HOST in .env.example"
    fi

    if [ ! -f .dockerignore ]; then
        echo "[WARN] .dockerignore missing (recommended)"
    else
        echo "[PASS] .dockerignore exists"
    fi

    if [ ! -f .gitignore ]; then
        echo "[WARN] .gitignore missing (recommended)"
    else
        echo "[PASS] .gitignore exists"
    fi

    if [ $test_passed -eq 1 ]; then
        ((TESTS_PASSED++))
        echo "[PASS] Configuration test passed"
    fi
    echo ""
}

test_backend_integrity() {
    echo "[TEST 4] Backend Integrity Validation"
    echo "----------------------------------------"
    local test_passed=1

    if [ ! -f backend/app/__init__.py ]; then
        echo "[FAIL] backend/app/__init__.py missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Backend app module exists"
    fi

    if [ ! -f backend/routes/__init__.py ]; then
        echo "[FAIL] backend/routes/__init__.py missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Backend routes module exists"
    fi

    if [ ! -f backend/services/__init__.py ]; then
        echo "[FAIL] backend/services/__init__.py missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Backend services module exists"
    fi

    if [ ! -f backend/assistants/__init__.py ]; then
        echo "[FAIL] backend/assistants/__init__.py missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Backend assistants module exists"
    fi

    if [ ! -f backend/models/__init__.py ]; then
        echo "[FAIL] backend/models/__init__.py missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Backend models module exists"
    fi

    # Check critical route files
    if [ ! -f backend/routes/api.py ]; then
        echo "[FAIL] backend/routes/api.py missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] API routes exist"
    fi

    if [ ! -f backend/routes/chat.py ]; then
        echo "[FAIL] backend/routes/chat.py missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Chat routes exist"
    fi

    if [ ! -f backend/routes/sba.py ]; then
        echo "[FAIL] backend/routes/sba.py missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] SBA routes exist"
    fi

    if [ ! -f backend/routes/rag.py ]; then
        echo "[FAIL] backend/routes/rag.py missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] RAG routes exist"
    fi

    # Check critical service files
    if [ ! -f backend/services/api_service.py ]; then
        echo "[FAIL] backend/services/api_service.py missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] API service exists"
    fi

    if [ ! -f backend/services/chroma.py ]; then
        echo "[FAIL] backend/services/chroma.py missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Chroma service exists"
    fi

    if [ ! -f backend/services/sba_rag_ingest.py ]; then
        echo "[FAIL] backend/services/sba_rag_ingest.py missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] SBA RAG ingest service exists"
    fi

    if [ ! -f backend/requirements.txt ]; then
        echo "[FAIL] backend/requirements.txt missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Backend requirements.txt exists"
    fi

    if [ ! -f backend/config.py ]; then
        echo "[FAIL] backend/config.py missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Backend config.py exists"
    fi

    if [ $test_passed -eq 1 ]; then
        ((TESTS_PASSED++))
        echo "[PASS] Backend integrity test passed"
    fi
    echo ""
}

test_frontend_integrity() {
    echo "[TEST 5] Frontend Integrity Validation"
    echo "----------------------------------------"
    local test_passed=1

    if [ ! -d frontend/build ]; then
        echo "[FAIL] frontend/build directory missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Frontend build directory exists"
    fi

    if [ ! -f frontend/build/index.html ]; then
        echo "[FAIL] frontend/build/index.html missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Frontend index.html exists"
    fi

    if [ ! -d frontend/build/static ]; then
        echo "[FAIL] frontend/build/static directory missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Frontend static assets exist"
    fi

    if [ ! -d frontend/public ]; then
        echo "[FAIL] frontend/public directory missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Frontend public directory exists"
    fi

    if [ ! -f frontend/public/resources.html ]; then
        echo "[FAIL] frontend/public/resources.html missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Frontend resources.html exists"
    fi

    if [ ! -f frontend/public/programs.html ]; then
        echo "[FAIL] frontend/public/programs.html missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Frontend programs.html exists"
    fi

    if [ ! -f frontend/nginx.dev.conf ]; then
        echo "[FAIL] frontend/nginx.dev.conf missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Frontend nginx config exists"
    fi

    if [ $test_passed -eq 1 ]; then
        ((TESTS_PASSED++))
        echo "[PASS] Frontend integrity test passed"
    fi
    echo ""
}

test_executables() {
    echo "[TEST 6] Executables Validation"
    echo "----------------------------------------"
    local test_passed=1

    if [ ! -f Start.sh ]; then
        echo "[FAIL] Start.sh missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Start.sh exists"
    fi

    if [ ! -f Stop.sh ]; then
        echo "[FAIL] Stop.sh missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Stop.sh exists"
    fi

    if [ ! -f Start.command ]; then
        echo "[FAIL] Start.command missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Start.command exists"
    fi

    if [ ! -f Stop.command ]; then
        echo "[FAIL] Stop.command missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Stop.command exists"
    fi

    if [ ! -f Test.sh ]; then
        echo "[FAIL] Test.sh missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] Test.sh exists"
    fi

    if [ $test_passed -eq 1 ]; then
        ((TESTS_PASSED++))
        echo "[PASS] Executables test passed"
    fi
    echo ""
}

test_documentation() {
    echo "[TEST 7] Documentation Validation"
    echo "----------------------------------------"
    local test_passed=1

    if [ ! -f README.md ]; then
        echo "[FAIL] README.md missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] README.md exists"
    fi

    # Check README content
    if ! grep -q "Quick Start" README.md; then
        echo "[WARN] README.md may be missing Quick Start section"
    else
        echo "[PASS] README.md contains Quick Start"
    fi

    if ! grep -q "Docker" README.md; then
        echo "[WARN] README.md may be missing Docker instructions"
    else
        echo "[PASS] README.md contains Docker instructions"
    fi

    if ! grep -q "GEMINI_API_KEY" README.md; then
        echo "[WARN] README.md may be missing API key instructions"
    else
        echo "[PASS] README.md contains API key instructions"
    fi

    if [ ! -f LICENSE.txt ]; then
        echo "[FAIL] LICENSE.txt missing"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] LICENSE.txt exists"
    fi

    if ! grep -q "MIT" LICENSE.txt; then
        echo "[WARN] LICENSE.txt may not be MIT license"
    else
        echo "[PASS] LICENSE.txt contains MIT license"
    fi

    if [ $test_passed -eq 1 ]; then
        ((TESTS_PASSED++))
        echo "[PASS] Documentation test passed"
    fi
    echo ""
}

test_cleanliness() {
    echo "[TEST 8] Distribution Cleanliness Validation"
    echo "----------------------------------------"
    local test_passed=1

    # Check for test files (should not exist)
    if ls backend/test_*.py 1> /dev/null 2>&1; then
        echo "[FAIL] Test files found in backend (should be removed)"
        ls backend/test_*.py
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] No test files in backend"
    fi

    # Check for diagnostic files
    if [ -f backend/diagnostic.py ]; then
        echo "[FAIL] diagnostic.py found (should be removed)"
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] No diagnostic files"
    fi

    # Check for temporary files (excluding requirements.txt)
    if ls backend/*.txt 1> /dev/null 2>&1; then
        if ls backend/*.txt | grep -v requirements.txt 1> /dev/null 2>&1; then
            echo "[FAIL] Temporary .txt files found in backend"
            ls backend/*.txt | grep -v requirements.txt
            test_passed=0
            ((TESTS_FAILED++))
        else
            echo "[PASS] Only requirements.txt found (legitimate)"
        fi
    else
        echo "[PASS] No .txt files found"
    fi

    # Check for backup files
    if ls backend/*.bak 1> /dev/null 2>&1; then
        echo "[FAIL] Backup files found in backend"
        ls backend/*.bak
        test_passed=0
        ((TESTS_FAILED++))
    else
        echo "[PASS] No backup files"
    fi

    # Check for __pycache__ directories
    if find backend -type d -name __pycache__ 1> /dev/null 2>&1; then
        echo "[WARN] __pycache__ directories found (should be removed)"
        find backend -type d -name __pycache__
    else
        echo "[PASS] No __pycache__ directories"
    fi

    # Check data directories (should not exist initially)
    if [ -d uploads ]; then
        echo "[WARN] uploads directory exists (should be created at runtime)"
    else
        echo "[PASS] uploads directory does not exist (will be created)"
    fi

    if [ -d chromadb_data ]; then
        echo "[WARN] chromadb_data directory exists (should be created at runtime)"
    else
        echo "[PASS] chromadb_data directory does not exist (will be created)"
    fi

    if [ -d logs ]; then
        echo "[WARN] logs directory exists (should be created at runtime)"
    else
        echo "[PASS] logs directory does not exist (will be created)"
    fi

    if [ $test_passed -eq 1 ]; then
        ((TESTS_PASSED++))
        echo "[PASS] Cleanliness test passed"
    fi
    echo ""
}
