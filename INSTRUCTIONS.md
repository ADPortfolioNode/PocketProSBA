# PocketPro:SBA Edition - Production Build & Deployment Instructions (2025)

## Production-Ready Build & Deployment (Render.com, Docker, Local)

---

### Prerequisites
- **Python 3.9+** (or 3.13 for requirements_full.txt)
- **Node.js 16.x** (Node 20+ is NOT supported due to frontend build issues with ajv/ajv-keywords)
- **Docker & Docker Compose**
- **Google Gemini API key**

---

### Environment Variables
- `.env` and `.env.chromadb` must be present and filled:
  - `GEMINI_API_KEY`, `SECRET_KEY`, `CHROMA_DB_IMPL`, `CHROMA_SERVER_HOST`, `CHROMA_SERVER_PORT`, `FLASK_ENV`, etc.
- On Render.com, set all required secrets in the dashboard after deploy.

---

### Install Dependencies
- **Local:**
  - `pip install -r requirements_full.txt`
  - `cd frontend && npm install`
- **Docker/Render:**
  - Dependencies installed via `requirements-render-full.txt` in Dockerfile
  - Frontend dependencies are installed and built in the Dockerfile

---

### Frontend Build (React)
- **Node.js 16.x is required.**
- If you see errors about `ajv-keywords` or `formatMinimum`, add this to `frontend/package.json`:
  ```json
  "overrides": {
    "ajv": "8.12.0",
    "ajv-keywords": "3.5.2"
  }
  ```
- Then run:
  ```sh
  rm -rf node_modules package-lock.json
  npm install
  npm run build
  ```
- The Dockerfile will use Node 16.20.2-alpine for the build stage.

---

### Dockerfile.backend.multi (Production Docker Build)
- **Multi-stage build** with named targets (`dev` & `prod`):
- Stage 1 (`dev`): React frontend build with Node 16.20.2-alpine
- Stage 2 (`dev`): Install backend dependencies for development
- Stage 3 (`prod`): Copy only production backend code and install production dependencies
- Uses `Dockerfile.backend.multi` (target `prod`) and `requirements-render-production.txt`
- Healthcheck on `/health` port `5000`
- **.dockerignore** is required to avoid copying dev files, node_modules, etc.

---

### Starting the App
- **Local:**
  - `start-dev-full.bat`, `start-dev-full.ps1`, or `./start-dev-full.sh`
- **Docker:**
  - `deploy-docker.bat` or `./deploy-docker.sh`
- **Render.com:**
  - Uses `Dockerfile.render.full` and `requirements-render-full.txt`, healthcheck on `/health` port `10000`

---

### Health & Verification
- Health endpoint: `GET /health` on port `10000` (proxied by Nginx)
- Use `docker-compose logs -f` for troubleshooting
- Verification scripts: `A1Starter1A.*`, `verify-deployment.ps1`, etc.

---

### Production Best Practices
- **Security:**
  - All secrets in environment variables, never in code
  - Use non-root user in Docker
  - Only copy production code/assets in Dockerfile
- **Performance:**
  - Use multi-stage Docker builds
  - Use `.dockerignore` to keep images small
  - Use Gunicorn with 2-4 workers for 1 CPU
- **Monitoring:**
  - Monitor `/health` endpoint
  - Set up logging and alerts for errors
- **Scaling:**
  - For Render.com, increase `numInstances` in `render.yaml` for high availability

---

### Render.com Deployment Notes
- Render.com sets the `PORT` environment variable (default is 10000)
- The Dockerfile and docker-compose.yml are configured to use this variable
- The app will be available at `https://<your-app-name>.onrender.com` after deployment
- Make sure all required environment variables (e.g., `GEMINI_API_KEY`, `SECRET_KEY`) are set in the Render dashboard

---

### Troubleshooting
- **Frontend build fails with ajv/ajv-keywords errors:**
  - Use Node.js 16.x
  - Add the `overrides` block above to `package.json`
  - Clean and reinstall node_modules
- **Backend fails to start:**
  - Check for missing environment variables
  - Check logs for Python errors
- **502/Bad Gateway:**
  - Ensure all services are healthy and ports are mapped correctly
  - Check Nginx and backend logs

---

### Summary
- Use Node.js 16.x for all builds
- Use Dockerfile.render.full for production/Render.com
- All secrets and config in environment variables
- Healthcheck and static file serving are production-ready
- See this file for all future updates and deployment best practices
