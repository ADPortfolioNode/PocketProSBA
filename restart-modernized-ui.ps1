Write-Host "Restarting PocketPro SBA Application..." -ForegroundColor Green

# Restart the Docker containers to apply changes
docker-compose down
docker-compose up -d

Write-Host "Application restarted! The modernized UI with SBA Content Explorer is now available." -ForegroundColor Green
Write-Host "Access the application at http://localhost:3000" -ForegroundColor Cyan
