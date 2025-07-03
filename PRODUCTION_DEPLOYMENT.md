# PocketPro:SBA Production Deployment Guide

This guide covers deploying PocketPro:SBA Edition to production environments, including Render.com.

## Architecture Overview

The production setup consists of three main services:

1. **ChromaDB** - Vector database for document embeddings
2. **Backend API** - Flask application with RAG capabilities
3. **Frontend** - React application built as static files

## Local Production Testing

### Prerequisites

- Docker and Docker Compose
- Node.js 16+ (for frontend builds)
- Python 3.9+ (for local development)

### Quick Start

1. **Environment Setup**
   ```bash
   # Copy environment template
   cp .env.template .env
   
   # Edit .env with your configuration
   # Required: GEMINI_API_KEY=your_api_key_here
   ```

2. **Deploy Locally**
   ```bash
   # Windows
   .\deploy-production.ps1
   
   # Linux/Mac
   chmod +x deploy-production.sh && ./deploy-production.sh
   ```

3. **Access Application**
   - Frontend: http://localhost
   - Backend API: http://localhost:5000
   - ChromaDB: http://localhost:8000

### Manual Deployment

```bash
# Stop existing containers
docker-compose -f docker-compose.prod.yml down

# Build and start production services
docker-compose -f docker-compose.prod.yml up --build -d

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Render.com Deployment

### 1. Repository Setup

1. Push your code to GitHub/GitLab
2. Connect repository to Render.com
3. Set up environment variables in Render dashboard

### 2. Required Environment Variables

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key

# Optional (will be generated if not provided)
SECRET_KEY=your_secret_key

# Automatic (set by Render)
CHROMA_HOST=auto_configured_by_render
REACT_APP_BACKEND_URL=auto_configured_by_render
```

### 3. Service Configuration

The `render.yaml` file defines three services:

1. **ChromaDB Service**
   - Type: Web service with Docker
   - Persistent disk for data storage
   - Exposes vector database API

2. **Backend Service**
   - Type: Web service with Docker
   - Connects to ChromaDB
   - Health check endpoint: `/health`
   - Auto-scaling capable

3. **Frontend Service**
   - Type: Static site
   - Built from React source
   - Automatically connected to backend

### 4. Deployment Steps

1. **Create Render Account**
   - Sign up at render.com
   - Connect your GitHub/GitLab account

2. **Deploy from Dashboard**
   - Create new service from Git repository
   - Select "Docker" as environment
   - Render will read `render.yaml` automatically

3. **Set Environment Variables**
   ```
   GEMINI_API_KEY=your_actual_api_key
   ```

4. **Monitor Deployment**
   - Check logs in Render dashboard
   - Verify all services are healthy
   - Test functionality

## Production Features

### Security
- CORS configuration for cross-origin requests
- Security headers in nginx configuration
- Environment variable protection
- Health checks for all services

### Performance
- Gunicorn WSGI server for Python backend
- Static file serving with nginx
- Gzip compression enabled
- Proper caching headers

### Scalability
- Containerized services
- Horizontal scaling support
- Persistent data storage
- Load balancer ready

### Monitoring
- Health check endpoints
- Service dependency management
- Container restart policies
- Logging aggregation

## Troubleshooting

### Common Issues

1. **ChromaDB Connection Failed**
   ```bash
   # Check ChromaDB logs
   docker-compose -f docker-compose.prod.yml logs chromadb
   
   # Verify network connectivity
   docker-compose -f docker-compose.prod.yml exec backend ping chromadb
   ```

2. **Frontend Shows 404 Errors**
   ```bash
   # Check nginx configuration
   docker-compose -f docker-compose.prod.yml logs frontend
   
   # Verify build artifacts
   docker-compose -f docker-compose.prod.yml exec frontend ls -la /usr/share/nginx/html
   ```

3. **Backend API Errors**
   ```bash
   # Check backend logs
   docker-compose -f docker-compose.prod.yml logs backend
   
   # Test health endpoint
   curl http://localhost:5000/health
   ```

### Health Checks

```bash
# Run comprehensive health check
python simple_health_check.py

# Test specific endpoints
curl http://localhost:5000/health
curl http://localhost:8000/api/v2/heartbeat
curl http://localhost/
```

### Performance Monitoring

```bash
# Monitor resource usage
docker stats

# Check service performance
docker-compose -f docker-compose.prod.yml logs --tail=100 -f

# Monitor ChromaDB metrics
curl http://localhost:8000/api/v2/heartbeat
```

## Maintenance

### Updates
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up --build -d
```

### Backups
```bash
# Backup ChromaDB data
docker-compose -f docker-compose.prod.yml exec chromadb tar -czf /tmp/chromadb-backup.tar.gz /chroma/chroma

# Copy backup to host
docker cp container_name:/tmp/chromadb-backup.tar.gz ./backups/
```

### Scaling
```bash
# Scale backend service
docker-compose -f docker-compose.prod.yml up --scale backend=3 -d
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | - | Google Gemini API key for LLM |
| `SECRET_KEY` | No | Generated | Flask secret key |
| `FLASK_ENV` | No | production | Flask environment |
| `CHROMA_HOST` | No | chromadb | ChromaDB host |
| `CHROMA_PORT` | No | 8000 | ChromaDB port |
| `CORS_ORIGINS` | No | * | Allowed CORS origins |
| `REACT_APP_BACKEND_URL` | No | Auto | Frontend backend URL |

## Support

For issues and questions:
1. Check the logs for error messages
2. Verify environment configuration
3. Test individual service health
4. Review this documentation
5. Check the main README.md for additional help
