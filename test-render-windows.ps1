# Windows-compatible script for testing Render.com deployment
# This script works around the fcntl module issue on Windows

Write-Host "Starting Render.com compatibility test on Windows" -ForegroundColor Cyan
Write-Host "This script will help prepare your app for Render.com deployment" -ForegroundColor Cyan

# Check if gunicorn is installed
try {
    $gunicornVersion = python -m pip show gunicorn
    Write-Host "Gunicorn is installed:" -ForegroundColor Green
    Write-Host $gunicornVersion -ForegroundColor Gray
}
catch {
    Write-Host "Gunicorn is not installed. Installing it now..." -ForegroundColor Red
    python -m pip install gunicorn
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install gunicorn. Please install it manually:" -ForegroundColor Red
        Write-Host "    pip install gunicorn" -ForegroundColor Yellow
        exit 1
    }
}

# Check if Flask is installed
try {
    $flaskVersion = python -m pip show flask
    Write-Host "Flask is installed:" -ForegroundColor Green
    Write-Host $flaskVersion -ForegroundColor Gray
}
catch {
    Write-Host "Flask is not installed. Installing it now..." -ForegroundColor Red
    python -m pip install flask
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install Flask. Please install it manually:" -ForegroundColor Red
        Write-Host "    pip install flask" -ForegroundColor Yellow
        exit 1
    }
}

# Run the Windows compatibility test
Write-Host "`nRunning Render.com Windows compatibility test..." -ForegroundColor Cyan
python render_windows_compatibility.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nCompatibility test PASSED!" -ForegroundColor Green
    Write-Host "Your application is now configured for Render.com deployment" -ForegroundColor Green
    
    # Create or update WINDOWS_RENDER_NOTES.md
    $notes = @"
# Render.com Deployment Notes for Windows Users

## Windows Compatibility

Since Windows doesn't have the `fcntl` module that Gunicorn normally uses, we've created a modified configuration:

- `gunicorn_windows_render.py`: A Windows-compatible Gunicorn configuration file
- `render_windows_compatibility.py`: A test script to verify your app will work on Render.com

## Deployment Steps

1. Develop and test your application locally using Flask's development server:
   ```
   set PORT=5000
   python app.py
   ```

2. When ready to deploy to Render.com:
   - Push your code to GitHub
   - Connect your GitHub repo to Render.com
   - Use the following build command: `pip install -r requirements.txt`
   - Use the following start command: `gunicorn app:app --config=gunicorn_windows_render.py`

3. Render.com will automatically:
   - Set the PORT environment variable
   - Run your application using Gunicorn
   - Make your app available at your Render.com URL

## Troubleshooting

If you encounter issues on Render.com:

1. Check the Render logs for any error messages
2. Verify that your application is listening on the correct port
3. Make sure all required dependencies are in your requirements.txt file
4. Confirm that your Procfile is correctly formatted

Remember: Even though you develop on Windows, your app will run on a Linux environment on Render.com.
"@

    Set-Content -Path "WINDOWS_RENDER_NOTES.md" -Value $notes
    Write-Host "`nCreated WINDOWS_RENDER_NOTES.md with deployment instructions" -ForegroundColor Cyan
    
    # Optionally, run the Flask app directly for testing
    $runDirectly = Read-Host "Would you like to test the Flask app directly? (y/n)"
    if ($runDirectly -eq "y") {
        Write-Host "`nStarting Flask app directly for testing..." -ForegroundColor Yellow
        Write-Host "Press Ctrl+C to stop the application" -ForegroundColor Yellow
        
        # Set the PORT environment variable
        $env:PORT = "5000"
        
        # Run the Flask app
        python app.py
    } else {
        Write-Host "`nTo test your application locally, run:" -ForegroundColor Yellow
        Write-Host "    set PORT=5000" -ForegroundColor Gray
        Write-Host "    python app.py" -ForegroundColor Gray
    }
} else {
    Write-Host "`nCompatibility test FAILED!" -ForegroundColor Red
    Write-Host "Please fix the issues before deploying to Render.com" -ForegroundColor Red
}
