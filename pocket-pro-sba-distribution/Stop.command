#!/bin/bash

echo "========================================"
echo "PocketPro SBA - Stopping Application"
echo "========================================"
echo ""

# Stop containers
echo "Stopping Docker containers..."
docker compose down

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to stop containers"
    read -p "Press Enter to close..."
    exit 1
fi

echo ""
echo "========================================"
echo "Application Stopped Successfully!"
echo "========================================"
echo ""
echo "All containers have been stopped and removed."
echo "Your data in uploads/, chromadb_data/, and logs/ is preserved."
echo ""
read -p "Press Enter to close..."
