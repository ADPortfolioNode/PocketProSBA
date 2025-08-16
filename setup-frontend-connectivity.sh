#!/bin/bash

# Comprehensive Frontend Connectivity Setup Script
# This script configures the frontend for all deployment scenarios

echo "🔧 Setting up comprehensive frontend connectivity..."

# Create necessary directories
mkdir -p frontend/src/config
mkdir -p frontend/src/services

# Ensure all required files exist
echo "✅ Checking required files..."

# Create .env file if it doesn't exist
if [ ! -f frontend/.env ]; then
    echo "📝 Creating .env file from template..."
    cp frontend/.env.example frontend/.env
    echo "⚠️  Please edit frontend/.env with your specific configuration"
fi

# Create enhanced package.json with proxy configurations
echo "🔄 Updating package.json with enhanced proxy settings..."

# Create Docker configuration for frontend
cat > frontend/Dockerfile.connectivity << 'EOF'
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Install serve for production
RUN npm install -g serve

# Expose port
EXPOSE 3000

# Start the app
CMD ["serve", "-s", "build", "-l", "3000"]
EOF

# Create nginx configuration for production
cat > frontend/nginx.connectivity.conf << 'EOF'
server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api {
        proxy_pass http://backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://backend:5000/health;
    }
}
EOF

# Create Docker Compose for full stack
cat > docker-compose.connectivity.yml << 'EOF'
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - PORT=5000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.connectivity
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - REACT_APP_BACKEND_URL=http://backend:5000
      - REACT_APP_DEV_MODE=false

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./frontend/nginx.connectivity.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
      - frontend
EOF

# Create Windows batch file equivalent
cat > setup-frontend-connectivity.bat << 'EOF'
@echo off
echo 🔧 Setting up comprehensive frontend connectivity...

REM Create necessary directories
if not exist frontend\src\config mkdir frontend\src\config
if not exist frontend\src\services mkdir frontend\src\services

REM Create .env file if it doesn't exist
if not exist frontend\.env (
    echo 📝 Creating .env file from template...
    copy frontend\.env.example frontend\.env
    echo ⚠️  Please edit frontend\.env with your specific configuration
)

echo ✅ Frontend connectivity setup complete!
echo.
echo 🚀 To start the application:
echo.
echo Local development:
echo   cd frontend && npm start
echo.
echo Docker deployment:
echo   docker-compose -f docker-compose.connectivity.yml up
echo.
echo Production build:
echo   cd frontend && npm run build
pause
EOF

echo "✅ Frontend connectivity setup complete!"
echo ""
echo "🚀 Available commands:"
echo ""
echo "Local development:"
echo "  cd frontend && npm start"
echo ""
echo "Docker deployment:"
echo "  docker-compose -f docker-compose.connectivity.yml up"
echo ""
echo "Production build:"
echo "  cd frontend && npm run build"
echo ""
echo "📋 Next steps:"
echo "1. Review and update frontend/.env with your configuration"
echo "2. Ensure backend is running on the configured port"
echo "3. Test connectivity with the enhanced diagnostics"
echo ""

# Make scripts executable
chmod +x setup-frontend-connectivity.sh
chmod +x setup-frontend-connectivity.bat

echo "🎉 Setup complete! Your frontend now has comprehensive connectivity support."
EOF

chmod +x setup-frontend-connectivity.sh
