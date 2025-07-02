# PocketPro:SBA Go-Live Checklist

## Critical Fixes Completed
- [x] Fixed ESLint error in frontend/src/App.js (missing catch block)
- [x] Fixed Docker Compose configuration errors (duplicate networks, environment variables)

## Pre-Deployment Checks

### Frontend
- [ ] Verify React dependencies (`npm list react` shows correct versions)
- [ ] Ensure frontend builds without errors (`cd frontend && npm run build`)
- [ ] Verify REACT_APP_BACKEND_URL is set correctly in .env files:
  - For production: REACT_APP_BACKEND_URL=https://your-production-domain
  - For local Docker: REACT_APP_BACKEND_URL=http://localhost:10000
  - For local dev: REACT_APP_BACKEND_URL=http://localhost:5000

### Backend
- [ ] Verify Flask application is functioning (http://localhost:5000/health)
- [ ] Ensure all required Python packages are installed (`pip install -r requirements.txt`)
- [ ] Verify Google Gemini API key is set in environment variables
- [ ] Check ChromaDB connection (run `python test_chroma_connection.py`)

### Docker
- [ ] Verify Docker Compose configuration is valid (`docker-compose config`)
- [ ] Build and test all containers locally (`docker-compose up -d`)
- [ ] Verify Nginx configuration is correct (`nginx -t` inside container)
- [ ] Test application via Nginx proxy (http://localhost:10000)

## Deployment Steps

1. **Prepare Environment**
   - [ ] Set up production server with Docker and Docker Compose
   - [ ] Configure DNS to point to your production server
   - [ ] Set up SSL certificates for HTTPS (Let's Encrypt recommended)

2. **Configure Production Environment**
   - [ ] Create a production .env file with appropriate settings
   - [ ] Update Nginx configuration for production domain and SSL
   - [ ] Set FLASK_ENV=production in Docker Compose or environment

3. **Deploy Application**
   - [ ] Clone repository to production server
   - [ ] Run `docker-compose up -d --build` to build and start all containers
   - [ ] Verify all services are running (`docker-compose ps`)

4. **Post-Deployment Verification**
   - [ ] Verify frontend is accessible via HTTPS
   - [ ] Test API endpoints (health check, file upload, chat)
   - [ ] Verify ChromaDB connection and vector search functionality
   - [ ] Test end-to-end functionality (document upload, search, chat)

## Monitoring and Maintenance

- [ ] Set up application logging to persistent storage
- [ ] Configure monitoring for container health and resource usage
- [ ] Set up automated backups for ChromaDB data
- [ ] Create a rollback plan in case of deployment issues

## Security Considerations

- [ ] Review API endpoints for potential security issues
- [ ] Ensure sensitive environment variables are properly secured
- [ ] Verify CORS settings are appropriate for production
- [ ] Review file upload security (allowed file types, size limits)
