# AI Agent Instructions for PocketProSBA

## Project Overview
PocketProSBA is a Retrieval-Augmented Generation (RAG) application using Python/Flask backend, React frontend, and ChromaDB for vector storage. The system integrates with Google Gemini for generative AI capabilities.

## Key Architecture Patterns

### Service Architecture
```
Frontend (React) → apiClient → Backend (Flask) → Services → ChromaDB
    │                         │
    └── Environment Variables └── Environment Variables
```

### Major Components
- `/backend`: Flask API with BluePrint-based routing (`/api`, `/chat`)
- `/frontend`: React SPA with dedicated RAG workflow interface
- `/src/assistants`: AI assistant implementations (extend `BaseAssistant`)
- `/src/services`: Core services (RAG, ChromaDB, LLM integrations)
- `chromadb_data/`: Persistent vector database storage

## Development Workflows

### Local Development
1. Backend: 
   ```bash
   cd backend
   flask run --debug
   ```
2. Frontend:
   ```bash
   cd frontend
   npm start
   ```

### Testing
- Backend: Use `pytest` in `/backend` directory
- Frontend: Use `npm test` with Jest in `/frontend` directory
- Workflow Tests: `test_concierge_workflows.py` for end-to-end RAG flows

## Project-Specific Conventions

### Code Organization
- Backend: Uses Flask BluePrints and service layer pattern
- Frontend: `apiClient.js` for API calls, custom hooks in `hooks/`
- Naming: `camelCase` for frontend, `snake_case` for backend

### Error Handling
- Backend: Global Flask error handlers (400/404/500)
- Frontend: Error handling in `useConnection` hook
- Standardized JSON error format across API

### Environment Configuration
Backend (.env):
```
PORT=5000
FRONTEND_URL=http://localhost:3000
GEMINI_API_KEY=your_key
CHROMADB_HOST=localhost
CHROMADB_PORT=8000
```

Frontend (.env):
```
REACT_APP_API_URL=http://localhost:5000
```

## Integration Points

### ChromaDB Integration
- Runs as separate service (port 8000)
- Persistent storage in `chromadb_data/`
- Connection configured via environment variables

### RAG Workflow
1. Document Upload → `DocumentProcessor`
2. Vector Embedding → ChromaDB
3. Query Processing → Concierge Service
4. Context Retrieval → RAG Manager
5. Response Generation → Gemini LLM

## Common Development Tasks

### Adding New Features
1. New Assistant Types: Extend `BaseAssistant` class
2. Document Formats: Add processors in `DocumentProcessor`
3. API Endpoints: Add routes in `app.py`

### Testing Changes
1. Run backend tests: `pytest tests/test_api.py -v`
2. Run frontend tests: `npm test -- --coverage`
3. Verify ChromaDB integration: `test_concierge_comprehensive.py`

### Docker Development
```bash
# Development with hot-reload
docker-compose -f docker-compose.dev.yml up --build

# View logs
docker-compose -f docker-compose.dev.yml logs -f
```