# Production Deployment Full Testing Plan

## Objective
To thoroughly test the production deployment process and Docker port communication locking solution to ensure production readiness with minimal regression risk.

## Scope
- Execution of the production deployment script (`deploy-production.ps1`)
- Verification of Docker and Docker Compose installation and versions
- Validation of environment file (.env) presence and critical variables (e.g., GEMINI_API_KEY)
- Docker container orchestration using `docker-compose.prod.yml`
- Verification of container startup and port communication locking
- Backend health check endpoint availability and response correctness
- Log monitoring and error detection during deployment and runtime
- Rollback and cleanup procedures (docker-compose down)

## Test Cases

### 1. Prerequisite Checks
- Verify Docker is installed and accessible
- Verify Docker Compose is installed and accessible
- Verify .env file exists and contains required variables

### 2. Deployment Script Execution
- Run `deploy-production.ps1` with default and custom environment parameters
- Confirm script stops existing containers gracefully
- Confirm script builds and starts containers successfully
- Confirm script waits for services to start

### 3. Container and Port Communication
- Verify all expected containers are running after deployment
- Verify ports are correctly locked and exposed as per configuration
- Validate no port conflicts or binding errors occur

### 4. Backend Health Check
- Send HTTP requests to backend health check endpoint (http://localhost:5000/api/health)
- Confirm HTTP 200 response and expected health status

### 5. Logs and Monitoring
- Monitor docker-compose logs for errors or warnings during and after deployment
- Confirm no critical errors are present

### 6. Rollback and Cleanup
- Run `docker-compose -f docker-compose.prod.yml down`
- Confirm all containers are stopped and resources cleaned up

## Reporting
- Document test results for each test case
- Highlight any issues or regressions found
- Provide recommendations for fixes or improvements if needed

## Tools and Commands
- PowerShell for script execution
- Docker CLI for container management
- curl or HTTP client for health check requests
- Log inspection via `docker-compose logs`

---

Please confirm this testing plan so I can proceed with implementation.
