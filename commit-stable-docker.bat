@echo off
REM Git commit script for stable Docker configuration

REM Add the changes to git
git add docker-compose.yml
git add docker-compose.minimal-memory.yml
git add gunicorn.minimal.py
git add Dockerfile.backend
git add Dockerfile.frontend.dev
git add frontend\src\App.js
git add frontend\src\App.css
git add frontend\src\index.js
git add frontend\REACT18_UPGRADE.md
git add INSTRUCTIONS.md
git add DOCKER_CONFIGURATION.md
git add nginx.conf

REM Create a commit with a descriptive message
git commit -m "Stable Docker configuration with memory optimizations and React 18 upgrade"

REM Add tag for this stable version
git tag -a v1.0.0-stable -m "Stable Docker configuration with memory optimizations and React 18 upgrade"

echo Changes committed successfully. Tag v1.0.0-stable created.
echo Use 'git push origin master --tags' to push changes to remote repository.
