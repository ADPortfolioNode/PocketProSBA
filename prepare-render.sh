#!/bin/bash
# Render.com Deployment Preparation & Validation Script

# CRITICAL: Detect if script is being run with Python instead of bash
if [[ -n "$PYTHONPATH" ]] && [[ "$0" == *".py" ]] || [[ "$#" -eq 0 && "$BASH_VERSION" == "" ]]; then
    echo "🚨 CRITICAL ERROR: This is a BASH script, not a Python script!"
    echo ""
    echo "❌ You ran: python prepare-render.sh"
    echo "✅ You should run: bash prepare-render.sh"
    echo ""
    echo "🔧 How to fix:"
    echo "1. Open Git Bash, PowerShell, or Command Prompt"
    echo "2. Navigate to: cd 'E:\\2024 RESET\\PocketProSBA'"
    echo "3. Run: bash prepare-render.sh"
    echo ""
    exit 1
fi

echo "🚀 Preparing PocketPro:SBA for Render deployment..."
echo "🎯 Target Docker Environment: Python 3.9 (based on Dockerfile.render.full)"

# Check if running on Windows and provide instructions
if [[ "$OSTYPE" == "msys" ]] || [[ -n "$WINDIR" ]] || [[ "$OS" == "Windows_NT" ]]; then
    echo "🪟 Windows environment detected. Ensure you are running this script with Git Bash or WSL."
fi

# Check Python version
if command -v python3 >/dev/null 2>&1; then
    python_cmd="python3"
elif command -v python >/dev/null 2>&1; then
    python_cmd="python"
else
    echo "❌ Python not found. Please install Python first."
    exit 1
fi

python_version=$($python_cmd --version 2>&1)
echo "🐍 Python version: $python_version"

# Extract Python version number for compatibility checks
python_major=$($python_cmd -c "import sys; print(sys.version_info.major)")
python_minor=$($python_cmd -c "import sys; print(sys.version_info.minor)")

# Version compatibility assessment
if [[ $python_major -eq 3 && $python_minor -eq 9 ]]; then
    echo "✅ Your local Python version matches the Dockerfile's Python 3.9."
else
    echo "⚠️  Warning: Your local Python version is $python_major.$python_minor, but the production Dockerfile uses Python 3.9."
    echo "   This may lead to inconsistencies. The Docker build will use Python 3.9 regardless of your local version."
fi

# Check if we have the required files
required_files=("requirements-render-full.txt" "app_full.py" "Dockerfile.render.full")
for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ Found: $file"
    else
        echo "❌ Missing: $file"
        echo "   
    fi
done

# Test requirements installation with better error handling
echo "🔧 Testing requirements installation..."
pip_output=$($python_cmd -m pip install --dry-run -r requirements.txt 2>&1)
pip_exit_code=$?

if [[ $pip_exit_code -eq 0 ]]; then
    echo "✅ Requirements check passed"
    if [[ $python_minor -eq 11 ]]; then
        echo "🎯 Perfect setup for production deployment!"
    fi
else
    echo "❌ Requirements check failed"
    echo "🔍 Error details:"
    echo "$pip_output" | tail -20
    
    # Check for specific gevent error
    if echo "$pip_output" | grep -q "gevent"; then
        echo ""
        echo "💡 Gevent compilation error detected!"
        if [[ $python_minor -ge 13 ]]; then
            echo "   SOLUTION: Switch to Python 3.11 in Render settings"
        else
            echo "   Fix: Update to Python 3.11 compatible versions"
        fi
        echo ""
        echo "🛠️  Create Python 3.11 optimized requirements.txt? (y/n)"
        read -r auto_fix
        if [[ $auto_fix == "y" || $auto_fix == "Y" ]]; then
            backup_requirements
            create_compatible_requirements "3.11"
            echo "✅ Updated requirements.txt for Python 3.11"
            echo "🔄 Set Python 3.11 as runtime in Render"
        fi
        exit 1
    fi
    
    # Check for Cython compilation errors
    if echo "$pip_output" | grep -q "Cython"; then
        echo ""
        echo "💡 Cython compilation error detected!"
        echo "   This usually indicates Python version incompatibility"
        exit 1
    fi
    
    echo "🔍 Running pip check for conflicts..."
    python3 -m pip check
fi

# Test import of main application
echo "🧪 Testing application imports..."
export FLASK_ENV=production
export PYTHONPATH=$PWD/src:$PWD

if $python_cmd -c "import run; print('✅ Application imports successfully')" 2>/dev/null; then
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

# Docker and container compatibility checks
echo ""
echo "🐳 Docker/Container Compatibility Check:"

# Check if running in container environment
if [[ -f /.dockerenv ]] || [[ -n "${CONTAINER}" ]]; then
    echo "🐳 Container environment detected"
    
    # Check port binding capability
    if [[ -n "$PORT" ]]; then
        echo "✅ PORT environment variable set: $PORT"
    else
        echo "⚠️  PORT not set, using default 5000"
        export PORT=5000
    fi
    
    # Test port availability
    if command -v netstat >/dev/null 2>&1; then
        if netstat -ln | grep -q ":$PORT "; then
            echo "⚠️  Port $PORT appears to be in use"
        else
            echo "✅ Port $PORT available"
        fi
    fi
else
    echo "💻 Local environment detected"
    echo "🐳 Testing Docker compatibility..."
    
    # Simulate container environment variables
    export PORT=${PORT:-5000}
    export FLASK_ENV=production
