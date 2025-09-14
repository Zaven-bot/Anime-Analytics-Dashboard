"""
ETL Configuration and Settings
Manages environment variables and ETL pipeline configuration.
"""

import os

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ETLSettings(BaseSettings):
    """ETL Pipeline Configuration"""

    # Database - defaults adjust based on environment
    database_url: str = "postgresql://anime_user:anime_password@localhost:5433/anime_dashboard"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Jikan API
    jikan_base_url: str = "https://api.jikan.moe/v4"
    jikan_rate_limit_delay: float = 1.5  # seconds between requests
    jikan_max_retries: int = 3
    jikan_timeout: int = 30

    # ETL Configuration
    debug: bool = False
    log_level: str = "INFO"

    # Snapshot Configuration
    top_anime_limit: int = 50
    seasonal_anime_limit: int = 25
    upcoming_anime_limit: int = 25

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    def __init__(self, **kwargs):
        """Initialize settings with environment-aware defaults"""
        super().__init__(**kwargs)

        # Override defaults for GitHub Actions environment
        if os.getenv("GITHUB_ACTIONS"):
            # Use GitHub Actions service containers
            if not os.getenv("DATABASE_URL"):
                self.database_url = "postgresql://test_user:test_password@localhost:5432/test_db"
            if not os.getenv("REDIS_URL"):
                self.redis_url = "redis://localhost:6379/1"  # Use database 1 for tests

            # Be more conservative with API calls in CI
            if not os.getenv("JIKAN_RATE_LIMIT_DELAY"):
                self.jikan_rate_limit_delay = 2.0

            # Reduce limits for faster CI tests
            self.top_anime_limit = 10
            self.seasonal_anime_limit = 5
            self.upcoming_anime_limit = 5

    @field_validator("jikan_rate_limit_delay")
    def validate_rate_limit(cls, v):
        """Ensure rate limit is reasonable"""
        if v < 0.1:
            raise ValueError("Rate limit delay must be at least 0.1 seconds")
        return v


# ETL Job Definitions
ETL_JOBS = {
    "top_anime": {
        "endpoint": "/anime",
        "params": {
            "order_by": "score",
            "sort": "desc",
            "limit": 25,
            "rating": [
                "g",
                "pg13",
                "r17",
                "r",
                None,
            ],  # Exclude "pg" (children) and "rx" (adult)
            "status": "complete",  # Only completed anime for top rankings
        },
        "max_pages": 2,  # NEW: To get 50 total (25 * 2 pages)
        "snapshot_type": "top",
        "description": "Top-rated completed anime",
    },
    "seasonal_current": {
        "endpoint": "/anime",
        "params": {
            "order_by": "score",
            "sort": "desc",
            "limit": 25,
            "rating": [
                "g",
                "pg13",
                "r17",
                "r",
                None,
            ],  # Exclude "pg" (children) and "rx" (adult)
            "status": "airing",  # Currently airing
        },
        "snapshot_type": "seasonal_current",
        "max_pages": None,
        "description": "Currently airing seasonal anime",
    },
    "seasonal_upcoming": {
        "endpoint": "/anime",
        "params": {
            "order_by": "score",
            "sort": "desc",
            "limit": 25,
            "rating": [
                "g",
                "pg13",
                "r17",
                "r",
                None,
            ],  # Exclude "pg" (children) and "rx" (adult)
            "status": "upcoming",
        },
        "max_pages": None,
        "snapshot_type": "upcoming",
        "description": "Upcoming anime releases",
    },
    "popular_movies": {
        "endpoint": "/anime",
        "params": {
            "type": "movie",
            "order_by": "score",
            "rating": [
                "g",
                "pg13",
                "r17",
                "r",
                None,
            ],  # Exclude "pg" (children) and "rx" (adult)
            "sort": "desc",
            "limit": 25,
        },
        "max_pages": 1,
        "snapshot_type": "popular_movies",
        "description": "Popular anime movies",
    },
}


def get_settings() -> ETLSettings:
    """Get ETL settings instance"""
    return ETLSettings()
