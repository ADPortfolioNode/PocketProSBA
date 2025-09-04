#!/bin/bash

echo "Running comprehensive test suite for PocketPro SBA..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run backend tests
run_backend_tests() {
    echo -e "${YELLOW}Running backend tests...${NC}"
    cd backend

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo -e "${RED}Virtual environment not found. Creating one...${NC}"
        python -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Install dependencies if needed
    if [ ! -f "requirements.txt" ]; then
        echo -e "${RED}requirements.txt not found${NC}"
        return 1
    fi

    pip install -r requirements.txt

    # Run pytest
    python -m pytest tests/ -v --tb=short

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Backend tests passed!${NC}"
    else
        echo -e "${RED}Backend tests failed!${NC}"
        return 1
    fi

    cd ..
}

# Function to run frontend tests
run_frontend_tests() {
    echo -e "${YELLOW}Running frontend tests...${NC}"
    cd frontend

    # Install dependencies if needed
    if [ ! -f "package.json" ]; then
        echo -e "${RED}package.json not found${NC}"
        return 1
    fi

    npm install

    # Run Jest tests
    npm test -- --watchAll=false --passWithNoTests

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Frontend tests passed!${NC}"
    else
        echo -e "${RED}Frontend tests failed!${NC}"
        return 1
    fi

    cd ..
}

# Function to run integration tests
run_integration_tests() {
    echo -e "${YELLOW}Running integration tests...${NC}"

    # Start backend server in background
    cd backend
    source venv/bin/activate
    python app.py &
    BACKEND_PID=$!

    # Wait for backend to start
    sleep 5

    # Run integration tests
    python -m pytest tests/test_integration.py -v --tb=short -m integration

    INTEGRATION_RESULT=$?

    # Kill backend server
    kill $BACKEND_PID

    if [ $INTEGRATION_RESULT -eq 0 ]; then
        echo -e "${GREEN}Integration tests passed!${NC}"
    else
        echo -e "${RED}Integration tests failed!${NC}"
        return 1
    fi

    cd ..
}

# Main execution
echo "Starting test execution..."

# Run backend tests
run_backend_tests
BACKEND_RESULT=$?

# Run frontend tests
run_frontend_tests
FRONTEND_RESULT=$?

# Run integration tests
run_integration_tests
INTEGRATION_RESULT=$?

# Summary
echo -e "\n${YELLOW}Test Summary:${NC}"
echo "Backend tests: $([ $BACKEND_RESULT -eq 0 ] && echo -e "${GREEN}PASSED${NC}" || echo -e "${RED}FAILED${NC}")"
echo "Frontend tests: $([ $FRONTEND_RESULT -eq 0 ] && echo -e "${GREEN}PASSED${NC}" || echo -e "${RED}FAILED${NC}")"
echo "Integration tests: $([ $INTEGRATION_RESULT -eq 0 ] && echo -e "${GREEN}PASSED${NC}" || echo -e "${RED}FAILED${NC}")"

# Exit with appropriate code
if [ $BACKEND_RESULT -eq 0 ] && [ $FRONTEND_RESULT -eq 0 ] && [ $INTEGRATION_RESULT -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed! 🎉${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed. Please review the output above.${NC}"
    exit 1
fi
