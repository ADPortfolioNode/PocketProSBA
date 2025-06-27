"""
RAG Manager for coordinating retrieval-augmented generation workflows.
"""
from typing import Dict, Any, List, Optional
from src.services.chroma_service import get_chroma_service_instance
from src.services.llm_factory import LLMFactory
from src.utils.config import config


class RAGManager:
    """Manager for RAG operations combining retrieval and generation."""
    
    def __init__(self):
        self.chroma_service = get_chroma_service_instance()
        self.llm = LLMFactory.get_llm()
    
    def query_documents(self, 
                       query: str, 
                       n_results: int = None,
                       include_sources: bool = True) -> Dict[str, Any]:
        """Query documents and return formatted results."""
        if n_results is None:
            n_results = config.DEFAULT_TOP_K
        
        # Get documents from ChromaDB
        search_results = self.chroma_service.query_documents(
            query_text=query,
            n_results=n_results
        )
        
        if not search_results.get("success", False):
            return {
                "success": False,
                "error": search_results.get("error", "Unknown error"),
                "results": []
            }
        
        # Format results
        formatted_results = self._format_search_results(
            search_results["results"], 
            include_sources=include_sources
        )
        
        return {
            "success": True,
            "results": formatted_results
        }
    
    def generate_rag_response(self, 
                             query: str, 
                             n_results: int = None,
                             system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response using RAG workflow."""
        try:
            # Retrieve relevant documents
            search_results = self.query_documents(query, n_results)
            
            if not search_results.get("success", False):
                return {
                    "success": False,
                    "text": "I apologize, but I couldn't retrieve relevant information at this time.",
                    "sources": []
                }
            
            # Format context from retrieved documents
            context = self._build_context_from_results(search_results["results"])
            sources = self._extract_sources_from_results(search_results["results"])
            
            # Generate response using LLM
            if not system_prompt:
                system_prompt = """You are a helpful assistant that answers questions based on the provided context. 
                Use only the information from the context to answer questions. 
                If the context doesn't contain enough information to answer the question, say so clearly.
                Always be accurate and cite your sources when possible."""
            
            response_text = self.llm.generate_response(
                prompt=query,
                context=context,
                system_prompt=system_prompt
            )
            
            return {
                "success": True,
                "text": response_text,
                "sources": sources,
                "context_used": bool(context)
            }
        
        except Exception as e:
            print(f"Error in RAG response generation: {e}")
            return {
                "success": False,
                "text": f"I encountered an error while processing your request: {str(e)}",
                "sources": []
            }
    
    def _format_search_results(self, 
                              results: Dict[str, List], 
                              include_sources: bool = True) -> List[Dict[str, Any]]:
        """Format ChromaDB search results into a structured format."""
        formatted_results = []
        
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
            result = {
                "content": doc,
                "metadata": metadata,
                "relevance_score": 1.0 - distance,  # Convert distance to similarity score
                "rank": i + 1
            }
            
            if include_sources and metadata:
                result["source"] = metadata.get("source", "Unknown")
                result["chunk_index"] = metadata.get("chunk_index", 0)
            
            formatted_results.append(result)
        
        return formatted_results
    
    def _build_context_from_results(self, results: List[Dict[str, Any]]) -> str:
        """Build context string from search results."""
        if not results:
            return ""
        
        context_parts = []
        for i, result in enumerate(results):
            content = result.get("content", "")
            source = result.get("source", "Unknown")
            
            context_parts.append(f"[Source {i+1}: {source}]\n{content}")
        
        return "\n\n".join(context_parts)
    
    def _extract_sources_from_results(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract unique sources from search results."""
        sources = []
        seen_sources = set()
        
        for result in results:
            source = result.get("source", "Unknown")
            if source not in seen_sources:
                sources.append(source)
                seen_sources.add(source)
        
        return sources
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the document collection."""
        return self.chroma_service.get_collection_stats()


# Singleton instance
_rag_manager_instance = None

def get_rag_manager() -> RAGManager:
    """Get singleton RAG manager instance."""
    global _rag_manager_instance
    if _rag_manager_instance is None:
        _rag_manager_instance = RAGManager()
    return _rag_manager_instance
