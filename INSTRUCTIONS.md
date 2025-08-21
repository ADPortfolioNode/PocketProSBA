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

The application uses environment variables for configuration. Create a `.env` file in the `backend` directory and a `.env` file in the `frontend` directory. You can use the `.env.example` files as a template.

**Backend (`backend/.env`):**

```
FLASK_ENV=development
PORT=5000
FRONTEND_URL=http://localhost:3000
CHROMADB_HOST=localhost
CHROMADB_PORT=8000
GEMINI_API_KEY=YOUR_GEMINI_API_KEY # Replace with your actual Gemini API Key
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

To run the application with Docker, use the `docker-compose.yml` file:

```bash
docker-compose up --build
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
