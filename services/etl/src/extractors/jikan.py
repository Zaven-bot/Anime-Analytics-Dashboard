"""
Jikan API Extractor
Handles fetching data from Jikan API with retry logic and rate limiting.
"""

import asyncio  # Async sleep and control flow
import time
from typing import Any, Dict, List, Optional  # Type hints

import httpx  # Async HTTP client
from logging_config import setup_logging
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential  # Retry logic

from ..config import get_settings
from ..models.jikan import JikanAnime, JikanSearchResponse

# Conditionally import ETL metrics to avoid global registry pollution
try:
    from ..metrics_server import etl_metrics

    ETL_METRICS_AVAILABLE = True
except ImportError:
    ETL_METRICS_AVAILABLE = False

from .rate_limiter import JikanRateLimiter

logger = setup_logging("etl-extractors-jikan")


class JikanAPIError(Exception):
    """Custom exception for Jikan API errors"""

    pass


class JikanExtractor:
    """
    Extracts anime data from Jikan API with proper rate limiting and error handling.
    """

    def __init__(self, rate_limiter: Optional[JikanRateLimiter] = None):
        self.settings = get_settings()
        self.rate_limiter = rate_limiter or JikanRateLimiter(delay=self.settings.jikan_rate_limit_delay)
        self.base_url = self.settings.jikan_base_url
        self.client = httpx.AsyncClient(
            timeout=self.settings.jikan_timeout,
            headers={"User-Agent": "AnimeDashboard-ETL/1.0"},
        )

    # Function can pause and let other tasks run
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, JikanAPIError)),
        reraise=True,
    )
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to Jikan API with retry logic and rate limiting.
        """
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()

        # Determine endpoint type for metrics
        endpoint_type = "search" if "anime" == endpoint else "other"

        logger.info("Making Jikan API request", url=url, params=params)

        try:
            # Rate limiting
            await self.rate_limiter.wait()

            response = await self.client.get(url, params=params)
            request_duration = time.time() - start_time

            # Handle rate limiting (429) specially
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning("Rate limited by Jikan API", retry_after=retry_after)

                # Record rate limit metrics
                if ETL_METRICS_AVAILABLE:
                    etl_metrics.record_jikan_request(endpoint_type, 429, request_duration)

                await asyncio.sleep(retry_after)
                raise JikanAPIError("Rate limited")

            # Handle other HTTP errors
            response.raise_for_status()

            data = response.json()
            logger.info("Jikan API request successful", status_code=response.status_code)

            # Record successful request metrics
            if ETL_METRICS_AVAILABLE:
                etl_metrics.record_jikan_request(endpoint_type, response.status_code, request_duration)

            return data

        except httpx.HTTPError as e:  # Network issues, timeouts, etc.
            request_duration = time.time() - start_time
            logger.error("HTTP error during Jikan API request", error=str(e), url=url)

            # Record error metrics (use 0 if no status code available)
            if ETL_METRICS_AVAILABLE:
                etl_metrics.record_jikan_request(endpoint_type, 0, request_duration)

            raise JikanAPIError(f"HTTP error: {e}")
        except Exception as e:  # Bugs in code, weird data, etc.
            request_duration = time.time() - start_time
            logger.error("Unexpected error during Jikan API request", error=str(e), url=url)

            # Record error metrics
            if ETL_METRICS_AVAILABLE:
                etl_metrics.record_jikan_request(endpoint_type, 500, request_duration)

            raise JikanAPIError(f"Unexpected error: {e}")

    async def fetch_anime_search(self, params: Dict[str, Any], max_pages: Optional[int] = None) -> List[JikanAnime]:
        """
        Fetch anime data using the search endpoint.
        Handles pagination automatically.

        Args:
            params: Query parameters for the search
            max_pages: Maximum number of pages to fetch (None for all)

        Returns:
            List of JikanAnime objects
        """
        all_anime = []
        current_page = 1

        while True:
            # Add pagination to params
            page_params = {**params, "page": current_page}

            try:
                response_data = await self._make_request("/anime", page_params)

                # Validate response structure
                try:
                    search_response = JikanSearchResponse(**response_data)
                except Exception as e:
                    logger.error(
                        "Failed to parse Jikan response",
                        error=str(e),
                        page=current_page,
                    )
                    break

                # Add anime from this page
                all_anime.extend(search_response.data)

                logger.info(
                    "Fetched anime page",
                    page=current_page,
                    anime_count=len(search_response.data),
                    total_count=len(all_anime),
                    has_next=search_response.pagination.has_next_page,
                )

                # Check if we should continue
                if not search_response.pagination.has_next_page:
                    break

                if max_pages is not None and current_page >= max_pages:
                    logger.info("Reached maximum page limit", max_pages=max_pages)
                    break

                current_page += 1

            except JikanAPIError as e:
                logger.error("Failed to fetch page", page=current_page, error=str(e))
                break

        logger.info(
            "Completed anime search",
            total_anime=len(all_anime),
            pages_fetched=current_page,
        )
        return all_anime

    async def fetch_top_anime(self, limit: int = 50) -> List[JikanAnime]:
        """Fetch top-rated anime"""
        params = {
            "order_by": "score",
            "sort": "desc",
            "limit": min(limit, 25),  # Jikan API limit per page
            "status": "complete",
        }
        return await self.fetch_anime_search(params, max_pages=limit // 25 + 1)

    async def fetch_seasonal_anime(self, season: str, year: int, limit: int = 25) -> List[JikanAnime]:
        """Fetch seasonal anime"""
        params = {
            "season": season,
            "year": year,
            "order_by": "popularity",
            "sort": "desc",
            "limit": min(limit, 25),
        }
        return await self.fetch_anime_search(params, max_pages=limit // 25 + 1)

    async def fetch_upcoming_anime(self, limit: int = 25) -> List[JikanAnime]:
        """Fetch upcoming anime"""
        params = {
            "status": "upcoming",
            "order_by": "popularity",
            "sort": "desc",
            "limit": min(limit, 25),
        }
        return await self.fetch_anime_search(params, max_pages=limit // 25 + 1)

    async def fetch_by_job_config(self, job_config: Dict[str, Any]) -> List[JikanAnime]:
        """
        Fetch anime using job configuration from config.py
        """
        endpoint = job_config["endpoint"]
        params = job_config["params"]
        max_pages = job_config.get("max_pages")

        if endpoint == "/anime":
            return await self.fetch_anime_search(params, max_pages=max_pages)
        else:
            raise ValueError(f"Unsupported endpoint: {endpoint}")


# Utility function for synchronous usage
def create_extractor() -> JikanExtractor:
    """Create a new JikanExtractor instance"""
    return JikanExtractor()
