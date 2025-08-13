# Docker Build Browser URLs - PocketPro:SBA

## Local Development URLs (Docker Compose)

When running Docker builds locally, these are the typical browser URLs:

### Frontend Services
- **Frontend (React App)**: http://localhost:3000
- **Frontend Development**: http://localhost:3000 (with hot reload)

### Backend Services
- **Backend API**: http://localhost:5000
- **Backend Health Check**: http://localhost:5000/health
- **API Documentation**: http://localhost:5000/api/docs (if available)

### Database Services
- **ChromaDB Interface**: http://localhost:8000
- **ChromaDB API**: http://localhost:8000/api/v1

## Docker Build Commands with Browser Access

### Standard Docker Compose Build
```bash
# Build and start all services
docker-compose up --build

# Access URLs:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:5000
# - ChromaDB: http://localhost:8000
```

### Production Build
```bash
# Production build
docker-compose -f docker-compose.prod.yml up --build

# Access URLs:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:5000
```

### Minimal Memory Build
```bash
# Minimal memory setup
docker-compose -f docker-compose.minimal-memory.yml up --build

# Access URLs:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:5000
```

## Render.com Deployment URLs

### After Docker Build Deploy to Render
- **Frontend**: https://your-frontend-name.onrender.com
- **Backend**: https://your-backend-name.onrender.com
- **ChromaDB**: https://your-chromadb-name.onrender.com (private service)

## Docker Build URLs by Service Type

### Frontend Container
- **Development**: http://localhost:3000
- **Production**: http://localhost:3000 (mapped from container port 80)

### Backend Container
- **API Base**: http://localhost:5000
- **API Endpoints**: http://localhost:5000/api/*
- **Health Check**: http://localhost:5000/health

### ChromaDB Container
- **Database Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Quick Access Commands

```bash
# Check if services are running
docker-compose ps

# View logs
docker-compose logs frontend
docker-compose logs backend
docker-compose logs chromadb

# Test URLs
curl http://localhost:3000      # Frontend
curl http://localhost:5000/health  # Backend health
curl http://localhost:8000      # ChromaDB
```

## Troubleshooting URLs

If services aren't accessible:
1. Check Docker containers: `docker-compose ps`
2. Check port bindings: `docker-compose port [service] [port]`
3. Check logs: `docker-compose logs [service]`
4. Verify network: `docker network ls`
