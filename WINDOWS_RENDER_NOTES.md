# Render.com Deployment Notes for Windows Users

## Windows Compatibility

Since Windows doesn't have the cntl module that Gunicorn normally uses, we've created a modified configuration:

- gunicorn_windows_render.py: A Windows-compatible Gunicorn configuration file
- ender_windows_compatibility.py: A test script to verify your app will work on Render.com

## Deployment Steps

1. Develop and test your application locally using Flask's development server:
   `
   set PORT=5000
   python app.py
   `

2. When ready to deploy to Render.com:
   - Push your code to GitHub
   - Connect your GitHub repo to Render.com
   - Use the following build command: pip install -r requirements.txt
   - Use the following start command: gunicorn app:app --config=gunicorn_windows_render.py

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
