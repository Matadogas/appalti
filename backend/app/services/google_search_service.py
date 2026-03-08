"""Google Search service for discovering candidate RFP websites."""
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlparse
import asyncio
import structlog
from sqlalchemy.orm import Session

from app.models.candidate_website import (
    CandidateWebsite,
    WebsiteStatus,
    DiscoveryMethod,
)

logger = structlog.get_logger()


# Procurement-related keywords to detect relevance
PROCUREMENT_KEYWORDS = [
    "bid", "bids", "rfp", "rfq", "ifb", "solicitation", "procurement",
    "purchasing", "contract", "proposal", "current bids", "open bids",
    "bid opportunities", "vendor", "supplier", "construction bids",
    "public works", "capital projects",
]


class GoogleSearchService:
    """Service for discovering procurement websites via Google search.

    This service can use multiple search backends:
    - Google Custom Search API (recommended, requires API key)
    - SerpAPI (alternative, requires API key)
    - Manual search results (for testing)
    """

    def __init__(self, db: Session, api_key: Optional[str] = None):
        """Initialize search service.

        Args:
            db: Database session
            api_key: Google Custom Search API key (optional)
        """
        self.db = db
        self.api_key = api_key

    async def search_and_store(
        self,
        query: str,
        entity_name: str,
        entity_state: str,
        entity_type: str,
        max_results: int = 10,
    ) -> List[CandidateWebsite]:
        """Execute search and store candidate websites.

        Args:
            query: Search query string
            entity_name: Associated entity name
            entity_state: State (NY, NJ, CT)
            entity_type: Entity type (county, city, etc.)
            max_results: Maximum results to process

        Returns:
            List of CandidateWebsite objects created
        """
        logger.info(f"Searching for: {query}")

        # Execute search (placeholder - implement actual search API)
        search_results = await self._execute_search(query, max_results)

        candidates = []

        for rank, result in enumerate(search_results, start=1):
            try:
                # Check if URL already exists
                existing = (
                    self.db.query(CandidateWebsite)
                    .filter(CandidateWebsite.url == result["url"])
                    .first()
                )

                if existing:
                    logger.info(f"URL already exists: {result['url']}")
                    continue

                # Analyze result
                analysis = self._analyze_result(result)

                # Create candidate
                candidate = CandidateWebsite(
                    url=result["url"],
                    domain=urlparse(result["url"]).netloc,
                    title=result.get("title"),
                    description=result.get("snippet"),
                    entity_name=entity_name,
                    entity_state=entity_state,
                    entity_type=entity_type,
                    discovery_method=DiscoveryMethod.GOOGLE_SEARCH,
                    search_query=query,
                    search_rank=rank,
                    relevance_score=analysis["relevance_score"],
                    procurement_keywords_found=analysis["keywords_found"],
                    is_government_domain=analysis["is_gov_domain"],
                    priority=self._calculate_priority(analysis, rank),
                )

                self.db.add(candidate)
                candidates.append(candidate)

                logger.info(
                    f"Added candidate: {result['url']} "
                    f"(score: {analysis['relevance_score']:.1f})"
                )

            except Exception as e:
                logger.error(f"Error processing result: {str(e)}")
                continue

        self.db.commit()

        logger.info(f"Stored {len(candidates)} new candidates for {entity_name}")
        return candidates

    async def _execute_search(
        self, query: str, max_results: int
    ) -> List[Dict[str, Any]]:
        """Execute Google search.

        This is a placeholder. In production, implement one of:
        1. Google Custom Search API
        2. SerpAPI
        3. Scraping (not recommended)

        Args:
            query: Search query
            max_results: Max results to return

        Returns:
            List of search result dicts with url, title, snippet
        """
        # TODO: Implement actual Google Custom Search API integration
        # For now, return empty list as placeholder

        logger.warning("Search API not implemented - returning empty results")
        logger.warning("Implement Google Custom Search API or SerpAPI")

        # Example of what this should return:
        # return [
        #     {
        #         "url": "https://example.gov/procurement",
        #         "title": "Current Bids | Example County",
        #         "snippet": "View current bid opportunities for Example County...",
        #     },
        #     ...
        # ]

        return []

    def _analyze_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze search result for procurement relevance.

        Args:
            result: Search result dict

        Returns:
            Analysis dict with relevance_score, keywords_found, is_gov_domain
        """
        url = result["url"].lower()
        title = (result.get("title") or "").lower()
        snippet = (result.get("snippet") or "").lower()

        # Combine text for analysis
        text = f"{url} {title} {snippet}"

        # Find procurement keywords
        keywords_found = [kw for kw in PROCUREMENT_KEYWORDS if kw in text]

        # Calculate relevance score
        relevance_score = len(keywords_found) * 10.0  # Base score

        # Boost for .gov or .us domains
        parsed = urlparse(url)
        is_gov_domain = parsed.netloc.endswith((".gov", ".us"))
        if is_gov_domain:
            relevance_score += 30.0

        # Boost for procurement in URL path
        if any(kw in parsed.path for kw in ["procurement", "bid", "rfp"]):
            relevance_score += 20.0

        # Boost for "current" or "open" in title/snippet
        if any(word in text for word in ["current", "open", "active"]):
            relevance_score += 10.0

        # Cap at 100
        relevance_score = min(relevance_score, 100.0)

        return {
            "relevance_score": relevance_score,
            "keywords_found": keywords_found,
            "is_gov_domain": is_gov_domain,
        }

    def _calculate_priority(self, analysis: Dict[str, Any], rank: int) -> int:
        """Calculate priority for review (1-10).

        Args:
            analysis: Result analysis
            rank: Search result rank

        Returns:
            Priority score 1-10
        """
        priority = 5  # Default

        # High relevance score
        if analysis["relevance_score"] >= 70:
            priority += 3
        elif analysis["relevance_score"] >= 50:
            priority += 2
        elif analysis["relevance_score"] >= 30:
            priority += 1

        # High in search results
        if rank <= 3:
            priority += 2
        elif rank <= 5:
            priority += 1

        # Government domain
        if analysis["is_gov_domain"]:
            priority += 1

        return min(priority, 10)

    def get_candidates_for_review(
        self, status: WebsiteStatus = WebsiteStatus.DISCOVERED, limit: int = 50
    ) -> List[CandidateWebsite]:
        """Get candidates needing review.

        Args:
            status: Filter by status
            limit: Max results

        Returns:
            List of candidates ordered by priority
        """
        return (
            self.db.query(CandidateWebsite)
            .filter(CandidateWebsite.status == status)
            .order_by(
                CandidateWebsite.priority.desc(),
                CandidateWebsite.relevance_score.desc(),
            )
            .limit(limit)
            .all()
        )

    def verify_candidate(
        self,
        candidate_id: str,
        status: WebsiteStatus,
        verified_by: str,
        notes: Optional[str] = None,
    ):
        """Verify a candidate website.

        Args:
            candidate_id: Candidate UUID
            status: New status (VERIFIED, APPROVED, REJECTED)
            verified_by: User who verified
            notes: Verification notes
        """
        from uuid import UUID

        candidate = (
            self.db.query(CandidateWebsite)
            .filter(CandidateWebsite.id == UUID(candidate_id))
            .first()
        )

        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")

        candidate.status = status
        candidate.verified_at = datetime.utcnow()
        candidate.verified_by = verified_by

        if notes:
            candidate.verification_notes = notes

        self.db.commit()

        logger.info(
            f"Verified candidate {candidate.url} as {status.value} by {verified_by}"
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get discovery statistics.

        Returns:
            Dict with counts by status, state, etc.
        """
        from sqlalchemy import func

        # Count by status
        status_counts = dict(
            self.db.query(
                CandidateWebsite.status, func.count(CandidateWebsite.id)
            )
            .group_by(CandidateWebsite.status)
            .all()
        )

        # Count by state
        state_counts = dict(
            self.db.query(
                CandidateWebsite.entity_state, func.count(CandidateWebsite.id)
            )
            .group_by(CandidateWebsite.entity_state)
            .all()
        )

        # Average relevance score
        avg_score = (
            self.db.query(func.avg(CandidateWebsite.relevance_score))
            .scalar()
        )

        # Government domain percentage
        gov_count = (
            self.db.query(CandidateWebsite)
            .filter(CandidateWebsite.is_government_domain == True)
            .count()
        )
        total = self.db.query(CandidateWebsite).count()

        return {
            "total_candidates": total,
            "by_status": {str(k): v for k, v in status_counts.items()},
            "by_state": {str(k): v for k, v in state_counts.items()},
            "average_relevance_score": float(avg_score or 0),
            "government_domain_percentage": (gov_count / total * 100) if total > 0 else 0,
        }
