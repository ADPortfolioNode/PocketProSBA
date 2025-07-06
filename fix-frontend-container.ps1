# PowerShell script to fix frontend container issues

Write-Host "Fixing frontend container issues..." -ForegroundColor Cyan

# Navigate to the project root
Set-Location "e:\2024 RESET\PocketProSBA"

# Create a custom docker-compose file for rebuilding just the frontend
$customCompose = @"
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - REACT_APP_BACKEND_URL=http://localhost:10000
      - CI=false
      - ESLINT_NO_DEV_ERRORS=true
      - NODE_OPTIONS=--max-old-space-size=4096
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
"@

$customCompose | Out-File -FilePath "docker-compose.frontend.yml" -Encoding utf8

# Rebuild just the frontend service
Write-Host "Rebuilding frontend container with react-bootstrap..." -ForegroundColor Yellow
docker-compose -f docker-compose.frontend.yml up -d --build

Write-Host "Rebuild completed!" -ForegroundColor Green
Write-Host "Check the application at http://localhost:10000" -ForegroundColor Cyan
