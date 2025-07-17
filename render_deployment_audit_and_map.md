# Render Deployment Audit and Shared Deployment Map

## 1. Service Audit

### Service: Production Backend
- **Docker Path:** Dockerfile.production
- **Build Command:** `docker build -f Dockerfile.production .`
- **Start Command:**  
  `gunicorn --bind 0.0.0.0:${PORT} --timeout 60 --workers 2 --access-logfile - --error-logfile - --log-level info app_full:app`
- **Environment Variables:**  
  - PORT=5000  
  - FLASK_ENV=production  
  - FLASK_APP=app.py  
  - PYTHONUNBUFFERED=1  
  - PYTHONDONTWRITEBYTECODE=1  
- **Git Path:** Not specified

---

### Service: Render Full Backend
- **Docker Path:** Dockerfile.render.full
- **Build Command:** `docker build -f Dockerfile.render.full .`
- **Start Command:**  
  `gunicorn --bind 0.0.0.0:${PORT} --workers=1 --timeout=120 app_full:app`
- **Environment Variables:**  
  - PORT=5000  
  - FLASK_ENV=production  
  - FLASK_APP=app_full.py  
  - PYTHONUNBUFFERED=1  
- **Git Path:** Not specified

---

### Service: Frontend Render
- **Docker Path:** Dockerfile.frontend.render
- **Build Command:**  
  - Stage 1 (build):  
    `npm install` and `npm run build` in frontend directory  
  - Stage 2 (production): Nginx serves built app
- **Start Command:** Entrypoint script `/usr/local/bin/entrypoint.sh` which starts Nginx
- **Environment Variables (build time):**  
  - CI=true  
  - ESLINT_NO_DEV_ERRORS=true  
  - NODE_OPTIONS=--max-old-space-size=4096  
- **Exposed Port:** 80
- **Git Path:** Not specified

---

### Service: Render Compose Web (Frontend)
- **Docker Path:** Dockerfile.frontend.render
- **Build Context:** `.`
- **Ports:** 10000:80
- **Depends On:** backend
- **Environment Variables:**  
  - BACKEND_URL=backend:$PORT

---

### Service: Render Compose Backend
- **Docker Path:** Dockerfile.render.full
- **Image:** pocketpro-sba-backend
- **Container Name:** pocketpro-sba-backend
- **Environment Variables:**  
  - PORT  
  - FLASK_ENV=production  
  - FLASK_APP=app_full.py  
- **Start Command:**  
  `/bin/sh -c "gunicorn --bind 0.0.0.0:$PORT --timeout 60 app_full:app"`

---

### Service: Production Compose - ChromaDB
- **Image:** chromadb/chroma:latest
- **Ports:** 8000:8000
- **Environment Variables:**  
  - CHROMA_HOST=0.0.0.0  
  - CHROMA_PORT=8000  
  - CHROMA_SERVER_AUTHN_CREDENTIALS_FILE=/chroma/auth.txt  
  - CHROMA_SERVER_AUTHN_PROVIDER=chromadb.auth.basic.BasicAuthenticationServerProvider

---

### Service: Production Compose Backend
- **Docker Path:** Dockerfile.backend.prod
- **Build Context:** `.`
- **Ports:** 5000:5000
- **Environment Variables:**  
  - FLASK_ENV=production  
  - FLASK_APP=run.py  
  - GEMINI_API_KEY=${GEMINI_API_KEY}  
  - SECRET_KEY=${SECRET_KEY:-default_secret_key_change_in_production}  
  - CHROMA_HOST=chromadb  
  - CHROMA_PORT=8000  
  - CORS_ORIGINS=*  
- **Volumes:** app_uploads, app_logs
- **Start Command:**  
  `gunicorn --bind 0.0.0.0:5000 run:app`

---

### Service: Production Compose Frontend
- **Docker Path:** Dockerfile.frontend.prod
- **Build Context:** `.`
- **Ports:** 80:80
- **Environment Variables:**  
  - BACKEND_URL=http://backend:5000  
- **Build Args:**  
  - REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL:-http://localhost:5000}
- **Depends On:** backend
- **Start Command:** Default CMD in Dockerfile.frontend.prod (not explicitly read)

---

## 2. Shared Deployment Map

| Service Name           | Docker Path              | Build Command                          | Start Command                                         | Environment Variables                         | Git Path |
|-----------------------|--------------------------|--------------------------------------|-------------------------------------------------------|----------------------------------------------|----------|
| Production Backend     | Dockerfile.production    | docker build -f Dockerfile.production . | gunicorn --bind 0.0.0.0:${PORT} --timeout 60 --workers 2 app_full:app | PORT=5000, FLASK_ENV=production, FLASK_APP=app.py, PYTHONUNBUFFERED=1, PYTHONDONTWRITEBYTECODE=1 | N/A      |
| Render Full Backend    | Dockerfile.render.full   | docker build -f Dockerfile.render.full . | gunicorn --bind 0.0.0.0:${PORT} --workers=1 --timeout=120 app_full:app | PORT=5000, FLASK_ENV=production, FLASK_APP=app_full.py, PYTHONUNBUFFERED=1 | N/A      |
| Frontend Render       | Dockerfile.frontend.render | npm install & npm run build (frontend) + Nginx | Entrypoint script /usr/local/bin/entrypoint.sh (starts Nginx) | CI=true, ESLINT_NO_DEV_ERRORS=true, NODE_OPTIONS=--max-old-space-size=4096 | N/A      |
| Render Compose Web    | Dockerfile.frontend.render | docker-compose build (context: .)    | Nginx on port 80 (mapped to 10000)                    | BACKEND_URL=backend:$PORT                     | N/A      |
| Render Compose Backend | Dockerfile.render.full   | docker-compose build (context: .)    | gunicorn --bind 0.0.0.0:$PORT --timeout 60 app_full:app | PORT, FLASK_ENV=production, FLASK_APP=app_full.py | N/A      |
| Production Compose ChromaDB | chromadb/chroma:latest | N/A (pull image)                     | Default container start                                | CHROMA_HOST=0.0.0.0, CHROMA_PORT=8000, CHROMA_SERVER_AUTHN_CREDENTIALS_FILE, CHROMA_SERVER_AUTHN_PROVIDER | N/A      |
| Production Compose Backend | Dockerfile.backend.prod | docker-compose build (context: .)    | gunicorn --bind 0.0.0.0:5000 run:app                  | FLASK_ENV=production, FLASK_APP=run.py, GEMINI_API_KEY, SECRET_KEY, CHROMA_HOST, CHROMA_PORT, CORS_ORIGINS | N/A      |
| Production Compose Frontend | Dockerfile.frontend.prod | docker-compose build (context: .)    | Default CMD (not explicitly read)                      | BACKEND_URL=http://backend:5000              | N/A      |

---

This audit consolidates the key deployment details for each service related to Render.com deployments.

If you want, I can also extract and include any git repository links if you provide where they might be stored or referenced.
