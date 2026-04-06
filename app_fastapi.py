"""
FastAPI Backend for PocketPro:SBA Edition
High-performance async API server with modern Python features
"""
import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for API
class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "PocketPro:SBA Backend"
    version: str = "2.0.0"
    environment: str
    timestamp: float

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="The search query")
    collection: str = Field("documents", description="Collection to search in")
    top_k: int = Field(5, ge=1, le=20, description="Number of results to return")

class QueryResponse(BaseModel):
    status: str
    results: Dict[str, Any]
    query: str
    collection: str

class DocumentUploadResponse(BaseModel):
    status: str
    filename: str
    doc_id: str
    message: str

class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str = Field(default="default")
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: float

class TaskDecomposition(BaseModel):
    task: str = Field(..., min_length=1)
    context: Optional[Dict[str, Any]] = None

class TaskResponse(BaseModel):
    task_id: str
    steps: List[Dict[str, Any]]
    status: str

# Initialize FastAPI app
app = FastAPI(
    title="PocketPro:SBA API",
    description="High-performance RAG-powered SBA business assistant API",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:10000", 
        "http://frontend:80",
        "http://nginx:80"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global services
chroma_service = None
rag_system_available = False

async def get_chroma_service():
    """Dependency to get ChromaDB service"""
    global chroma_service
    if chroma_service is None:
        try:
            from services.chroma_service import get_chroma_service_instance
            chroma_service = get_chroma_service_instance()
            return chroma_service
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise HTTPException(
                status_code=503, 
                detail="ChromaDB service unavailable"
            )
    return chroma_service

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global rag_system_available
    try:
        logger.info("🚀 Starting PocketPro:SBA FastAPI server...")
        
        # Initialize ChromaDB service
        await get_chroma_service()
        rag_system_available = True
        
        logger.info("✅ All services initialized successfully")
    except Exception as e:
        logger.error(f"❌ Service initialization failed: {e}")
        rag_system_available = False

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🔄 Shutting down PocketPro:SBA server...")

# Root endpoint
@app.get("/")
async def root():
    """Root API endpoint"""
    return {
        "name": "PocketPro:SBA Edition",
        "description": "High-performance RAG-powered SBA business assistant",
        "status": "running",
        "version": "2.0.0",
        "api_docs": "/api/docs",
        "endpoints": {
            "health": "/health",
            "api": "/api/*",
            "chat": "/api/chat",
            "rag": "/api/rag/*",
            "sba": "/api/sba/*"
        }
    }

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        environment=os.environ.get('FLASK_ENV', 'production'),
        timestamp=asyncio.get_event_loop().time()
    )

# API Routes
@app.get("/api/health")
async def api_health():
    """API health check"""
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "chromadb": "connected" if rag_system_available else "disconnected"
        },
        "timestamp": asyncio.get_event_loop().time()
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage, chroma: Any = Depends(get_chroma_service)):
    """Chat endpoint with RAG integration"""
    try:
        # Process chat message with RAG
        response_text = await process_chat_message(message.message, chroma)
        
        return ChatResponse(
            response=response_text,
            session_id=message.session_id,
            timestamp=asyncio.get_event_loop().time()
        )
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag/query", response_model=QueryResponse)
async def query_documents(query: QueryRequest, chroma: Any = Depends(get_chroma_service)):
    """Query documents using RAG"""
    try:
        results = chroma.query_documents(
            query_text=query.query,
            n_results=query.top_k
        )
        
        return QueryResponse(
            status="success",
            results=results,
            query=query.query,
            collection=query.collection
        )
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    chroma: Any = Depends(get_chroma_service)
):
    """Upload and process document"""
    try:
        # Read file content
        content = await file.read()
        text = content.decode('utf-8')
        
        # Generate document ID
        import uuid
        doc_id = str(uuid.uuid4())
        
        # Add to ChromaDB
        result = chroma.add_documents(
            documents=[text],
            metadatas=[{"filename": file.filename, "size": len(content)}],
            ids=[doc_id]
        )
        
        if result.get("success"):
            return DocumentUploadResponse(
                status="success",
                filename=file.filename,
                doc_id=doc_id,
                message=f"Document {file.filename} uploaded successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to process document")
            
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/decompose", response_model=TaskResponse)
async def decompose_task(task: TaskDecomposition):
    """Decompose task into steps"""
    try:
        # Implement task decomposition logic
        steps = await decompose_task_logic(task.task)
        
        import uuid
        task_id = str(uuid.uuid4())
        
        return TaskResponse(
            task_id=task_id,
            steps=steps,
            status="decomposed"
        )
    except Exception as e:
        logger.error(f"Task decomposition error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# SBA Content Routes
@app.get("/api/sba/articles")
async def search_sba_articles(q: str = "", limit: int = 10):
    """Search SBA articles"""
    try:
        # Implement SBA article search
        return {"articles": [], "query": q, "limit": limit}
    except Exception as e:
        logger.error(f"SBA articles search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sba/courses")
async def search_sba_courses(q: str = "", limit: int = 10):
    """Search SBA courses"""
    try:
        # Implement SBA course search
        return {"courses": [], "query": q, "limit": limit}
    except Exception as e:
        logger.error(f"SBA courses search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
async def process_chat_message(message: str, chroma_service) -> str:
    """Process chat message with RAG"""
    try:
        # Query relevant documents
        results = chroma_service.query_documents(message, n_results=3)
        
        if results.get("success") and results["results"]["documents"]:
            # Use retrieved context to generate response
            context = "\n".join(results["results"]["documents"][0])
            response = f"Based on the available information: {context}\n\nTo answer your question: {message}"
        else:
            response = f"I understand you're asking about: {message}. Let me help you with that."
        
        return response
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        return "I apologize, but I'm having trouble processing your request right now."

async def decompose_task_logic(task: str) -> List[Dict[str, Any]]:
    """Decompose task into actionable steps"""
    # Simple task decomposition logic
    steps = [
        {"id": 1, "description": f"Analyze the task: {task}", "status": "pending"},
        {"id": 2, "description": "Research relevant information", "status": "pending"},
        {"id": 3, "description": "Execute the main action", "status": "pending"},
        {"id": 4, "description": "Validate and review results", "status": "pending"}
    ]
    return steps

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500}
    )

# Main entry point
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"🚀 Starting FastAPI server on {host}:{port}")
    
    uvicorn.run(
        "fastapi_app:app",
        host=host,
        port=port,
        reload=os.environ.get("FLASK_ENV") == "development",
        workers=1 if os.environ.get("FLASK_ENV") == "development" else 4
    )9