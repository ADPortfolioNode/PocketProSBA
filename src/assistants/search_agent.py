"""
SearchAgent - Specialized assistant for document retrieval and RAG operations.
"""
from typing import Dict, Any, Optional, List
from src.assistants.base_assistant import BaseAssistant
from src.services.chroma_service import get_chroma_service_instance
from src.services.rag_manager import get_rag_manager
from src.services.llm_factory import LLMFactory


class SearchAgent(BaseAssistant):
    """Specialized assistant for document search and retrieval operations."""
    
    def __init__(self):
        super().__init__("SearchAgent")
        self.chroma_service = get_chroma_service_instance()
        self.rag_manager = get_rag_manager()
        self.llm = LLMFactory.get_llm()
        
        # System prompt for search operations
        self.system_prompt = """You are a search specialist that retrieves relevant document information from the knowledge base.
        Focus on providing accurate, relevant information from the available documents.
        Always cite your sources and indicate the relevance of the information found."""
    
    def handle_message(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Handle search requests and return relevant documents or perform internet search if requested."""
        try:
            self._update_status("running", 10, "Processing search query...")

            # Check for internet search intent
            if context and context.get("internet_search", False):
                self._update_status("running", 20, "Performing internet search...")
                query = message
                # Use Google Custom Search API or similar (pseudo-code, replace with real implementation)
                import requests
                api_key = context.get("google_api_key")
                cx = context.get("google_cx")
                if not api_key or not cx:
                    return self.report_failure("Google API key and CX (search engine ID) required for internet search.")
                url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={cx}"
                resp = requests.get(url)
                if resp.status_code != 200:
                    return self.report_failure(f"Google Search API error: {resp.text}")
                data = resp.json()
                items = data.get("items", [])
                results = []
                for item in items:
                    results.append({
                        "title": item.get("title"),
                        "snippet": item.get("snippet"),
                        "link": item.get("link")
                    })
                formatted = "\n\n".join([f"{r['title']}\n{r['snippet']}\n{r['link']}" for r in results])
                return self.report_success(
                    text=f"Internet search results for '{query}':\n\n{formatted}",
                    additional_data={
                        "results": results,
                        "source": "google_search"
                    }
                )

            # ...existing document search logic...
            top_k = 5
            if context:
                top_k = context.get("top_k", 5)
                search_filters = context.get("filters", None)

            # Get collection statistics
            collection_stats = self.rag_manager.get_collection_stats()

            if collection_stats.get("document_count", 0) == 0:
                return self.report_failure(
                    "No documents are currently available in the knowledge base. Please upload some documents first."
                )

            self._update_status("running", 30, "Searching document collection...")

            # Execute search
            search_results = self.rag_manager.query_documents(
                query=message,
                n_results=top_k,
                include_sources=True
            )

            if not search_results.get("success", False):
                return self.report_failure(
                    f"Search failed: {search_results.get('error', 'Unknown error')}"
                )

            results = search_results.get("results", [])

            if not results:
                return self.report_success(
                    text="I couldn't find any relevant documents for your query. You might want to try rephrasing your question or check if the relevant documents have been uploaded.",
                    additional_data={
                        "sources": [],
                        "results_count": 0,
                        "collection_stats": collection_stats
                    }
                )

            self._update_status("running", 70, "Formatting search results...")

            # Format results for presentation
            formatted_results = self._format_advanced_results(results)

            return self.report_success(
                text=formatted_results,
                additional_data={
                    "sources": self._extract_sources(results),
                    "results_count": len(results),
                    "collection_stats": collection_stats,
                    "raw_results": results
                }
            )

        except Exception as e:
            return self.report_failure(f"Error during search operation: {str(e)}")
    
    def _format_advanced_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results into a comprehensive response."""
        if not results:
            return "No relevant documents found."
        
        # Group results by source
        sources_content = {}
        for result in results:
            source = result.get("source", "Unknown")
            content = result.get("content", "")
            relevance = result.get("relevance_score", 0.0)
            
            if source not in sources_content:
                sources_content[source] = []
            
            sources_content[source].append({
                "content": content,
                "relevance": relevance,
                "chunk_index": result.get("chunk_index", 0)
            })
        
        # Build formatted response
        response_parts = []
        response_parts.append(f"I found relevant information from {len(sources_content)} document(s):")
        response_parts.append("")
        
        for source, chunks in sources_content.items():
            response_parts.append(f"**{source}:**")
            
            # Sort chunks by relevance and take top 2 per source
            chunks.sort(key=lambda x: x["relevance"], reverse=True)
            top_chunks = chunks[:2]
            
            for i, chunk in enumerate(top_chunks):
                content = chunk["content"]
                relevance = chunk["relevance"]
                
                # Truncate very long content
                if len(content) > 300:
                    content = content[:300] + "..."
                
                response_parts.append(f"  {content}")
                if len(top_chunks) > 1:
                    response_parts.append("")
            
            response_parts.append("")
        
        # Add summary
        response_parts.append("Would you like me to elaborate on any specific aspect of this information?")
        
        return "\n".join(response_parts)
    
    def _extract_sources(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract unique sources from search results."""
        sources = []
        seen_sources = set()
        
        for result in results:
            source = result.get("source", "Unknown")
            if source not in seen_sources:
                sources.append(source)
                seen_sources.add(source)
        
        return sources
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the document collection."""
        try:
            stats = self.rag_manager.get_collection_stats()
            return self.report_success(
                text=f"Document collection contains {stats.get('document_count', 0)} chunks from uploaded documents.",
                additional_data=stats
            )
        except Exception as e:
            return self.report_failure(f"Error retrieving collection info: {str(e)}")


# Factory function for creating SearchAgent instances
def create_search_agent() -> SearchAgent:
    """Create a new SearchAgent assistant instance."""
    return SearchAgent()
