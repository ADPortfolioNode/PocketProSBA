# PocketPro:SBA Edition - Instructions

This document provides instructions for setting up, running, and deploying the PocketPro:SBA Edition application.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [Environment Variables](#environment-variables)
  - [Installation](#installation)
- [Running the Application Locally](#running-the-application-locally)
- [Running with Docker](#running-with-docker)
- [Deploying to Render](#deploying-to-render)
- [Testing](#testing)
- [API Reference](#api-reference)

## Prerequisites

- [Node.js](https://nodejs.org/) (v16 or higher)
- [Python](https://www.python.org/) (v3.9 or higher)
- [Docker](https://www.docker.com/)
- [Render CLI](https://render.com/docs/cli)

## Getting Started

### Environment Variables

The application uses environment variables for configuration. You should create `.env` files in the `backend` and `frontend` directories based on the provided `.env.example` files.

**Backend (`backend/.env`):**

```
PORT=5000
FRONTEND_URL=http://localhost:3000
GEMINI_API_KEY=YOUR_GEMINI_API_KEY # Replace with your actual Gemini API Key
CHROMADB_HOST=localhost
CHROMADB_PORT=8000
```

**Frontend (`frontend/.env`):

```
REACT_APP_API_URL=http://localhost:5000 # Base URL for the backend API
```

### Installation

**Backend:**

```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**

```bash
cd frontend
npm install
```

## Running the Application Locally

**Backend:**

```bash
cd backend
flask run
```

The backend will be running at `http://localhost:5000`.

**Frontend:**

```bash
cd frontend
npm start
```

The frontend will be running at `http://localhost:3000`.

## Running with Docker

### Local Development with Docker

To run the application with Docker for local development:

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Services Overview
- **Backend**: Runs on port 5000 (http://localhost:5000)
- **Frontend**: Runs on port 3000 (http://localhost:3000)
- **ChromaDB**: Runs on port 8000 (http://localhost:8000)

### Environment Setup for Docker

1. **Backend**: Copy `backend/.env.example` to `backend/.env`
2. **Frontend**: Copy `frontend/.env.example` to `frontend/.env`

### Production Docker Build

For production deployment:

```bash
# Build production image
docker build -f Dockerfile.production -t pocketpro-backend .

# Build frontend image
docker build -f Dockerfile.frontend -t pocketpro-frontend .

# Run production containers
docker run -p 5000:5000 pocketpro-backend
docker run -p 3000:80 pocketpro-frontend
```

## Deploying to Render

The application is configured for deployment to Render using the `render.yaml` file. You can deploy the application by creating a new "Blueprint" service in the Render dashboard and connecting it to your GitHub repository.

Render will automatically build and deploy the frontend and backend services based on the `render.yaml` file.

**Build Commands:**

- **Backend:** `pip install -r backend/requirements.txt`
- **Frontend:** `cd frontend && npm install && npm run build`

**Start Commands:**

- **Backend:** `gunicorn 'backend.app:create_app()' --bind 0.0.0.0:$PORT`

## Testing

**Backend:**

```bash
cd backend
pytest
```

**Frontend:**

```bash
cd frontend
npm test
```

## API Reference

For details on the API endpoints, please see the [API Reference](docs/api.md).
