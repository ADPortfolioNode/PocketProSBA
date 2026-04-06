#!/bin/bash

# Function to check Docker status
check_docker_status() {
    if docker info >/dev/null 2>&1; then
        echo "Docker is running."
    else
        echo "Docker is not running. Attempting to start Docker..."
        # On Linux, use systemctl; on macOS/Windows, Docker Desktop might need manual start
        if command -v systemctl >/dev/null; then
            sudo systemctl start docker
        else
            echo "Please start Docker Desktop manually or ensure Docker daemon is running."
            exit 1
        fi
        sleep 5  # Wait for Docker to start
        if docker info >/dev/null 2>&1; then
            echo "Docker started successfully."
        else
            echo "Failed to start Docker. Check system logs."
            exit 1
        fi
    fi
}

# Function to restart Docker
restart_docker() {
    echo "Restarting Docker..."
    if command -v systemctl >/dev/null; then
        sudo systemctl restart docker
    else
        echo "Manual restart required for Docker Desktop."
        exit 1
    fi
    sleep 5
    if docker info >/dev/null 2>&1; then
        echo "Docker restarted successfully."
    else
        echo "Failed to restart Docker."
        exit 1
    fi
}

# Function to troubleshoot using logs
troubleshoot_logs() {
    echo "Checking Docker logs for errors..."
    # Check system logs (Linux example)
    if command -v journalctl >/dev/null; then
        journalctl -u docker --since "1 hour ago" | grep -i error
    fi
    # Check Docker daemon logs if available
    docker system info 2>&1 | grep -i error
    echo "Inspect recent container logs if applicable (run 'docker logs <container_id>' manually)."
}

# Main script
echo "Determining Docker status..."
check_docker_status

echo "Restarting Docker for good measure..."
restart_docker

echo "Troubleshooting errors..."
troubleshoot_logs

echo "Docker troubleshooting complete."
