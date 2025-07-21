# PocketPro:SBA Edition

A scalable Retrieval-Augmented Generation (RAG) application for SBA and small business resources, powered by AI.

## Features

- 🤖 **AI-Powered Chat Interface**: Conversational AI using Google Gemini
- 📄 **Document Processing**: Upload and process PDF, Word, Markdown, and text files
- 🔍 **Semantic Search**: Find relevant information using vector similarity
- 🏗️ **Task Decomposition**: Break down complex tasks into manageable steps
- 🌐 **Web Interface**: Modern, responsive React frontend
- 🐳 **Docker Ready**: Easy deployment with Docker Compose

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- Docker and Docker Compose (for containerized deployment)
- Google Gemini API key

### 1. Clone and Setup

```bash
git clone <repository-url>
cd PocketProSBA
```

### 2. Configure Environment

```bash
# Copy the environment template
cp .env.template .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your_api_key_here
```

### 3. Development Mode

#### Option A: Docker (Recommended)

```bash
# For Windows
deploy-docker.bat

# For Linux/Mac
chmod +x deploy-docker.sh
./deploy-docker.sh
```

#### Option B: Local Development

```bash
# For Windows
start-dev.bat

# For Linux/Mac
chmod +x start-dev.sh
./start-dev.sh
```

### 4. Access the Application

- **Web Interface**: http://localhost:10000 (Docker) or http://localhost:3000 (Local)
- **Backend API**: http://localhost:5000
- **ChromaDB**: http://localhost:8000

### 5. Health Check

```bash
python health_check.py
```

## Architecture

- **Frontend**: React.js with Bootstrap, served by Nginx
- **Backend**: Python Flask with SocketIO for real-time updates
- **Vector DB**: ChromaDB for document embeddings
- **LLM**: Google Gemini for AI capabilities

## API Endpoints

- `POST /api/decompose` - Process user messages and decompose tasks
- `POST /api/files` - Upload and process documents
- `POST /api/query` - Search documents
- `GET /health` - Health check
- `GET /api/info` - Application information

## File Upload Support

- PDF (.pdf)
- Microsoft Word (.docx)
- Markdown (.md)
- Plain text (.txt)

## Configuration

Key environment variables:

- `GEMINI_API_KEY` - Required: Google Gemini API key
- `CHROMA_HOST` - ChromaDB host (default: localhost)
- `UPLOAD_FOLDER` - File upload directory (default: ./uploads)
- `CHUNK_SIZE` - Document chunking size (default: 500)

## Troubleshooting

If you encounter connection issues between the frontend and backend, try these steps:

1. **Check if the backend is running:**
   ```
   .\check-backend.ps1
   ```
   or
   ```
   check-backend.bat
   ```

2. **Run the connection diagnostics:**
   ```
   .\diagnose-connection.ps1
   ```
   or
   ```
   diagnose-connection.bat
   ```

3. **Ensure the frontend is configured correctly:**
   - Make sure there's a `.env` file in the `frontend` directory with `REACT_APP_BACKEND_URL=http://localhost:5000`
   - Check that `package.json` has a proxy entry: `"proxy": "http://localhost:5000"`

4. **Start both backend and frontend together:**
   ```
   .\start-dev-full.ps1
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
