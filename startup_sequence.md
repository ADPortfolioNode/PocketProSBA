# Optimal Startup Sequence for Stable Render.com Deployment

This document outlines the recommended startup sequence and configuration for deploying the PocketPro SBA application on Render.com to ensure stability and performance.

## 1. Environment Setup

- Ensure all required environment variables are set:
  - `GEMINI_API_KEY`
  - `SECRET_KEY`
  - `PORT` (typically 10000 for Render.com Docker deployment)
  - `CHROMA_HOST` and `CHROMA_PORT` if using ChromaDB service
  - Other app-specific environment variables as needed

- Use `requirements-full.txt` for backend dependencies to match production environment.

## 2. Backend Startup

- Use the Dockerfile `Dockerfile.render.full` for building the backend image.
- The backend Flask app should:
  - Bind to `0.0.0.0` and listen on the port specified by the `PORT` environment variable (default 10000).
  - Initialize ChromaDB client if available, with proper error handling and fallback.
  - Initialize vector store and RAG system before accepting requests.
  - Register all API routes and health check endpoints.
  - Serve React frontend build for non-API routes.
- Use Gunicorn with the following recommended command:
  ```
  gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 app_full:app
  ```
- Ensure logging is enabled for startup steps and errors.

## 3. Frontend Startup

- Use the Node runtime with the following build and start commands:
  - Build: `cd frontend && npm install --legacy-peer-deps && npm run build`
  - Start: `npx serve -s frontend/build -l $PORT`
- The frontend should:
  - Serve static files from the build directory.
  - Use environment variable `REACT_APP_BACKEND_URL` to point to the backend URL.
  - Use port 10000 or the port assigned by Render.com.

## 4. Health Checks and Monitoring

- Configure health check endpoint `/health` on the backend.
- Render.com will use this endpoint to monitor service health and restart if necessary.
- Monitor logs and metrics via Render dashboard.

## 5. Local Development Setup

- Backend Flask app should run on port 10000 locally to mimic Render.com.
- Frontend React dev server should run on port 3000.
- Use proxy middleware in frontend (`setupProxy.js`) to forward `/api` requests to `http://localhost:10000`.
- Use `.env` files to set environment variables consistently.

## 6. Deployment

- Push all changes to GitHub repository connected to Render.com.
- Use Render Blueprints or manual service creation with `render.yaml` configuration.
- Clear build cache on Render.com before redeploying to avoid stale dependencies.
- Verify deployment by accessing backend health endpoint and frontend UI.

---

This sequence ensures a stable and performant deployment on Render.com, matching local development environment closely for easier debugging and testing.
