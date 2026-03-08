"""Google Custom Search API integration.

To use this, you need:
1. Google Custom Search API key from https://developers.google.com/custom-search
2. Custom Search Engine ID (CSE ID)

Free tier: 100 queries/day
Paid tier: $5 per 1000 queries
"""
from typing import List, Dict, Any, Optional
import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()


class GoogleCustomSearchAPI:
    """Google Custom Search API client."""

    BASE_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, api_key: str, cse_id: str):
        """Initialize API client.

        Args:
            api_key: Google API key
            cse_id: Custom Search Engine ID
        """
        self.api_key = api_key
        self.cse_id = cse_id
        self.client = httpx.AsyncClient(timeout=30.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def search(
        self,
        query: str,
        num_results: int = 10,
        start_index: int = 1,
        site_restrict: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Execute search query.

        Args:
            query: Search query string
            num_results: Number of results (max 10 per request)
            start_index: Starting index for pagination (1-based)
            site_restrict: Restrict to specific site (e.g., ".gov")

        Returns:
            List of search results

        Raises:
            Exception: If API call fails
        """
        params = {
            "key": self.api_key,
            "cx": self.cse_id,
            "q": query,
            "num": min(num_results, 10),  # API max is 10
            "start": start_index,
        }

        # Add site restriction if specified
        if site_restrict:
            params["q"] = f"{query} site:{site_restrict}"

        try:
            logger.info(f"Searching Google: {query}")
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()

            data = response.json()

            # Parse results
            results = []
            for item in data.get("items", []):
                results.append({
                    "url": item.get("link"),
                    "title": item.get("title"),
                    "snippet": item.get("snippet"),
                    "display_link": item.get("displayLink"),
                })

            logger.info(f"Found {len(results)} results for: {query}")
            return results

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error("Rate limit exceeded - API quota exhausted")
                raise Exception("Google API rate limit exceeded")
            logger.error(f"Search failed: {e}")
            raise

        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            raise

    async def search_paginated(
        self,
        query: str,
        total_results: int = 30,
        site_restrict: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search with pagination to get more than 10 results.

        Args:
            query: Search query
            total_results: Total results to fetch (max 100)
            site_restrict: Restrict to site

        Returns:
            Combined list of results
        """
        all_results = []
        num_fetched = 0

        # Fetch in batches of 10
        while num_fetched < total_results:
            batch_size = min(10, total_results - num_fetched)
            start_index = num_fetched + 1

            results = await self.search(
                query, batch_size, start_index, site_restrict
            )

            if not results:
                break  # No more results

            all_results.extend(results)
            num_fetched += len(results)

        return all_results

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class SerpAPIClient:
    """Alternative: SerpAPI client (serpapi.com).

    SerpAPI provides Google search results without needing your own API key.
    Pricing: $50/month for 5,000 searches
    """

    BASE_URL = "https://serpapi.com/search"

    def __init__(self, api_key: str):
        """Initialize SerpAPI client.

        Args:
            api_key: SerpAPI key
        """
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def search(
        self,
        query: str,
        num_results: int = 10,
        start_index: int = 0,
    ) -> List[Dict[str, Any]]:
        """Execute search via SerpAPI.

        Args:
            query: Search query
            num_results: Number of results
            start_index: Starting index

        Returns:
            List of search results
        """
        params = {
            "api_key": self.api_key,
            "q": query,
            "num": num_results,
            "start": start_index,
            "engine": "google",
        }

        try:
            logger.info(f"Searching via SerpAPI: {query}")
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()

            data = response.json()

            # Parse organic results
            results = []
            for item in data.get("organic_results", []):
                results.append({
                    "url": item.get("link"),
                    "title": item.get("title"),
                    "snippet": item.get("snippet"),
                    "display_link": item.get("displayed_link"),
                })

            logger.info(f"Found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"SerpAPI search error: {str(e)}")
            raise

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
