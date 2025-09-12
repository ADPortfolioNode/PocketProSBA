# PocketProSBA Production Deployment Guide

## Overview
This guide covers deploying PocketProSBA to production using either Render.com (recommended) or Docker.

## Render.com Deployment (Recommended)

### Prerequisites
1. GitHub repository connected to Render
2. Google Gemini API key
3. Render.com account with billing enabled

### Deployment Steps

1. **Create New Blueprint**
   - Go to Render Dashboard
   - Click "New +"
   - Select "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml`

2. **Configure Environment Variables**
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - Other variables are auto-configured by Render

3. **Verify Services**
   - Backend API should be running on `https://pocketprosba-backend.onrender.com`
   - Frontend should be accessible at `https://pocketprosba-frontend.onrender.com`
   - ChromaDB service should be running internally

### Health Monitoring
- Backend health check endpoint: `/api/health`
- Monitor logs in Render dashboard
- Set up Render alerts for downtime notifications

## Docker Production Deployment

### Prerequisites
- Docker and Docker Compose installed
- SSL certificates (for HTTPS)
- Environment variables configured

### Deployment Steps

1. **Build Production Images**
   ```bash
   # Build backend
   docker build -f Dockerfile.production -t pocketprosba-backend:latest .
   
   # Build frontend
   docker build -f Dockerfile.frontend -t pocketprosba-frontend:latest .
   
   # Build ChromaDB
   docker build -f Dockerfile.chromadb -t pocketprosba-chromadb:latest .
   ```

2. **Configure Environment**
   Create `.env` file with production values:
   ```
   PORT=5000
   FRONTEND_URL=https://your-domain.com
   GEMINI_API_KEY=your_key_here
   CHROMADB_HOST=chromadb
   CHROMADB_PORT=8000
   SECRET_KEY=your_secure_key
   FLASK_ENV=production
   PYTHONUNBUFFERED=1
   ```

3. **Deploy Services**
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

4. **Verify Deployment**
   ```bash
   # Check service health
   docker-compose ps
   
   # View logs
   docker-compose logs -f
   ```

## Performance Optimization

### Backend
- Gunicorn configured with 2 workers, 4 threads per worker
- Response compression enabled
- Static file caching configured

### Frontend
- React production build with optimization
- Static assets compressed and cached
- API client with retry logic

### ChromaDB
- Persistent storage enabled
- Proper indexing configured
- Regular backup schedule recommended

## Monitoring & Maintenance

### Health Checks
- Regular health check monitoring
- Error rate monitoring
- Response time tracking

### Backup Strategy
- ChromaDB data backup
- Environment configuration backup
- Regular security updates

### Security Measures
- All secrets in environment variables
- CORS properly configured
- Non-root container users
- Regular dependency updates

## Troubleshooting

### Common Issues
1. **502 Bad Gateway**
   - Check if backend service is running
   - Verify Gunicorn worker status
   - Check logs for Python errors

2. **ChromaDB Connection Issues**
   - Verify network connectivity
   - Check ChromaDB logs
   - Ensure proper environment variables

3. **Frontend Loading Issues**
   - Check API URL configuration
   - Verify CORS settings
   - Check browser console for errors

### Recovery Procedures
1. **Service Recovery**
   ```bash
   # Restart all services
   docker-compose restart
   
   # Rebuild and restart specific service
   docker-compose up -d --build backend
   ```

2. **Data Recovery**
   - ChromaDB data can be restored from backups
   - Vector embeddings will regenerate automatically
