# ChromaDB Render.com Production Deployment

## Files Created
- Dockerfile.chromadb: Production Dockerfile for ChromaDB
- .env.chromadb: Environment variables for ChromaDB
- docker-compose.chroma.yml: Multi-service config for backend + ChromaDB
- render-chromadb.yaml: Render.com service definition for ChromaDB

## Steps
1. Push all files to your repo.
2. On Render.com, create a new service using `render-chromadb.yaml`.
3. Ensure persistent disk is enabled for `/app/chroma-data`.
4. Backend should use `CHROMADB_HOST` and `CHROMADB_PORT` from `.env.chromadb`.
5. Health check endpoint: `/api/v1/heartbeat`.
6. For multi-service, use `docker-compose.chroma.yml` locally or on Render if supported.

## Notes
- All config favors Render.com best practices: persistent disk, health checks, auto deploy, environment isolation.
- For custom ChromaDB config, edit `.env.chromadb` and `render-chromadb.yaml`.
- Backend must wait for ChromaDB health check to pass before starting workflows.
