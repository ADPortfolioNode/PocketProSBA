# PocketPro:SBA - Production Deployment Guide

This project is a Retrieval-Augmented Generation (RAG) application designed for a streamlined, production-ready deployment on Render.com using the "Blueprint" (infrastructure-as-code) model.

## Technology Stack

| Component | Technology | Role |
|---|---|---|
| **Web Service** | Python (Flask) + React.js | A single Docker container serves both the backend API and the compiled frontend. |
| **Vector DB** | ChromaDB | Runs as a separate Private Service on Render for persistent vector storage. |
| **LLM** | Google Gemini | Provides the generative AI capabilities for the RAG system. |
| **Deployment** | Docker on Render.com | Infrastructure is defined in `render.yaml` for automated, repeatable deployments. |

---

### Prerequisites

- Python 3.9+
- Node.js 16+
- Docker and Docker Compose (for containerized deployment)
   ```
   or
   ```
   start-dev-full.bat
   ```

### Connection Issues

1. **Backend not responding**: Check if ChromaDB is running
2. **Frontend can't reach backend**: Verify nginx proxy configuration
3. **ChromaDB connection errors**: Ensure proper networking in docker-compose

### Common Fixes

```bash
# Restart containers
docker-compose down
docker-compose up --build

# Check container logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs chromadb

# Check container networking
docker network ls
docker-compose ps
```

### Container Networking

The application uses a custom Docker network to ensure proper communication:

- Frontend uses nginx proxy to route `/api/*` to backend
- Backend connects to ChromaDB using service name `chromadb:8000`
- All services are on the `app-network` bridge network

## Development

### Project Structure

```
PocketProSBA/
├── src/
│   ├── assistants/     # AI assistant implementations
│   ├── services/       # Core services (RAG, ChromaDB, LLM)
│   └── utils/          # Configuration and utilities
├── frontend/           # React frontend
├── uploads/           # Document storage
├── chromadb_data/     # Vector database storage
└── docker-compose.yml # Container orchestration
```

### Adding New Features

1. **New Assistant Types**: Extend `BaseAssistant` class
2. **Document Formats**: Add processors in `DocumentProcessor`
3. **API Endpoints**: Add routes in `app.py`

## Enhanced Frontend

The frontend interface now provides a comprehensive RAG workflow visualization and SBA resource navigation:

### RAG Workflow Interface

The frontend includes a dedicated RAG Workflow interface that visually guides users through the entire RAG process:

1. **Document Upload** - Upload and process documents
2. **Indexing** - Create vector embeddings of document chunks
3. **Query** - Ask questions about your documents
4. **Retrieval** - Find relevant context from indexed documents
5. **Generation** - Generate AI response using the context

This workflow-based approach helps users understand how RAG works and makes the process more intuitive.

### SBA Navigation

The enhanced SBA navigation organizes resources into three main categories:

- **SBA Programs** - Explore loan programs, government contracting, disaster assistance, etc.
- **Business Lifecycle** - Resources for planning, launching, managing, and growing a business
- **Local Resources** - Find local assistance through SBDCs, SCORE, Women's Business Centers, etc.

### Running the Frontend Separately

To start just the frontend during development:

#### Using PowerShell:

```powershell
# Start the frontend
.\start-frontend.ps1
```

#### Using Command Prompt:

```cmd
# Start the frontend
start-frontend.bat
```

## License

Copyright © 2025 StainlessDeoism.biz - PocketPro:SBA Edition

## Support

For issues and questions, please check the troubleshooting section or create an issue in the repository
