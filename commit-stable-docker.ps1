# Git commit script for stable Docker configuration

# Add the changes to git
git add docker-compose.yml
git add docker-compose.minimal-memory.yml
git add gunicorn.minimal.py
git add Dockerfile.backend
git add Dockerfile.frontend.dev
git add frontend/src/App.js
git add frontend/src/App.css
git add INSTRUCTIONS.md
git add DOCKER_CONFIGURATION.md
git add nginx.conf

# Create a commit with a descriptive message
git commit -m "Stable Docker configuration with memory optimizations and improved frontend"

# Add tag for this stable version
git tag -a v1.0.0-stable-docker -m "Stable Docker configuration with memory optimizations"

Write-Host "Changes committed successfully. Tag v1.0.0-stable-docker created."
Write-Host "Use 'git push origin master --tags' to push changes to remote repository."
