#!/bin/bash
# Render.com deployment preparation script

echo "🚀 Preparing PocketPro:SBA for Render deployment..."

# Check Python version
python_version=$(python3 --version 2>&1)
echo "🐍 Python version: $python_version"

# Check if we have the required files
required_files=("requirements.txt" "run.py" "app.py" "render.yaml")
for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ Found: $file"
    else
        echo "❌ Missing: $file"
        exit 1
    fi
done

# Test requirements installation
echo "🔧 Testing requirements installation..."
if python3 -m pip install --dry-run -r requirements.txt > /dev/null 2>&1; then
    echo "✅ Requirements check passed"
else
    echo "❌ Requirements check failed"
    echo "🔍 Checking for conflicts..."
    python3 -m pip check
fi

# Test import of main application
echo "🧪 Testing application imports..."
export FLASK_ENV=production
export PYTHONPATH=$PWD/src:$PWD

if python3 -c "import run; print('✅ Application imports successfully')" 2>/dev/null; then
    echo "✅ Import test passed"
else
    echo "⚠️  Import test failed, but fallback should work"
fi

# Check environment variables
echo "🔍 Environment check:"
if [[ -z "$GEMINI_API_KEY" ]]; then
    echo "⚠️  GEMINI_API_KEY not set (required for production)"
else
    echo "✅ GEMINI_API_KEY is set"
fi

echo ""
echo "📋 Render Deployment Checklist:"
echo "1. ✅ Create a new Web Service on Render"
echo "2. ✅ Connect your GitHub repository"
echo "3. ✅ Set runtime to 'Python'"
echo "4. ✅ Build command: 'pip install -r requirements.txt'"
echo "5. ✅ Start command: 'gunicorn --bind 0.0.0.0:\$PORT --workers 1 --timeout 120 run:app'"
echo "6. ⚠️  Add environment variable: GEMINI_API_KEY"
echo "7. ✅ Deploy!"
echo ""
echo "🎯 Your app will be available at: https://your-service-name.onrender.com"