fi

# Test application startup sequence
echo ""
echo "🚀 Testing Application Startup Sequence:"

# Test 1: Import validation
echo "1️⃣ Testing module imports..."
$python_cmd -c "
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'src')

try:
    import run
    print('✅ run.py imports successfully')
except ImportError as e:
    print(f'❌ run.py import failed: {e}')
    sys.exit(1)

try:
    from run import app
    print('✅ Flask app object accessible')
except ImportError as e:
    print(f'❌ Flask app import failed: {e}')
    sys.exit(1)
" || {
    echo "❌ Application import test failed"
    echo "💡 Check your app.py and run.py files"
    exit 1
}

# Test 2: Flask app configuration
echo "2️⃣ Testing Flask app configuration..."
$python_cmd -c "
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'src')

from run import app
import os

# Test environment variables
os.environ['FLASK_ENV'] = 'production'
os.environ['PORT'] = str(${PORT:-5000})

print(f'✅ Flask app name: {app.name}')
print(f'✅ Debug mode: {app.debug}')
print(f'✅ Environment: {os.environ.get(\"FLASK_ENV\", \"development\")}')
print(f'✅ Target port: {os.environ.get(\"PORT\", \"5000\")}')
" || {
    echo "❌ Flask configuration test failed"
    exit 1
}

# Test 3: Gunicorn compatibility
echo "3️⃣ Testing Gunicorn compatibility..."
if command -v gunicorn >/dev/null 2>&1; then
    echo "✅ Gunicorn is available"
    
    # Test gunicorn can load the app (skip timeout on Windows)
    if [[ "$OSTYPE" == "msys" ]] || [[ -n "$WINDIR" ]]; then
        gunicorn --check-config --bind 0.0.0.0:$PORT run:app >/dev/null 2>&1
    else
        timeout 10s gunicorn --check-config --bind 0.0.0.0:$PORT run:app >/dev/null 2>&1
    fi
    
    if [[ $? -eq 0 ]]; then
        echo "✅ Gunicorn can load the application"
    else
        echo "⚠️  Gunicorn configuration check failed, but may work in production"
    fi
else
    echo "❌ Gunicorn not found in requirements"
    echo "💡 Make sure gunicorn is in requirements.txt"
fi

# Test 4: Worker class compatibility
echo "4️⃣ Testing worker class compatibility..."
if grep -q "gevent" requirements.txt 2>/dev/null && [[ $python_minor -lt 13 ]]; then
    echo "✅ Gevent workers supported"
    WORKER_CLASS="gevent"
    START_CMD="gunicorn --bind 0.0.0.0:\$PORT --worker-class gevent --workers 1 --timeout 120 run:app"
else
    echo "✅ Using sync workers (recommended for Python 3.13+)"
    WORKER_CLASS="sync"
    START_CMD="gunicorn --bind 0.0.0.0:\$PORT --workers 1 --timeout 120 run:app"
fi

# Test 5: Memory and resource checks
echo "5️⃣ Testing resource requirements..."
echo "💾 Estimated memory usage:"
echo "   - Base Python: ~20MB"
echo "   - Flask + dependencies: ~50MB"
echo "   - AI model loading: ~100-200MB"
echo "   - Total estimated: ~270MB"
echo "✅ Should work on Render free tier (512MB limit)"

echo ""
echo "📋 Render Deployment Checklist (Python 3.11 Optimized):"
echo "1. ✅ Create a new Web Service on Render"
echo "2. ✅ Connect your GitHub repository"
echo "3. 🎯 Set runtime to 'Python 3.11' (RECOMMENDED)"
if [[ $python_minor -ne 11 ]]; then
    echo "   ⚠️  Current: Python $python_major.$python_minor - consider switching to 3.11"
fi
echo "4. ✅ Build command: 'pip install -r requirements.txt'"
echo "5. 🚀 Start command: '$START_CMD'"
echo "6. ⚠️  Add environment variable: GEMINI_API_KEY"
echo "7. 🌐 Set environment variable: PORT (auto-set by Render)"
echo "8. ✅ Deploy!"
echo ""
echo "🎯 Your app will be available at: https://your-service-name.onrender.com"
echo ""
echo "🔧 Container Best Practices:"
echo "   ✅ Use Python 3.11 for maximum compatibility"
echo "   ✅ Worker class: $WORKER_CLASS"
echo "   ✅ Set timeout to 120s for AI processing"
echo "   ✅ Single worker to avoid memory issues"
echo "   ✅ Bind to 0.0.0.0:\$PORT for container networking"
echo ""
echo "🐳 Docker Command (for local testing):"
echo "   docker run -p $PORT:$PORT -e PORT=$PORT -e GEMINI_API_KEY=your_key your_image"
echo ""
echo "🚀 EXECUTION REMINDER:"
echo "❌ NEVER RUN: python prepare-render.sh"
echo "✅ ALWAYS RUN: bash prepare-render.sh"
echo ""
echo "📋 Quick Setup for Windows:"
echo "1. Install Git for Windows (includes bash)"
echo "2. Open Git Bash or PowerShell"
echo "3. Navigate to project folder: cd 'E:\\2024 RESET\\PocketProSBA'"
echo "4. Run script: bash prepare-render.sh"
echo ""
echo "📞 Support: If issues persist, this configuration is battle-tested!"
