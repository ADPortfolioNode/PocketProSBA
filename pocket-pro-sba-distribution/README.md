# PocketPro SBA - Self-Hosted Distribution

A comprehensive AI-powered SBA (Small Business Administration) assistant that helps entrepreneurs navigate business planning, funding, and resources through intelligent conversation and document analysis.

## Features

- **AI-Powered Assistance**: Get personalized guidance on SBA programs, loans, and business planning
- **Document Analysis**: Upload and analyze business documents with AI
- **Interactive Chat**: Real-time conversation with intelligent assistants
- **Resource Browser**: Browse SBA resources, articles, and guides
- **Self-Hosted**: Complete control over your data - runs on your own infrastructure
- **Docker-Based**: Easy deployment with Docker and Docker Compose

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
  - Download from: https://www.docker.com/products/docker-desktop
- **Docker Compose** (included with Docker Desktop)
- **Gemini API Key** (Required for AI functionality)
  - Get your free API key from: https://makersuite.google.com/app/apikey

## Quick Start

### Windows Users

1. **Double-click** `Start.bat` to start the application
2. The script will:
   - Check if Docker is running
   - Create `.env` file from `.env.example` if it doesn't exist
   - Prompt you to add your GEMINI_API_KEY
   - Build and start all containers
   - Display access URLs

3. **Double-click** `Stop.bat` to stop the application

### Linux/Mac Users

1. Make the script executable (first time only):
   ```bash
   chmod +x Start.sh
   chmod +x Stop.sh
   ```

2. **Double-click** `Start.sh` or run `./Start.sh` to start the application
3. The script will:
   - Check if Docker is running
   - Create `.env` file from `.env.example` if it doesn't exist
   - Prompt you to add your GEMINI_API_KEY
   - Build and start all containers
   - Display access URLs

4. **Double-click** `Stop.sh` or run `./Stop.sh` to stop the application

## Manual Setup

If you prefer manual setup or encounter issues with the startup scripts:

### 1. Configure Environment

Copy the example environment file:
```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Edit `.env` and add your Gemini API Key:
```
GEMINI_API_KEY=your_actual_api_key_here
```

### 2. Start the Application

```bash
docker compose up --build -d
```

### 3. Stop the Application

```bash
docker compose down
```

## Accessing the Application

Once started, access the application at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **ChromaDB**: http://localhost:8000

### Health Check

Verify the application is running:
```bash
curl http://localhost:5000/api/health
```

## Configuration

### Environment Variables

Edit `.env` to configure the application:

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Required: Your Gemini API key | - |
| `SECRET_KEY` | Flask secret key for sessions | Random |
| `LLM_MODEL` | AI model to use | gemini-pro |
| `LLM_TEMPERATURE` | AI response randomness (0-1) | 0.2 |
| `CHROMADB_HOST` | ChromaDB host | chromadb |
| `CHROMADB_PORT` | ChromaDB port | 8000 |
| `UPLOAD_FOLDER` | File upload directory | ./uploads |
| `MAX_CONTENT_LENGTH` | Max upload size (bytes) | 16777216 |

### Port Configuration

To change default ports, edit `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "5000:5000"  # Change to "YOUR_PORT:5000"
  chromadb:
    ports:
      - "8000:8000"  # Change to "YOUR_PORT:8000"
  frontend:
    ports:
      - "3000:80"    # Change to "YOUR_PORT:80"
