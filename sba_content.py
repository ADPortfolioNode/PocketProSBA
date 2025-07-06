import requests
from typing import Any, Dict, Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

SBA_BASE_URL = "https://www.sba.gov/api/content/search"

class SBAContentAPI:
    """Client for SBA.gov Content API."""

    def __init__(self, base_url: str = SBA_BASE_URL):
        self.base_url = base_url
        logger.info(f"Initialized SBA Content API client with base URL: {base_url}")

    def search_articles(self, **params) -> Dict[str, Any]:
        """Search articles with optional filters."""
        url = f"{self.base_url}/articles.json"
        return self._get(url, params)

    def get_article(self, article_id: int) -> Dict[str, Any]:
        """Fetch a single article by ID."""
        url = f"{self.base_url}/articles/{article_id}.json"
        return self._get(url)

    def search_blogs(self, **params) -> Dict[str, Any]:
        """Search blogs with optional filters."""
        url = f"{self.base_url}/blogs.json"
        return self._get(url, params)

    def get_blog(self, blog_id: int) -> Dict[str, Any]:
        """Fetch a single blog post by ID."""
        url = f"{self.base_url}/blogs/{blog_id}.json"
        return self._get(url)

    def search_contacts(self, **params) -> Any:
        """Search contacts with optional filters."""
        url = f"{self.base_url}/contacts.json"
        return self._get(url, params)

    def search_courses(self, **params) -> Any:
        """Search courses with optional filters."""
        url = f"{self.base_url}/courses.json"
        return self._get(url, params)

    def get_course(self, pathname: str) -> Any:
        """Fetch a single course by pathname."""
        url = f"{self.base_url}/course.json"
        return self._get(url, {"pathname": pathname})

    def search_documents(self, **params) -> Any:
        """Search documents with optional filters."""
        url = f"{self.base_url}/documents.json"
        return self._get(url, params)

    def search_events(self, **params) -> Any:
        """Search events with optional filters."""
        url = f"{self.base_url}/events.json"
        return self._get(url, params)

    def search_lenders(self, **params) -> Any:
        """Search lenders with optional filters."""
        url = f"{self.base_url}/lenders.json"
        return self._get(url, params)

    def search_offices(self, **params) -> Any:
        """Search offices with optional filters."""
        url = f"{self.base_url}/offices.json"
        return self._get(url, params)

    def get_node(self, node_id: int) -> Any:
        """Fetch a node by ID."""
        url = f"{self.base_url}/node.json"
        return self._get(url, {"id": node_id})

    def search_taxonomys(self, **params) -> Any:
        """Search taxonomys with optional filters."""
        url = f"{self.base_url}/taxonomys.json"
        return self._get(url, params)

    def _get(self, url: str, params: Optional[dict] = None) -> Any:
        """Make a GET request to the SBA Content API.
        
        Includes error handling and logging for better diagnostics.
        """
        try:
            logger.info(f"Making request to SBA Content API: {url} with params {params}")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Successful response from SBA Content API: {url}")
            return data
        except requests.RequestException as e:
            logger.error(f"Error making request to SBA Content API: {url} - {str(e)}")
            return {"error": str(e), "success": False}
        except ValueError as e:
            logger.error(f"Error parsing JSON response from SBA Content API: {url} - {str(e)}")
            return {"error": f"Invalid JSON response: {str(e)}", "success": False}
        except Exception as e:
            logger.error(f"Unexpected error when accessing SBA Content API: {url} - {str(e)}")
            return {"error": f"Unexpected error: {str(e)}", "success": False}
