# DOCKER AND RENDER.COM DEPLOYMENT GUIDE

This document provides detailed instructions on Docker configuration, port mapping, and Render.com deployment for the PocketPro:SBA Edition application.

## DOCKER CONFIGURATION

### Port Mappings and Services

| Service  | Internal Port | External Port | Description |
|----------|---------------|--------------|-------------|
| Backend  | 5000          | 5000         | Flask API server with Gunicorn |
| Frontend | 3000          | 3000         | React development server |
| Nginx    | 80            | 8080         | Reverse proxy for routing |

### Service Architecture

```
Client → Nginx (8080) → Frontend (3000) or Backend (5000)
```

### Docker Compose Configuration

The application uses Docker Compose to orchestrate multiple containers:

1. **Backend Container**
   - Built using `Dockerfile.backend`
   - Memory allocation: 1GB limit, 512MB reservation
   - Uses a minimal Gunicorn configuration with single worker
   - Leverages tmpfs for in-memory temporary storage
   - Environment variables configured for development

2. **Frontend Container**
   - Built using `Dockerfile.frontend.dev`
   - Memory allocation: 3GB limit, 1GB reservation
   - Source maps disabled to reduce memory usage
   - Environment variables configured for React development

3. **Nginx Container**
   - Uses standard nginx:alpine image
   - Routes traffic between frontend and backend
   - Handles WebSocket connections for real-time features

## NGINX ROUTING CONFIGURATION

The nginx.conf file defines the following routes:

1. **Frontend Routes (`/`)**
   - All root requests are proxied to the frontend service on port 3000
   - WebSocket support enabled for hot reloading

2. **Backend API Routes (`/api/`)**
   - All `/api/` requests are proxied to the backend service on port 5000
   - Preserves request headers for proper communication

3. **Health Check Route (`/health`)**
   - Routed to the backend health check endpoint
   - Used for container orchestration and monitoring

4. **WebSocket Routes (`/socket.io/`)**
   - WebSocket connections for real-time features
   - Properly configured for Socket.IO

## RENDER.COM DEPLOYMENT

### Render.com Configuration

The application is configured for deployment on Render.com using the following approach:

1. **Web Service Configuration**
   - Uses Docker deployment via `Dockerfile.render`
   - Exposes a single port (default: 5000)
   - Environment variables set through Render dashboard
   - Health check configured to monitor application status

2. **Environment Variables**
   - `PORT`: Set by Render (default: 5000)
   - `FLASK_ENV`: Set to "production"
   - `FLASK_APP`: Set to "minimal_app.py"
   - Additional environment variables as defined in PRODUCTION_DEPLOYMENT_GUIDE.md

3. **Resource Allocation**
   - Starter plan recommended for initial deployment
   - Scale up resources based on usage patterns

### Deployment Steps

1. **Prepare for Deployment**
   ```bash
   # Option 1: Using Render Blueprint
   render blueprint render render.production.yaml
   
   # Option 2: Manual Deployment via Dashboard
   # See PRODUCTION_DEPLOYMENT_GUIDE.md for detailed steps
   ```

2. **Post-Deployment Verification**
   - Verify application is running at: `https://[your-app-name].onrender.com/`
   - Check health endpoint at: `https://[your-app-name].onrender.com/health`
   - Review logs in Render dashboard for any errors

## MEMORY OPTIMIZATION

The Docker configuration has been optimized to prevent "out of memory" errors:

1. **Backend Optimizations**
   - Single worker Gunicorn configuration
   - Disabled Python memory debugging
   - tmpfs volume for temporary files
   - Limited maximum requests per worker

2. **Frontend Optimizations**
   - Disabled source map generation
   - Configured Node.js memory limit (2GB max old space)
   - WebSocket port configuration to avoid conflicts
   - Efficient npm installation in Dockerfile

## TROUBLESHOOTING

### Common Issues and Solutions

1. **Memory Issues**
   - If the backend container crashes with "Cannot allocate memory" errors:
     - Increase memory limit in docker-compose.yml
     - Reduce worker count in Gunicorn configuration
     - Ensure Python debugging is disabled

2. **Port Conflicts**
   - If you see "port is already allocated" errors:
     - Ensure no other services are using ports 5000, 3000, or 8080
     - Change the external port mapping in docker-compose.yml

3. **Connection Issues**
   - If frontend cannot connect to backend:
     - Verify REACT_APP_BACKEND_URL environment variable
     - Check nginx.conf for proper routing configuration
     - Ensure backend health endpoint is accessible

## NEXT STEPS

Now that you have a stable deployment, you can:

1. Further enhance the frontend UI and features
2. Create a Git commit to mark this stable version
3. Implement additional RAG capabilities
4. Scale up resources based on usage patterns

For more detailed information, refer to PRODUCTION_DEPLOYMENT_GUIDE.md and DEPLOYMENT.md.
