# Render.com Deployment Checklist

## Port and Binding Configuration

- [x] All applications bind to `0.0.0.0` to accept external connections
- [x] All port references use environment variable: `PORT` (defaulting to 5000)
- [x] No hardcoded references to port 10000 in deployment files
- [x] Gunicorn properly configured to bind to `0.0.0.0:$PORT`

## Health Checks

- [x] `/health` endpoint implemented in app.py
- [x] Health check configured in render.yaml with appropriate timeout
- [x] Health check in Dockerfile matches render.yaml configuration

## Docker Configuration

- [x] Dockerfile uses `app:app` as the WSGI application
- [x] Dockerfile exposes the correct port (PORT/5000)
- [x] docker-compose files updated to use port 5000 consistently

## Render.yaml Configuration

- [x] Uses Python runtime or Docker environment as appropriate
- [x] Correct build command: `pip install -r requirements.txt`
- [x] Correct start command: `gunicorn app:app --bind=0.0.0.0:$PORT`
- [x] Proper environment variables set (PORT, FLASK_APP, etc.)
- [x] Health check path configured (`/health`)

## Application Code

- [x] app.py configured to listen on `0.0.0.0` and use PORT environment variable
- [x] wsgi.py updated to use port 5000 as default
- [x] gunicorn config files updated to use port 5000

## Requirements

- [x] All necessary dependencies included in requirements.txt
- [x] No conflicting or unnecessary dependencies

## Frontend Configuration

- [x] Frontend built with correct backend URL
- [x] Static assets properly configured for production

## Deployment Process

1. Push all changes to the repository
2. Verify no port 10000 references remain in deployment files
3. Deploy to Render.com
4. Monitor health checks and logs for any issues
5. Verify application is accessible at the Render.com URL

## Common Issues and Solutions

- If deployment fails with a timeout, check the health check path and timeout settings
- If application shows 502 errors, ensure the application is binding to 0.0.0.0:$PORT
- If application crashes on startup, check the logs for any missing dependencies
