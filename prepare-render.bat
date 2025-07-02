@echo off
echo 🚀 Preparing PocketPro:SBA for Render deployment...

echo 🐍 Python version:
python --version

echo 🔧 Testing application health...
python health_check_render.py

echo.
echo 📋 Render Deployment Checklist:
echo 1. ✅ Create a new Web Service on Render
echo 2. ✅ Connect your GitHub repository  
echo 3. ✅ Set runtime to 'Python'
echo 4. ✅ Build command: pip install -r requirements.txt
echo 5. ✅ Start command: gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 run:app
echo 6. ⚠️  Add environment variable: GEMINI_API_KEY
echo 7. ✅ Deploy!
echo.
echo 🌐 Your app will be available at: https://your-service-name.onrender.com
