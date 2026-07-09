#!/bin/bash

echo "PocketPro SBA Docker Setup Verification"
echo "====================================="

echo "Checking required files..."
files=(
    ".env.example"
    "backend/.env.example"
    "frontend/.env.example"
    "docker-compose.yml"
    "docker-compose.dev.yml"
    "Dockerfile.production"
    "Dockerfile.frontend"
    "Dockerfile.chromadb"
    "Dockerfile.dev"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "[ok] $file exists"
    else
        echo "[missing] $file"
    fi
done

echo ""
echo "Checking Docker Compose configuration..."
docker compose config > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "[ok] docker-compose.yml is valid"
else
    echo "[error] docker-compose.yml has errors"
fi

docker compose -f docker-compose.dev.yml config > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "[ok] docker-compose.dev.yml is valid"
else
    echo "[error] docker-compose.dev.yml has errors"
fi

echo ""
echo "Setup verification complete."
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and set GEMINI_API_KEY"
echo "2. Run: docker compose up --build"
echo "3. Open: http://localhost:3000"