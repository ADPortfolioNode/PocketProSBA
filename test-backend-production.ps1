# Test script for PocketPro:SBA Backend production Docker image
# Builds, runs, tests health, and checks API endpoint

$ImageName = "pocketpro-backend-prod"
$ContainerName = "pocketpro-backend-prod-test"
$Port = 8000  # Change if your backend uses a different port
$HealthEndpoint = "/health"  # Change if your backend uses a different health endpoint

Write-Host "Building Docker image..."
docker build -f Dockerfile.backend.prod -t $ImageName .

Write-Host "Running container..."
docker run -d --name $ContainerName -p $Port:8000 $ImageName

Start-Sleep -Seconds 10

Write-Host "Checking container health status (if defined)..."
$Health = docker inspect --format='{{.State.Health.Status}}' $ContainerName
Write-Host "Health status: $Health"

if ($Health -and $Health -ne "healthy") {
    Write-Host "Container health check failed!"
    docker logs $ContainerName
    docker stop $ContainerName
    docker rm $ContainerName
    exit 1
}

Write-Host "Testing backend API endpoint..."
$response = Invoke-WebRequest -Uri "http://localhost:$Port$HealthEndpoint" -UseBasicParsing -ErrorAction SilentlyContinue
if ($response -and $response.StatusCode -eq 200) {
    Write-Host "Backend API endpoint responded successfully."
} else {
    Write-Host "Failed to get successful response from backend! Status: $($response.StatusCode)"
    docker logs $ContainerName
    docker stop $ContainerName
    docker rm $ContainerName
    exit 1
}

Write-Host "Cleaning up..."
docker stop $ContainerName

docker rm $ContainerName
Write-Host "Test completed successfully."
