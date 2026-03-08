"""Bing Search API client for discovering procurement portals.

Microsoft Bing Search API:
- Free tier: 1,000 searches/month
- 3 searches/second rate limit
- Sign up: https://portal.azure.com
"""
import asyncio
from typing import List, Dict, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

logger = structlog.get_logger()


class BingSearchAPI:
    """Bing Search API client."""

    BASE_URL = "https://api.bing.microsoft.com/v7.0/search"

    def __init__(self, api_key: str):
        """Initialize Bing Search API client.

        Args:
            api_key: Bing Search API key from Azure
        """
        self.api_key = api_key
        self.headers = {
            "Ocp-Apim-Subscription-Key": api_key,
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def search(
        self,
        query: str,
        num_results: int = 10,
        market: str = "en-US",
    ) -> List[Dict]:
        """Execute Bing search query.

        Args:
            query: Search query
            num_results: Number of results to return (max 50)
            market: Market/locale (e.g., "en-US")

        Returns:
            List of search result dicts with url, title, snippet

        Raises:
            httpx.HTTPError: If search fails
        """
        params = {
            "q": query,
            "count": min(num_results, 50),  # Bing max is 50
            "mkt": market,
            "responseFilter": "Webpages",  # Only web results
            "safeSearch": "Off",  # No filtering
        }

        logger.info("Searching Bing", query=query, count=num_results)

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    self.BASE_URL,
                    params=params,
                    headers=self.headers,
                )

                response.raise_for_status()

                data = response.json()

                # Extract web pages
                web_pages = data.get("webPages", {})
                results = []

                for page in web_pages.get("value", []):
                    results.append({
                        "url": page.get("url"),
                        "title": page.get("name"),
                        "snippet": page.get("snippet", ""),
                        "display_url": page.get("displayUrl", ""),
                    })

                logger.info(
                    "Bing search completed",
                    query=query,
                    results_found=len(results),
                )

                return results

            except httpx.HTTPStatusError as e:
                logger.error(
                    "Bing search failed",
                    query=query,
                    status_code=e.response.status_code,
                    error=str(e),
                )
                raise

            except Exception as e:
                logger.error("Bing search error", query=query, error=str(e))
                raise

    async def search_with_rate_limit(
        self,
        query: str,
        num_results: int = 10,
        delay: float = 0.34,  # ~3 requests/second
    ) -> List[Dict]:
        """Search with rate limiting.

        Args:
            query: Search query
            num_results: Number of results
            delay: Delay between requests (seconds)

        Returns:
            List of search results
        """
        results = await self.search(query, num_results)

        # Rate limit: 3 searches/second = ~0.34 second delay
        await asyncio.sleep(delay)

        return results


class BingSearchService:
    """Service for discovering procurement portals using Bing Search."""

    def __init__(self, db, api_key: str):
        """Initialize Bing Search service.

        Args:
            db: Database session
            api_key: Bing Search API key
        """
        self.db = db
        self.client = BingSearchAPI(api_key)

    async def discover_entity_portals(
        self,
        entity_name: str,
        state: str,
        entity_type: str,
        num_queries: int = 3,
    ) -> List[Dict]:
        """Discover procurement portals for an entity.

        Args:
            entity_name: Entity name (e.g., "Bergen County")
            state: State code (e.g., "NJ")
            entity_type: Type (county, city, township, etc.)
            num_queries: Number of search queries to execute

        Returns:
            List of candidate portal dicts
        """
        # Generate search queries
        queries = self._generate_queries(entity_name, state, entity_type)

        # Limit to num_queries
        queries = queries[:num_queries]

        # Execute searches
        all_results = []

        for query in queries:
            results = await self.client.search_with_rate_limit(query, num_results=10)
            all_results.extend(results)

        # Deduplicate by URL
        seen_urls = set()
        unique_results = []

        for result in all_results:
            url = result["url"]
            if url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

        # Score and filter
        candidates = self._score_candidates(
            unique_results,
            entity_name,
            state,
            entity_type,
        )

        return candidates

    def _generate_queries(
        self,
        entity_name: str,
        state: str,
        entity_type: str,
    ) -> List[str]:
        """Generate search queries for an entity.

        Args:
            entity_name: Entity name
            state: State code
            entity_type: Entity type

        Returns:
            List of search queries
        """
        queries = []

        # Query 1: Basic procurement search
        queries.append(f'"{entity_name}" {state} procurement opportunities')

        # Query 2: Construction bids
        queries.append(f'"{entity_name}" {state} construction bids')

        # Query 3: Current RFPs
        queries.append(f'"{entity_name}" {state} current rfp')

        # Query 4: Site-restricted (for government sites)
        if entity_type in ["county", "city", "township"]:
            queries.append(f'site:.gov "{entity_name}" {state} bids')

        # Query 5: Purchasing department
        queries.append(f'"{entity_name}" {state} purchasing department')

        return queries

    def _score_candidates(
        self,
        results: List[Dict],
        entity_name: str,
        state: str,
        entity_type: str,
    ) -> List[Dict]:
        """Score and filter candidate portals.

        Args:
            results: Search results
            entity_name: Entity name
            state: State
            entity_type: Entity type

        Returns:
            Scored candidate dicts
        """
        candidates = []

        procurement_keywords = [
            "procurement", "purchasing", "bid", "bids", "rfp", "rfq",
            "solicitation", "contract", "vendor", "supplier",
        ]

        for result in results:
            url = result["url"]
            title = result["title"].lower()
            snippet = result["snippet"].lower()

            # Calculate relevance score
            score = 0

            # Government domain bonus
            if ".gov" in url or ".us" in url:
                score += 30

            # Procurement keywords in URL
            for keyword in procurement_keywords:
                if keyword in url.lower():
                    score += 20
                    break

            # Procurement keywords in title
            for keyword in procurement_keywords:
                if keyword in title:
                    score += 10
                    break

            # Procurement keywords in snippet
            keyword_count = sum(1 for kw in procurement_keywords if kw in snippet)
            score += min(keyword_count * 5, 30)

            # Entity name match
            if entity_name.lower() in title or entity_name.lower() in snippet:
                score += 20

            # State match
            if state.lower() in url.lower():
                score += 10

            # Priority based on score
            if score >= 50:
                priority = 10
            elif score >= 40:
                priority = 9
            elif score >= 30:
                priority = 8
            elif score >= 20:
                priority = 7
            else:
                priority = 6

            candidates.append({
                "url": url,
                "title": result["title"],
                "snippet": snippet,
                "relevance_score": score,
                "priority": priority,
                "entity_name": entity_name,
                "entity_state": state,
                "entity_type": entity_type,
                "is_government_domain": ".gov" in url or ".us" in url,
            })

        # Sort by relevance score
        candidates.sort(key=lambda c: c["relevance_score"], reverse=True)

        return candidates

    async def discover_all_entities(
        self,
        entities: List[Dict],
        queries_per_entity: int = 3,
    ) -> List[Dict]:
        """Discover portals for multiple entities.

        Args:
            entities: List of entity dicts with name, state, type
            queries_per_entity: Number of queries per entity

        Returns:
            List of all discovered candidates
        """
        all_candidates = []

        for entity in entities:
            entity_name = entity["entity_name"]
            state = entity["state"]
            entity_type = entity["entity_type"]

            logger.info(
                "Discovering portals",
                entity=entity_name,
                state=state,
                type=entity_type,
            )

            candidates = await self.discover_entity_portals(
                entity_name,
                state,
                entity_type,
                num_queries=queries_per_entity,
            )

            all_candidates.extend(candidates)

        return all_candidates
