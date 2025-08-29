import os
import requests
import logging

logger = logging.getLogger(__name__)

class SearchModule:
    """
    SearchModule provides Google Custom Search capabilities for assistants.
    Requires GOOGLE_API_KEY and GOOGLE_CSE_ID to be set in environment variables.
    """
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.cse_id = os.getenv("GOOGLE_CSE_ID")
        self.available = bool(self.api_key and self.cse_id)
        
        if not self.available:
            logger.warning("Search module disabled: GOOGLE_API_KEY and GOOGLE_CSE_ID must be set in environment variables.")

    def is_available(self):
        """Check if search module is available"""
        return self.available

    def search(self, query, num_results=5):
        """Perform a Google search if available, otherwise return empty results"""
        if not self.available:
            logger.warning("Search module not available - returning empty results")
            return []
            
        try:
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
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []
