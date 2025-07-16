import os
import requests

class SearchAgent:
    """
    SearchAgent provides search capabilities using Google Custom Search API.
    Requires GOOGLE_API_KEY and GOOGLE_CSE_ID to be set in environment variables.
    """
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.cse_id = os.getenv("GOOGLE_CSE_ID")
        if not self.api_key or not self.cse_id:
            raise ValueError("GOOGLE_API_KEY and GOOGLE_CSE_ID must be set in environment variables.")

    def search(self, query, num_results=5):
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
