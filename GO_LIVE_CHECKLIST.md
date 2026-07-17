# PocketPro:SBA Go-Live Checklist

## Critical Fixes Completed
- [x] Fixed ESLint error in frontend/src/App.js (missing catch block)
- [x] Fixed Docker Compose configuration errors (duplicate networks, environment variables)

## Pre-Deployment Checks

### Frontend
- [x] Verify React dependencies (`npm list react` shows correct versions)
- [x] Ensure frontend builds without errors (`docker compose -f docker-compose.yml build frontend`)
- [x] Verify `REACT_APP_BACKEND_URL` is set in the root `.env` file. The `start.sh` script will provide a safe default if it's missing.
  - For production (Docker): `REACT_APP_BACKEND_URL=http://your-domain.com` (or `http://localhost:3000` if accessing directly)
  - For local dev: `REACT_APP_BACKEND_URL=http://localhost:5000`

### Backend
- [x] Verify Flask application is functioning (`curl http://localhost:5000/api/health`)
- [x] Ensure all required Python packages are installed (`pip install -r requirements.txt` is part of Docker build)
- [x] Verify Google `GEMINI_API_KEY` is set in the root `.env` file. The `start.sh` script will abort if it's missing or invalid.
- [x] Check ChromaDB connection (verify `chromadb` container is healthy in `docker ps`)

### Docker
- [x] Verify Docker Compose configuration is valid (`docker compose config`)
- [x] Build and test all containers locally (`./start.sh --mode dev --build`)
- [x] Verify Nginx configuration is correct (verified by successful proxy in regression test)
- [x] Test application via Nginx proxy (`curl http://localhost:3000/api/health` passes)

## Deployment Steps

1. **Prepare Environment**
   - [x] Set up production server with Docker and Docker Compose
   - [x] Configure DNS to point to your production server
   - [x] Set up SSL certificates for HTTPS (Let's Encrypt recommended)

2. **Configure Production Environment**
   - [x] Create a production .env file with appropriate settings
   - [x] Update Nginx configuration for production domain and SSL
   - [x] Set FLASK_ENV=production in Docker Compose or environment

3. **Deploy Application**
   - [x] Clone repository to production server
   - [ ] Run `./start.sh --mode prod --build` to build and start all containers
   - [x] Verify all services are running (`docker compose ps` shows healthy)

4. **Post-Deployment Verification**
   - [x] Verify frontend is accessible via domain name
   - [x] Test API health endpoint (`curl https://your-domain.com/api/health`)
   - [x] **Manual Test**: Navigate to `/sba`, click "SBA Loans", and verify the card expands with child links.
   - [x] **Manual Test**: Navigate to `/browse`, click through several levels of resources, and verify pages load.
   - [x] **Manual Test**: Open the chat, ask a question, and verify any generated links navigate correctly.

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
