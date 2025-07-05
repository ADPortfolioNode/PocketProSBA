"""
ChromaDB fallback module for Render.com deployment
Allows the application to run even if ChromaDB is not available
"""

import logging
import os
import sys

logger = logging.getLogger(__name__)

def get_vector_store():
    """
    Tries to initialize ChromaDB, falls back to SimpleVectorStore if not available
    """
    try:
        logger.info("Attempting to initialize ChromaDB...")
        # Try importing ChromaDB
        import chromadb
        from chromadb.config import Settings
        
        # ChromaDB is available, return real implementation
        logger.info("✅ ChromaDB is available!")
        
        # Import the actual implementation
        from services.chroma import ChromaService
        return ChromaService()
        
    except ImportError as e:
        logger.warning(f"⚠️ ChromaDB not available: {e}")
        logger.warning("⚠️ Using SimpleVectorStore fallback")
        
        # Import the simple vector store implementation
        from app import SimpleVectorStore
        return SimpleVectorStore()
    except Exception as e:
        logger.error(f"❌ Error initializing ChromaDB: {e}")
        logger.warning("⚠️ Using SimpleVectorStore fallback")
        
        # Import the simple vector store implementation
        from app import SimpleVectorStore
        return SimpleVectorStore()
