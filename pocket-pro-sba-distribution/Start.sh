#!/bin/bash

echo "========================================"
echo "PocketPro SBA - Starting Application"
echo "========================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running."
    echo "Please start Docker and try again."
    read -p "Press Enter to exit..."
    exit 1
fi
echo "[OK] Docker is running"
echo ""

# Create .env from .env.example if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "[OK] .env file created"
    echo ""
    echo "IMPORTANT: Please edit .env and add your GEMINI_API_KEY"
    echo "Get your API key from: https://makersuite.google.com/app/apikey"
    echo ""
    read -p "Press Enter to continue after adding your API key..."
else
    echo "[OK] .env file exists"
    echo ""
fi

# Check for GEMINI_API_KEY
if ! grep -q "GEMINI_API_KEY=" .env; then
    echo "WARNING: GEMINI_API_KEY not found in .env file"
    echo "Please add your Gemini API key to .env:"
    echo "GEMINI_API_KEY=your_actual_api_key_here"
    echo ""
    read -p "Press Enter to continue anyway..."
elif grep -q "GEMINI_API_KEY=your_gemini_api_key_here" .env; then
    echo "WARNING: GEMINI_API_KEY is set to placeholder value"
    echo "Please edit .env and replace with your actual API key"
    echo "Get your API key from: https://makersuite.google.com/app/apikey"
    echo ""
    read -p "Press Enter to continue anyway..."
else
    echo "[OK] GEMINI_API_KEY is configured"
fi
echo ""

# Build and start containers
echo "Building and starting Docker containers..."
echo "This may take several minutes on first run..."
echo ""
docker compose up --build -d

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to start containers"
    echo "Run 'docker compose logs' to see error details"
    read -p "Press Enter to exit..."
    exit 1
fi

echo ""
echo "========================================"
echo "Application Started Successfully!"
echo "========================================"
echo ""
echo "Access URLs:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:5000"
echo "  ChromaDB: http://localhost:8000"
echo ""
echo "Health Check:"
echo "  http://localhost:5000/api/health"
echo ""
echo "To stop the application, run ./Stop.sh"
echo ""
read -p "Press Enter to close..."
