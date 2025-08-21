#!/bin/bash

echo "🔍 PocketPro SBA Setup Verification"
echo "=================================="

# Check for required files
echo "📋 Checking required files..."
files=(
    "backend/.env.example"
    "frontend/.env.example"
    "render.yaml"
    "docker-compose.yml"
    "Dockerfile.production"
    "Dockerfile.frontend"
    "Dockerfile.chromadb"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
    fi
done

# Check Docker configuration
echo ""
echo "🐳 Checking Docker configuration..."
docker-compose config > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Docker compose configuration is valid"
else
    echo "❌ Docker compose configuration has errors"
fi

# Check environment variables
echo ""
echo "🔧 Checking environment variables..."
if [ -f "backend/.env.example" ]; then
    echo "✅ Backend .env.example exists"
else
    echo "❌ Backend .env.example missing"
fi

if [ -f "frontend/.env.example" ]; then
    echo "✅ Frontend .env.example exists"
else
    echo "❌ Frontend .env.example missing"
fi

# Check render.yaml syntax
echo ""
echo "🚀 Checking Render configuration..."
if [ -f "render.yaml" ]; then
    echo "✅ render.yaml exists"
    # Basic YAML syntax check
    python3 -c "import yaml; yaml.safe_load(open('render.yaml'))" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ render.yaml has valid YAML syntax"
    else
        echo "❌ render.yaml has YAML syntax errors"
    fi
else
    echo "❌ render.yaml missing"
fi

echo ""
echo "🎯 Setup verification complete!"
echo ""
echo "📖 Next steps:"
echo "1. Copy backend/.env.example to backend/.env and configure your API keys"
echo "2. Copy frontend/.env.example to frontend/.env and configure your URLs"
echo "3. Run 'docker-compose up --build' for local development"
echo "4. Deploy to Render using the render.yaml blueprint"
