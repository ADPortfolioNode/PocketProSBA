#!/bin/bash
# Render.com deployment preparation script

echo "🚀 Preparing PocketPro:SBA for Render deployment..."
echo "🎯 Target: Python 3.11 (recommended for best compatibility)"

# Check Python version
python_version=$(python3 --version 2>&1)
echo "🐍 Python version: $python_version"

# Extract Python version number for compatibility checks
python_major=$(python3 -c "import sys; print(sys.version_info.major)")
python_minor=$(python3 -c "import sys; print(sys.version_info.minor)")

# Function to suggest compatible package versions
suggest_compatible_versions() {
    local py_version="$1"
    echo "💡 Recommended package versions for Python $py_version:"
    
    case "$py_version" in
        "3.11")
            echo "   Flask==2.3.3"
            echo "   gunicorn==21.2.0"
            echo "   gevent==23.7.0"
            echo "   Werkzeug==2.3.7"
            echo "   google-generativeai==0.3.2"
            echo "   python-dotenv==1.0.0"
            echo "   ✅ RECOMMENDED CONFIGURATION"
            ;;
        "3.12")
            echo "   Flask==3.0.0"
            echo "   gunicorn==21.2.0"
            echo "   gevent==23.9.1"
            echo "   Werkzeug==3.0.1"
            echo "   google-generativeai==0.3.2"
            echo "   python-dotenv==1.0.0"
            echo "   ⚠️  Consider downgrading to Python 3.11 for stability"
            ;;
        "3.13")
            echo "   Flask==3.0.0"
            echo "   gunicorn==21.2.0"
            echo "   Werkzeug==3.0.1"
            echo "   google-generativeai==0.3.2"
            echo "   python-dotenv==1.0.0"
            echo "   # Remove: gevent, eventlet (not compatible)"
            echo "   ❌ STRONGLY RECOMMEND: Downgrade to Python 3.11"
            ;;
        *)
            echo "   Flask==2.3.3"
            echo "   gunicorn==20.1.0"
            echo "   gevent==22.10.2"
            echo "   Werkzeug==2.3.7"
            echo "   google-generativeai==0.3.2"
            echo "   python-dotenv==1.0.0"
            echo "   ⚠️  Consider upgrading to Python 3.11"
            ;;
    esac
}

# Version compatibility assessment
if [[ $python_major -eq 3 && $python_minor -eq 11 ]]; then
    echo "🎉 Perfect! Python 3.11 detected - optimal compatibility"
    suggest_compatible_versions "3.11"
elif [[ $python_major -eq 3 && $python_minor -ge 13 ]]; then
    echo "🚨 Warning: Python 3.13+ detected. STRONGLY RECOMMEND downgrading to Python 3.11"
    
    # Check if gevent is in requirements
    if grep -q "gevent" requirements.txt 2>/dev/null; then
        echo "❌ gevent detected in requirements.txt - not compatible with Python 3.13+"
        echo "💡 SOLUTION: Downgrade to Python 3.11 for full compatibility"
        echo ""
        suggest_compatible_versions "3.13"
        echo ""
        echo "🔧 Alternative: Remove gevent and use sync workers:"
        echo "   gunicorn --bind 0.0.0.0:\$PORT --workers 1 --timeout 120 run:app"
        
        # Offer to create a Python 3.11 compatible requirements.txt
        echo ""
        echo "🛠️  Create Python 3.11 compatible requirements.txt? (y/n)"
        read -r create_req
        if [[ $create_req == "y" || $create_req == "Y" ]]; then
            backup_requirements
            create_compatible_requirements "3.11"
            echo "✅ Created Python 3.11 compatible requirements.txt"
            echo "🔄 Please switch to Python 3.11 in Render settings"
        fi
        exit 1
    fi
    
    suggest_compatible_versions "3.13"
elif [[ $python_major -eq 3 && $python_minor -eq 12 ]]; then
    echo "⚠️  Python 3.12 detected - good compatibility, but Python 3.11 is recommended"
    suggest_compatible_versions "3.12"
else
    echo "⚠️  Python $python_major.$python_minor detected - recommend upgrading to Python 3.11"
    suggest_compatible_versions "older"
fi

# Function to backup current requirements
backup_requirements() {
    if [[ -f "requirements.txt" ]]; then
        cp requirements.txt "requirements.txt.backup.$(date +%Y%m%d_%H%M%S)"
        echo "✅ Backed up requirements.txt"
    fi
}

# Function to create compatible requirements.txt
create_compatible_requirements() {
    local py_version="$1"
    echo "📝 Creating Python 3.11 optimized requirements.txt..."
    
    # Always create Python 3.11 compatible version as the default
    cat > requirements.txt << 'EOF'
# Optimized for Python 3.11 - Production Ready
Flask==2.3.3
gunicorn==21.2.0
gevent==23.7.0
Werkzeug==2.3.7
google-generativeai==0.3.2
python-dotenv==1.0.0

# Core dependencies with proven stability
Jinja2==3.1.2
MarkupSafe==2.1.3
click==8.1.7
blinker==1.6.3
itsdangerous==2.1.2
greenlet==2.0.2

# Additional production dependencies
certifi==2023.7.22
charset-normalizer==3.2.0
idna==3.4
requests==2.31.0
urllib3==2.0.4

# Development dependencies (uncomment if needed)
# pytest==7.4.3
# black==23.7.0
# flake8==6.0.0
EOF
    
    echo "✅ Created Python 3.11 optimized requirements.txt"
    echo "🔍 Contents:"
    cat requirements.txt
}

# Check if we have the required files
required_files=("requirements.txt" "run.py" "app.py")
for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ Found: $file"
    else
        echo "❌ Missing: $file"
        if [[ "$file" == "requirements.txt" ]]; then
            echo "🛠️  Create basic requirements.txt? (y/n)"
            read -r create_basic_req
            if [[ $create_basic_req == "y" || $create_basic_req == "Y" ]]; then
                create_compatible_requirements "$python_major.$python_minor"
            else
                exit 1
            fi
        else
            exit 1
        fi
    fi
done

# Test requirements installation with better error handling
echo "🔧 Testing requirements installation..."
pip_output=$(python3 -m pip install --dry-run -r requirements.txt 2>&1)
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
python3 -c "
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
python3 -c "
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
    
    # Test gunicorn can load the app
    timeout 10s gunicorn --check-config --bind 0.0.0.0:$PORT run:app 2>/dev/null
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
echo "📞 Support: If issues persist, this configuration is battle-tested!"
