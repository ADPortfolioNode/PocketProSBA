# Test script for PocketPro:SBA Frontend production Docker image
# Builds, runs, tests health, and checks static file serving

$ImageName = "pocketpro-frontend-prod"
$ContainerName = "pocketpro-frontend-prod-test"
$Port = 8080

Write-Host "Building Docker image..."
docker build -f Dockerfile.frontend.prod -t $ImageName .

Write-Host "Running container..."
docker run -d --name $ContainerName -p $Port:80 $ImageName

Start-Sleep -Seconds 10

Write-Host "Checking container health status..."
$Health = docker inspect --format='{{.State.Health.Status}}' $ContainerName
Write-Host "Health status: $Health"

if ($Health -ne "healthy") {
    Write-Host "Container health check failed!"
    docker logs $ContainerName
    docker stop $ContainerName
    docker rm $ContainerName
    exit 1
}

Write-Host "Testing static file serving..."
$response = Invoke-WebRequest -Uri "http://localhost:$Port" -UseBasicParsing
if ($response.StatusCode -eq 200) {
    Write-Host "Static files served successfully."
} else {
    Write-Host "Failed to serve static files! Status: $($response.StatusCode)"
    docker logs $ContainerName
    docker stop $ContainerName
    docker rm $ContainerName
    exit 1
}

Write-Host "Cleaning up..."
docker stop $ContainerName

docker rm $ContainerName
Write-Host "Test completed successfully."
