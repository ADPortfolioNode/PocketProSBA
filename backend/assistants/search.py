import os
import requests
from .base import BaseAssistant

class SearchAgent(BaseAssistant):
    """
    SearchAgent provides search capabilities using Google Custom Search API.
    Requires GOOGLE_API_KEY and GOOGLE_CSE_ID to be set in environment variables.
    """
    def __init__(self):
        super().__init__("SearchAgent")
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.cse_id = os.getenv("GOOGLE_CSE_ID")
        if not self.api_key or not self.cse_id:
            raise ValueError("GOOGLE_API_KEY and GOOGLE_CSE_ID must be set in environment variables.")

    def handle_message(self, message, session_id=None, metadata=None):
        """Handle a search request"""
        self._update_status("searching", 50, "Searching for information...")
        
        try:
            results = self.search(message, num_results=3)
            
            if not results:
                return self.report_failure("No search results found")
            
            # Format response
            response_text = f"I found these results for '{message}':\n\n"
            sources = []
            
            for i, result in enumerate(results):
                response_text += f"{i+1}. {result['title']}\n"
                response_text += f"   {result['snippet']}\n"
                response_text += f"   {result['link']}\n\n"
                
                sources.append({
                    "title": result['title'],
                    "url": result['link'],
                    "snippet": result['snippet']
                })
            
            return self.report_success(
                text=response_text,
                sources=sources
            )
            
        except Exception as e:
            return self.report_failure(f"Search failed: {str(e)}")

    def search(self, query, num_results=5):
        """Perform a Google search"""
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.api_key,
            "cx": self.cse_id,
            "q": query,
            "num": num_results
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json().get("items", [])
        return [
            {
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet")
            }
            for item in results
        ]
