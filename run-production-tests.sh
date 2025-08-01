#!/bin/bash
#
# Production Deployment Full Testing Script
#
# This script automates the testing plan outlined in production-testing-plan.md.
# It performs prerequisite checks, deploys the application using docker-compose,
# verifies container health, checks logs for errors, and cleans up resources.
#
# Usage:
# 1. Ensure you are in the project root directory.
# 2. Make the script executable: chmod +x run-production-tests.sh
# 3. Run the script: ./run-production-tests.sh

# --- Configuration ---
COMPOSE_FILE="docker-compose.prod.yml"
HEALTH_CHECK_URL="http://localhost:5000/api/health"
MAX_RETRIES=12
RETRY_INTERVAL=5 # seconds
ENV_FILE=".env"
# NOTE: Update this list if your service names in docker-compose.prod.yml are different.
EXPECTED_SERVICES=("backend" "frontend" "chromadb")

# --- Colors for output ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# --- Helper Functions ---
print_step() { echo -e "\n${YELLOW}==== $1 ====${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

cleanup() {
    print_step "Performing Cleanup..."
    # The &> /dev/null suppresses output, which is fine for a cleanup step
    # where we don't need to see the "Stopping..." messages.
    docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans &> /dev/null
    print_success "Containers stopped and resources cleaned up."
}

# Trap to ensure cleanup runs on script exit or interruption
trap cleanup EXIT

# --- Test Functions ---
check_prerequisites() {
    print_step "1. Prerequisite Checks"
    local all_ok=true
    command -v docker &> /dev/null || { print_error "Docker not found."; all_ok=false; }
    command -v docker-compose &> /dev/null || { print_error "Docker Compose not found."; all_ok=false; }
    command -v curl &> /dev/null || { print_error "curl not found. It is required for health checks."; all_ok=false; }
    
    if [ "$all_ok" = true ]; then
        print_success "Docker and Docker Compose are installed."
    fi

    if [ ! -f "$ENV_FILE" ]; then
        print_error "$ENV_FILE file is missing."
        all_ok=false
    else
        print_success "$ENV_FILE file found."
        if ! grep -q "GEMINI_API_KEY" "$ENV_FILE"; then
            print_error "GEMINI_API_KEY not defined in $ENV_FILE."
            all_ok=false
        else
            print_success "GEMINI_API_KEY is present in $ENV_FILE."
        fi
    fi

    [ "$all_ok" = false ] && exit 1
}

deploy_and_verify() {
    print_step "2. Deployment and Container Verification"
    echo "Stopping any existing containers..."
    docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans > /dev/null 2>&1

    echo "Building and starting containers with '$COMPOSE_FILE'..."
    docker-compose -f "$COMPOSE_FILE" up --build -d
    if [ $? -ne 0 ]; then
        print_error "docker-compose up failed. See logs below."
        docker-compose -f "$COMPOSE_FILE" logs
        exit 1
    fi
    print_success "Deployment command executed."
    echo "Waiting for services to stabilize..."
    sleep 10

    print_step "3. Container and Port Communication Check"
    local running_containers
    running_containers=$(docker-compose -f "$COMPOSE_FILE" ps --services --filter "status=running")
    
    local all_services_running=true
    for service in "${EXPECTED_SERVICES[@]}"; do
        if ! echo "$running_containers" | grep -q "^${service}$"; then
            print_error "Service '$service' is NOT running."
            all_services_running=false
        else
            print_success "Service '$service' is running."
        fi
    done

    if [ "$all_services_running" = false ]; then
        print_error "One or more services failed to start. See logs below."
        docker-compose -f "$COMPOSE_FILE" logs
        exit 1
    fi
}

run_health_check() {
    print_step "4. Backend Health Check"
    local attempt=1
    while [ $attempt -le $MAX_RETRIES ]; do
        echo "Attempt $attempt/$MAX_RETRIES: Checking backend health at $HEALTH_CHECK_URL..."
        local http_code
        http_code=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_CHECK_URL")
        
        if [ "$http_code" -eq 200 ]; then
            print_success "Backend is healthy! (HTTP 200)"
            return 0
        fi
        
        echo "Backend not ready yet (HTTP $http_code). Retrying in $RETRY_INTERVAL seconds..."
        sleep "$RETRY_INTERVAL"
        ((attempt++))
    done

    print_error "Backend health check failed after $MAX_RETRIES retries."
    print_error "Dumping logs for the 'backend' service:"
    docker-compose -f "$COMPOSE_FILE" logs backend
    exit 1
}

check_logs() {
    print_step "5. Logs and Monitoring"
    echo "Scanning container logs for error keywords..."
    # Give services a moment to log any late startup errors
    sleep 5 

    # We can add more specific error patterns here if needed.
    # The -v flag can be used to exclude known, benign "error" messages.
    local error_patterns="error|failed|exception|traceback|unhandled|cannot"
    local has_errors=false

    for service in "${EXPECTED_SERVICES[@]}"; do
        local service_logs
        service_logs=$(docker-compose -f "$COMPOSE_FILE" logs "$service")
        
        # Grep for error patterns, excluding known safe lines if necessary.
        # Example for excluding a safe line: | grep -v "some safe error message"
        local error_output
        error_output=$(echo "$service_logs" | grep -iE "$error_patterns")

        if [ -n "$error_output" ]; then
            print_error "Potential errors found in '$service' logs:"
            # Indent output for readability
            echo "$error_output" | sed 's/^/    /'
            has_errors=true
        else
            print_success "No critical error keywords found in '$service' logs."
        fi
    done

    if [ "$has_errors" = true ]; then
        echo -e "\n${YELLOW}Potential errors were detected. Manual log inspection is advised.${NC}"
        # We don't exit here, allowing the full test suite to complete,
        # but we do flag it as a potential issue.
    fi
}

# --- Main Execution ---
main() {
    check_prerequisites
    deploy_and_verify
    run_health_check
    check_logs

    print_step "Final Summary"
    print_success "All automated production tests passed successfully!"
    echo "The application appears to be deployed and healthy."
    echo "To perform manual tests, access the frontend at http://localhost"
    echo "The test script will now perform cleanup. Press Ctrl+C to keep containers running."
    sleep 10 # Give user time to see the message and cancel cleanup if needed
}

main