# PocketPro:SBA

A Retrieval-Augmented Generation (RAG) application for Small Business Administration guidance, distributed via Docker.

## Technology Stack

| Component | Technology | Role |
|---|---|---|
| **Backend** | Python (Flask) | REST API, RAG orchestration, assistant routing |
| **Frontend** | React.js + nginx | Web UI served in a container with API proxy |
| **Vector DB** | ChromaDB | Persistent vector storage for document retrieval |
| **LLM** | Google Gemini | Generative AI for RAG responses |
| **Distribution** | Docker Compose | Single-command local and production deployment |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- A Gemini API key

### Run with Docker

```bash
# Copy and configure environment variables
cp .env.example .env
# Edit .env and set GEMINI_API_KEY

# Start all services (backend, frontend, chromadb)
docker compose up --build

# Or use the launcher script
./start.sh --mode prod
```

### Service URLs

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:5000 |
| ChromaDB | http://localhost:8000 |

## Development

```bash
# Development mode with hot-reload backend
./start.sh --mode dev

# Or directly with compose
docker compose -f docker-compose.dev.yml up --build
```

### Project Structure

```
PocketProSBA/
├── backend/            # Flask API, assistants, RAG services
├── frontend/           # React UI
├── uploads/            # Document storage
├── chromadb_data/      # Vector database storage
├── docker-compose.yml  # Production stack
└── docker-compose.dev.yml
```

### Container Networking

- Frontend nginx proxies `/api/*` to the backend service
- Backend connects to ChromaDB at `chromadb:8000`
- All services share the `pocketpro-network` bridge network

## Features

- **SBA Concierge Chat** — AI-guided business assistance
- **RAG Workflow** — upload, index, query, retrieve, and generate
- **SBA Navigation** — programs, lifecycle resources, local assistance
- **Task Orchestrator** — multi-step task decomposition and execution

## Troubleshooting

```bash
# Restart containers
docker compose down
docker compose up --build

# View logs
docker compose logs backend
docker compose logs frontend
docker compose logs chromadb
```

## License

Copyright © 2025 StainlessDeoism.biz - PocketPro:SBA Edition