```

## Directory Structure

```
pocket-pro-sba-distribution/
├── backend/              # Python Flask backend
│   ├── app/             # Application modules
│   ├── assistants/      # AI assistant implementations
│   ├── knowledge_base/  # SBA knowledge base
│   ├── models/          # Database models
│   ├── routes/          # API routes
│   ├── services/        # Business logic
│   └── utils/           # Utility functions
├── frontend/            # React frontend
│   ├── build/           # Pre-built React app
│   ├── public/          # Static assets and HTML files
│   └── nginx.dev.conf   # Nginx configuration
├── uploads/             # User-uploaded files (created at runtime)
├── chromadb_data/       # Vector database storage (created at runtime)
├── logs/                # Application logs (created at runtime)
├── docker-compose.yml   # Docker Compose configuration
├── Dockerfile.production  # Backend Dockerfile
├── Dockerfile.frontend    # Frontend Dockerfile
├── nginx.conf            # Nginx configuration
├── .env.example          # Environment template
├── wsgi.py              # WSGI entry point
├── run.py               # Application entry point
├── Start.bat            # Windows startup script
├── Start.sh             # Linux/Mac startup script
├── Stop.bat             # Windows stop script
├── Stop.sh              # Linux/Mac stop script
├── LICENSE.txt          # MIT License
└── README.md            # This file
```

## Troubleshooting

### Docker Not Running

**Error**: "Docker is not running. Please start Docker Desktop and try again."

**Solution**:
- Windows/Mac: Start Docker Desktop from your applications
- Linux: Start Docker service: `sudo systemctl start docker`

### Port Already in Use

**Error**: "port is already allocated"

**Solution**:
- Change the port mapping in `docker-compose.yml`
- Or stop the service using the port:
  ```bash
  # Windows
  netstat -ano | findstr :3000
  taskkill /PID <PID> /F

  # Linux/Mac
  lsof -ti:3000 | xargs kill -9
  ```

### Missing GEMINI_API_KEY

**Error**: Application starts but AI features don't work

**Solution**:
1. Edit `.env` file
2. Add your Gemini API key: `GEMINI_API_KEY=your_key_here`
3. Restart containers: `docker compose restart`

### Container Won't Start

**Error**: Container exits immediately

**Solution**:
1. Check logs: `docker compose logs backend`
2. Verify `.env` file exists and is configured
3. Rebuild containers: `docker compose up --build -d`

### Frontend Not Loading

**Error**: Browser shows "Unable to connect"

**Solution**:
1. Check if frontend container is running: `docker compose ps`
2. Check frontend logs: `docker compose logs frontend`
3. Verify port 3000 is not blocked by firewall

### Slow Performance

**Cause**: Insufficient system resources

**Solution**:
- Allocate more RAM to Docker (Docker Desktop Settings > Resources)
- Reduce ChromaDB memory usage in `.env`:
  ```
  CHROMA_SERVER_GRPC_PORT=8001
  ```

## Data Persistence

The following directories are persisted as Docker volumes:

- `./uploads` - User-uploaded files
- `./chromadb_data` - Vector database storage
- `./logs` - Application logs

To backup your data:
```bash
# Create backup
tar -czf pocketpro-backup-$(date +%Y%m%d).tar.gz uploads chromadb_data logs

# Restore backup
tar -xzf pocketpro-backup-YYYYMMDD.tar.gz
```

## Updating the Application

To update to a new version:

1. Stop the application:
   ```bash
   docker compose down
   ```

2. Backup your data (see Data Persistence section)

3. Replace the distribution files with the new version

4. Restart:
   ```bash
   docker compose up --build -d
   ```

## Security Considerations

- **API Keys**: Never commit `.env` to version control
- **Firewall**: Consider restricting access to ports 5000 and 8000 in production
- **HTTPS**: For production deployment, use a reverse proxy with SSL/TLS
- **Updates**: Keep Docker and system packages updated

## System Requirements

### Minimum Requirements
- **RAM**: 4 GB
- **Disk Space**: 10 GB
- **CPU**: 2 cores

### Recommended Requirements
- **RAM**: 8 GB
- **Disk Space**: 20 GB
- **CPU**: 4 cores

## Support

For issues, questions, or contributions:

- Check the troubleshooting section above
- Review Docker logs: `docker compose logs`
- Verify environment configuration in `.env`

## License

This project is licensed under the MIT License - see LICENSE.txt for details.

## Acknowledgments

- SBA (Small Business Administration) for providing comprehensive business resources
- Google Gemini API for AI capabilities
- ChromaDB for vector database functionality
- Flask and React for the application framework
