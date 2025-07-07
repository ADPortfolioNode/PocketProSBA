# Render.com Port Binding Fix

## The Issue

Our Render.com deployment was failing because Gunicorn was binding to port 10000 instead of port 5000 (the port expected by Render.com). The logs showed:

```
[2025-07-07 15:23:38 +0000] [109] [INFO] Listening at: http://0.0.0.0:10000 (109)
...
==> Continuing to scan for open port 5000 (from PORT environment variable)...
==> Port scan timeout reached, failed to detect open port 5000 from PORT environment variable. Bind your service to port 5000 or update the PORT environment variable to the correct port.
```

## The Solution

We implemented several fixes to ensure proper port binding:

1. **Custom Startup Script**: Created `run_on_render.sh` that explicitly sets the port binding through environment variables before starting Gunicorn.

2. **Fixed Gunicorn Configuration**: Created a special `gunicorn_render_fixed.py` configuration that:
   - Explicitly logs the PORT environment variable at startup
   - Forces binding to `0.0.0.0:$PORT`
   - Adds diagnostic hooks to provide detailed logging

3. **Enhanced Logging**: Added additional logging in `app.py` to track port-related environment variables.

4. **Debugging Tools**: Added `debug_port_binding.py` to diagnose port binding issues.

5. **Updated Dockerfile**: Ensured consistent behavior in Docker deployments.

6. **Updated render.yaml**: Changed to use our custom startup script.

## How It Works

When Render.com deploys the application:

1. `run_on_render.sh` runs and logs all environment variables
2. The script then starts Gunicorn with our fixed configuration
3. The `gunicorn_render_fixed.py` configuration ensures proper port binding
4. Additional logging helps diagnose any remaining issues

## Testing the Fix

To verify the fix works:

1. Deploy to Render.com
2. Check the logs to ensure Gunicorn is binding to the correct port (5000)
3. Verify the health check endpoint is accessible
4. Verify the application is running correctly

## Further Considerations

If the issue persists, check:

1. If there are any gunicorn plugins/modules loaded that override the binding
2. If there are any hooks in the application that modify the port binding
3. If there are any environment variables set that conflict with our port configuration
