# Windows Development Guide for PocketPro:SBA

This guide explains how to develop and test PocketPro:SBA on Windows, since Gunicorn (used on Render.com) is not compatible with Windows.

## The Gunicorn Windows Compatibility Issue

Gunicorn relies on Unix-specific features (specifically the `fcntl` module) that aren't available on Windows:

```
ModuleNotFoundError: No module named 'fcntl'
```

## Solution: Use Flask's Built-in Server for Local Development

For Windows development, we'll use Flask's built-in development server instead of Gunicorn. This allows us to:

1. Develop and test on Windows
2. Maintain compatibility with Render.com deployment (which uses Gunicorn)

## How to Run the Application on Windows

### Option 1: Using the batch file

1. Run the provided batch file:
   ```
   run-windows.bat
   ```

### Option 2: Using the PowerShell script

1. Run the PowerShell script:
   ```powershell
   .\start-and-verify-windows.ps1
   ```
   This will:
   - Start the Flask app in a new window
   - Run the verification script
   - Show you if everything is working correctly

### Option 3: Manual setup

1. Set the environment variables:
   ```powershell
   $env:PORT = 5000
   $env:FLASK_ENV = "development"
   $env:FLASK_APP = "minimal_app.py"
   ```

2. Run the Windows-compatible script:
   ```powershell
   python run_windows.py
   ```

## How to Verify the Application

Run the verification script in a separate terminal:
```powershell
python verify_render_port.py
```

This will check:
- If the application is bound to port 5000
- If the health endpoint is responding
- If the port-debug endpoint is responding

## Testing the Application

Once running, you can test the application at:

- http://localhost:5000/ - Main endpoint
- http://localhost:5000/health - Health check
- http://localhost:5000/port-debug - Port and environment details

## Deployment to Render.com

When deploying to Render.com:

1. The application will use Gunicorn (as specified in render.yaml)
2. No changes are needed to the deployment configuration
3. The Windows-specific files are only for local development

## Troubleshooting

If the `/port-debug` endpoint returns a 404 error:
1. Make sure you're running the latest version of minimal_app.py
2. Restart the Flask server completely
3. Check if the endpoint is defined in minimal_app.py

If you encounter other issues:
1. Check the console output for error messages
2. Verify all environment variables are set correctly
3. Make sure no other application is using port 5000
