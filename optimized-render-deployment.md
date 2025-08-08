upd# Optimized Render Deployment Configuration

## Issue Analysis
The deployment log shows `ModuleNotFoundError: No module named 'flask_cors'` despite flask-cors being listed in requirements files. This indicates:

1. **Requirements mismatch**: Different requirements files being used
2. **Installation failure**: Dependencies not properly installed
3. **Dockerfile optimization needed**: Better dependency management

## Optimized Configuration

### 1. Consolidated Requirements (requirements-render-optimized.txt)
```txt
# Optimized Render deployment requirements - Python 3.13 compatible
# Core Flask dependencies with explicit versions
flask==3.0.0
flask-cors==4.0.0
flask-socketio==5.3.6
gunicorn==21.2.0
eventlet==0.33.3

# AI and Vector Database - Python 3.13 compatible
chromadb==0.4.24
google-generativeai==0.4.0
sentence-transformers==2.2.2

# Core utilities
python-dotenv==1.0.0
requests==2.31.0
numpy==1.26.2
PyPDF2==3.0.1
python-multipart==0.0.9

# System dependencies
pydantic==2.5.2
urllib3>=1.26.0,<3.0.0
setuptools>=68.0.0
```

### 2. Optimized Dockerfile (Dockerfile.optimized)
```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    procps \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random

# Copy and install dependencies FIRST (better caching)
COPY requirements-render-optimized.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-render-optimized.txt

# Copy application code
COPY . .

# Environment variables
ENV FLASK_APP=app_full.py
ENV FLASK_ENV=production
ENV PORT=5000

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# Use gunicorn with optimized settings
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "2", \
     "--threads", "4", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--preload", \
     "app_full:app"]
```

### 3. Optimized Render Configuration (render-optimized.yaml)
```yaml
services:
  - type: web
    name: pocketpro-sba-optimized
    runtime: docker
    plan: standard
    region: oregon
    dockerfilePath: ./Dockerfile.optimized
    autoDeploy: true
    
    # Environment variables
    envVars:
      - key: PYTHON_VERSION
        value: "3.13"
      - key: FLASK_ENV
        value: "production"
      - key: PORT
        value: "5000"
      - key: GEMINI_API_KEY
        sync: false
      - key: SECRET_KEY
        generateValue: true
      - key: CORS_ORIGINS
        value: "*"

    # Health check
    healthCheckPath: /health
    
    # Build optimization
    buildFilter:
      paths:
        - "!*.md"
        - "!*.txt"
        - "!tests/"
        - "!docs/"
```

### 4. Build Script Optimization (build-optimized.sh)
```bash
#!/bin/bash
set -e

echo "🚀 Starting optimized build process..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf __pycache__ .pytest_cache dist build

# Install dependencies with verification
echo "📦 Installing dependencies..."
pip install --no-cache-dir -r requirements-render-optimized.txt

# Verify critical dependencies
echo "✅ Verifying dependencies..."
python -c "import flask_cors; print('flask-cors:', flask_cors.__version__)"
python -c "import flask; print('flask:', flask.__version__)"
python -c "import chromadb; print('chromadb:', chromadb.__version__)"

# Run basic health check
echo "🏥 Running health check..."
python -c "from app_full import app; print('App loaded successfully')"

echo "✅ Build completed successfully!"
```

### 5. Deployment Verification Script (verify-deployment.py)
```python
#!/usr/bin/env python3
import requests
import sys
import time

def verify_deployment(url):
    """Verify the deployment is working correctly."""
    print(f"🔍 Verifying deployment at {url}")
    
    try:
        # Health check
        response = requests.get(f"{url}/health", timeout=30)
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
        # API endpoints
        endpoints = ['/api/info', '/api/health']
        for endpoint in endpoints:
            response = requests.get(f"{url}{endpoint}", timeout=30)
            if response.status_code == 200:
                print(f"✅ {endpoint} accessible")
            else:
                print(f"❌ {endpoint} failed: {response.status_code}")
                return False
                
        print("✅ All verification checks passed!")
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    verify_deployment(url)
```

## Deployment Steps

1. **Update requirements file**:
   ```bash
   cp requirements-render-optimized.txt requirements.txt
   ```

2. **Update Dockerfile**:
   ```bash
   cp Dockerfile.optimized Dockerfile
   ```

3. **Update render configuration**:
   ```bash
   cp render-optimized.yaml render.yaml
   ```

4. **Deploy with verification**:
   ```bash
   chmod +x build-optimized.sh
   ./build-optimized.sh
   ```

## Performance Optimizations

- **Faster builds**: Optimized Dockerfile with better caching
- **Memory efficient**: Python 3.13 slim base image
- **Dependency verification**: Build-time checks for critical packages
- **Health monitoring**: Comprehensive health checks
- **Resource optimization**: Tuned gunicorn settings for Render

## Troubleshooting

If flask_cors error persists:
1. Check which requirements file is being used in deployment
2. Verify the Docker build context includes the correct requirements file
3. Run the verification script to confirm all dependencies are installed
