# Production Deployment Guide for PocketPro:SBA on Render.com

This guide outlines the steps for deploying PocketPro:SBA to Render.com in a production environment.

## Production Configuration Files

The following files are configured specifically for production deployment:

- `render.production.yaml` - Production-ready Render blueprint 
- `Dockerfile.production` - Optimized Docker configuration
- `requirements-render-production.txt` - Production dependencies
- `Procfile.production` - Production Gunicorn configuration

## Deployment Options

You have three primary options for deploying to Render.com:

### Option 1: Standard Python Web Service (Recommended)

Uses Render's Python runtime with Gunicorn:

```bash
render blueprint render render.production.yaml
```

### Option 2: Docker-based Deployment

Uses the production Dockerfile:

```bash
render blueprint render render.docker.yaml
```

### Option 3: Manual Deployment via Dashboard

1. Log in to Render.com dashboard
2. Create a new Web Service
3. Connect your GitHub repository
4. Select "Python" runtime (or "Docker" if using Docker)
5. Use the build command:
   ```bash
   pip install --upgrade pip
   pip install --no-cache-dir -r requirements-render-production.txt
   ```
6. Use the start command: `gunicorn --bind 0.0.0.0:$PORT --timeout 60 --workers 2 --access-logfile - --error-logfile - minimal_app:app`
7. Set all environment variables as listed in `render.production.yaml`

## Production Environment Variables

| Variable | Purpose | Recommended Value |
|----------|---------|------------------|
| PORT | Application port | 5000 (set by Render) |
| FLASK_ENV | Flask environment | production |
| FLASK_APP | Flask application | minimal_app.py |
| SECRET_KEY | Security key | Generate random value |
| PYTHONUNBUFFERED | Unbuffered output | 1 |
| CORS_ORIGINS | CORS settings | * (or specific domains) |
| SENTRY_DSN | Error tracking | Your Sentry DSN |

## Health Check Configuration

The application includes a `/health` endpoint that Render will use to verify the service is running. If health checks fail, Render will restart the service.

## Scaling Considerations

The default configuration is set for the `starter` plan with 1 instance. For higher traffic:

1. Increase `numInstances` in render.yaml
2. Adjust `workers` in the Gunicorn command
3. Consider upgrading to a higher plan (standard/pro)

## Post-Deployment Verification

After deployment, verify:

1. The application is running: `https://[your-app-name].onrender.com/`
2. Health check is passing: `https://[your-app-name].onrender.com/health`
3. Logs show no errors in the Render dashboard

## Monitoring and Maintenance

1. **Logs**: Check the Render dashboard for application logs
2. **Metrics**: Monitor resource usage in the Render dashboard
3. **Updates**: Deploy updates by pushing to your GitHub repository or using the Render CLI

## Rollback Procedure

If deployment fails or introduces issues:

1. Use the Render dashboard to roll back to a previous deployment
2. Alternatively, revert your code changes and push the revert commit

## Security Considerations

1. Ensure `SECRET_KEY` is a strong, random value
2. Consider restricting `CORS_ORIGINS` to specific domains
3. Enable Render's DDoS protection
4. Set up Sentry for error monitoring

## Troubleshooting

If you encounter deployment issues:

1. Check the Render logs for error messages
2. Verify all environment variables are set correctly
3. Ensure the application binds to 0.0.0.0 and uses the PORT environment variable
4. Check if the health endpoint is responding correctly
