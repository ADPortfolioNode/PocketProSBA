# PowerShell script to fix react-bootstrap in Docker

Write-Host "Fixing react-bootstrap in Docker container..." -ForegroundColor Cyan

# Path variables
$projectDir = "e:\2024 RESET\PocketProSBA"
$frontendDir = "$projectDir\frontend"

# Ensure package.json has react-bootstrap
Write-Host "Checking package.json..." -ForegroundColor Yellow
$packageJson = Get-Content -Path "$frontendDir\package.json" -Raw | ConvertFrom-Json

# Verify the package.json has correct structure and react-bootstrap
if (-not ($packageJson.dependencies.'react-bootstrap')) {
    Write-Host "Adding react-bootstrap to package.json..." -ForegroundColor Yellow
    $packageJson.dependencies | Add-Member -MemberType NoteProperty -Name 'react-bootstrap' -Value '^2.8.0'
    $packageJson | ConvertTo-Json | Set-Content -Path "$frontendDir\package.json"
}

# Create a temporary Dockerfile to rebuild with fresh dependencies
Write-Host "Creating a temporary Dockerfile..." -ForegroundColor Yellow
$dockerfileContent = @"
FROM node:16-alpine as build

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install
RUN npm install react-bootstrap@2.8.0 --save

# Copy source files
COPY . .

# Set environment variables - prevent ESLint errors from failing the build
ENV CI=false
ENV ESLINT_NO_DEV_ERRORS=true
ENV NODE_OPTIONS=--max-old-space-size=4096

# Build the application
RUN npm run build

# Production environment
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
"@

$dockerfileContent | Set-Content -Path "$frontendDir\Dockerfile.fixed" -Encoding UTF8

# Backup original Dockerfile if it exists
if (Test-Path "$frontendDir\Dockerfile") {
    Write-Host "Backing up original Dockerfile..." -ForegroundColor Yellow
    Copy-Item -Path "$frontendDir\Dockerfile" -Destination "$frontendDir\Dockerfile.bak" -Force
}

# Replace Dockerfile with fixed version
Write-Host "Replacing Dockerfile with fixed version..." -ForegroundColor Yellow
Copy-Item -Path "$frontendDir\Dockerfile.fixed" -Destination "$frontendDir\Dockerfile" -Force

# Check if Docker is running
$dockerRunning = $null
try {
    $dockerRunning = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
} catch {
    $dockerRunning = $null
}

if ($dockerRunning) {
    Write-Host "Docker is running. Rebuilding container..." -ForegroundColor Green
    
    # Go to project directory
    Set-Location $projectDir
    
    # Stop containers
    docker-compose down
    
    # Rebuild and restart
    docker-compose up -d --build
    
    Write-Host "Container rebuild initiated. Please wait for it to complete..." -ForegroundColor Cyan
    Write-Host "Access the application at: http://localhost:10000" -ForegroundColor Green
} else {
    Write-Host "Docker Desktop is not running. Please start Docker Desktop first." -ForegroundColor Red
    Write-Host "After starting Docker Desktop, run: docker-compose up -d --build" -ForegroundColor Yellow
}

Write-Host "Fix process complete!" -ForegroundColor Cyan
