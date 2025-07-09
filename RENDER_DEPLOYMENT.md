# Render.com Deployment Configuration

This document outlines the specific configurations for deploying the PocketPro SBA application on Render.com.

## Port Configuration

The critical aspect of deploying to Render.com is proper port binding. Render sets a `PORT` environment variable and expects your application to listen on that port.

### Key Changes Made:

1. **Procfile Update**:
   - Changed to use a platform-specific configuration file
   - For Linux/MacOS: `web: gunicorn app:app --config=gunicorn_render_fixed.py`
   - For Windows development: `web: gunicorn app:app --config=gunicorn_windows_render.py`

2. **Gunicorn Configuration**:
   - Using configuration files that properly read the PORT environment variable
   - Ensures correct port binding with `bind = f"0.0.0.0:{port}"`
   - Converts PORT to integer to avoid type issues

3. **Frontend Connectivity**:
   - Updated to try multiple health endpoints for better compatibility
   - Uses relative URLs to avoid hardcoded backend addresses
   - Improved error handling to work in various deployment scenarios

## Windows-Specific Considerations

When developing on Windows and deploying to Render.com (which uses Linux), there are additional considerations:

1. **Module Compatibility**:
   - The `fcntl` module is not available on Windows but is used by Gunicorn
   - We've created `gunicorn_windows_render.py` which works around this limitation

2. **Testing on Windows**:
   - Use `render_windows_compatibility.py` to test your configuration
   - Run `test-render-windows.ps1` for a complete compatibility check

3. **Local Development on Windows**:
   - For testing, use Flask's built-in server: `python app.py`
   - Set the PORT environment variable: `set PORT=5000`

## Common Issues and Solutions

### Port Binding Error
If you see this error in Render logs:
```
==> Continuing to scan for open port 5000 (from PORT environment variable)...
==> Port scan timeout reached, failed to detect open port 5000 from PORT environment variable.
```

This means your application is not binding to the expected port. Check:
1. The Procfile is using the correct gunicorn configuration
2. The gunicorn configuration is correctly reading and using the PORT environment variable
3. The application isn't overriding the port setting elsewhere

### CORS Issues
For CORS errors between frontend and backend:
1. Ensure the backend has CORS properly configured
2. Use relative URLs in the frontend
3. Verify Nginx or other proxies are correctly configured

## Testing Deployment
Before pushing to Render, test locally with:

**On Linux/macOS:**
```
PORT=5000 gunicorn app:app --config=gunicorn_render_fixed.py
```

**On Windows:**
```
set PORT=5000
python render_windows_compatibility.py
```

This simulates how Render will run your application.
