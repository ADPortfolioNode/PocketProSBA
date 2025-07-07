# Render.com Deployment Troubleshooting Guide

This guide will help you troubleshoot deployment issues with Render.com, specifically related to port binding and health checks.

## Common Issues

### 1. Port Binding Issues

**Symptoms:**
- Application fails to start
- Health checks fail
- Error messages about port binding
- 502 Bad Gateway errors

**Solutions:**
- Ensure your Flask app is binding to `0.0.0.0` (not localhost/127.0.0.1)
- Use the PORT environment variable: `PORT = int(os.environ.get('PORT', 5000))`
- Make sure your application is listening on the correct port in all startup commands
- Ensure your Gunicorn command uses `--bind 0.0.0.0:$PORT`
- Check that the Dockerfile has the correct `EXPOSE ${PORT}` directive

### 2. Health Check Failures

**Symptoms:**
- Application deploys but is repeatedly restarted
- Messages about failed health checks in the logs

**Solutions:**
- Ensure you have a `/health` endpoint that returns a 200 OK response
- Set proper health check timeout values in render.yaml
- Verify that the health check path is correctly set in render.yaml
- Increase Gunicorn timeout if your application takes longer to respond

### 3. Application Crashes

**Symptoms:**
- Application starts but crashes shortly after
- Error messages in the logs

**Solutions:**
- Check for proper dependency installation in requirements.txt
- Ensure all required environment variables are set
- Look for Python exceptions in the logs

## Verification Steps

1. Run the `verify-render-port.ps1` script to check your local setup
2. Verify that the application binds to 0.0.0.0 and the PORT environment variable
3. Check that all endpoints are accessible, especially the health endpoint
4. Verify that Gunicorn is configured with the correct timeout and binding settings

## Debugging Tools

- `/port-debug` endpoint: Shows the current port configuration and environment variables
- `/health` endpoint: Confirms if the application is running correctly
- Render.com logs: Check for error messages
- Set `PYTHONUNBUFFERED=1` to ensure logs are immediately visible

## Render.yaml Configuration

```yaml
services:
  - type: web
    name: pocketpro-sba-backend
    runtime: python
    buildCommand: pip install --upgrade pip setuptools wheel && pip install -r requirements-render-minimal.txt
    startCommand: gunicorn --bind 0.0.0.0:$PORT --config=gunicorn.render.conf.py minimal_app:app
    envVars:
      - key: PYTHON_VERSION
        value: 3.9
      - key: FLASK_ENV
        value: production
      - key: PORT
        value: 5000
    healthCheckPath: /health
    healthCheckTimeout: 15
```

## Gunicorn Configuration

```python
# Server socket - CRITICAL for Render.com
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"

# Timeout - prevent 502 errors
timeout = 60  # Increased for Render.com
keepalive = 5
```

## Flask Application Configuration

```python
# Get PORT from environment (critical for Render.com)
PORT = int(os.environ.get('PORT', 5000))

# When run directly, use the PORT environment variable
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT, debug=False)
```

## Render.com Resource Tips

- Free tier resources are limited - keep your application lightweight
- Consider using async workers for better performance
- Keep dependencies minimal to reduce build time
- Use proper timeout settings to prevent 502 errors

## Quick Fixes

If you encounter issues, try these quick fixes:

1. **502 Bad Gateway**: Increase Gunicorn timeout in render.yaml and gunicorn.conf.py
2. **Failed Health Checks**: Verify the health endpoint and increase health check timeout
3. **Application Not Starting**: Check PORT binding and logs for Python exceptions
4. **Slow Application**: Reduce dependencies and optimize code
