"""
ETL Configuration and Settings
Manages environment variables and ETL pipeline configuration.
"""

import os
from typing import List, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict

class ETLSettings(BaseSettings):
    """ETL Pipeline Configuration"""
    
    # Database
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
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
    )
    
    @field_validator('jikan_rate_limit_delay')
    def validate_rate_limit(cls, v):
        """Ensure rate limit is reasonable"""
        if v < 0.1:
            raise ValueError('Rate limit delay must be at least 0.1 seconds')
        return v


# ETL Job Definitions
ETL_JOBS = {
    "top_anime": {
        "endpoint": "/anime",
        "params": {
            "order_by": "score",
            "sort": "desc",
            "limit": 25,
            "rating": ["g", "pg13", "r17", "r", None], # Exclude "pg" (children) and "rx" (adult)
            "status": "complete"  # Only completed anime for top rankings
        },
        "max_pages": 2,  # NEW: To get 50 total (25 * 2 pages)
        "snapshot_type": "top",
        "description": "Top-rated completed anime"
    },
    "seasonal_current": {
        "endpoint": "/anime",
        "params": {
            "order_by": "score",
            "sort": "desc", 
            "limit": 25,
            "rating": ["g", "pg13", "r17", "r", None], # Exclude "pg" (children) and "rx" (adult)
            "status": "airing"  # Currently airing
        },
        "snapshot_type": "seasonal_current",
        "max_pages": None,
        "description": "Currently airing seasonal anime"
    },
    "seasonal_upcoming": {
        "endpoint": "/anime",
        "params": {
            "order_by": "score",
            "sort": "desc",
            "limit": 25,
            "rating": ["g", "pg13", "r17", "r", None], # Exclude "pg" (children) and "rx" (adult)
            "status": "upcoming"
        },
        "max_pages": None,
        "snapshot_type": "upcoming",
        "description": "Upcoming anime releases"
    },
    "popular_movies": {
        "endpoint": "/anime",
        "params": {
            "type": "movie",
            "order_by": "score",
            "rating": ["g", "pg13", "r17", "r", None], # Exclude "pg" (children) and "rx" (adult)
            "sort": "desc",
            "limit": 25
        },
        "max_pages": 1,
        "snapshot_type": "popular_movies",
        "description": "Popular anime movies"
    }
}

def get_settings() -> ETLSettings:
    """Get ETL settings instance"""
    return ETLSettings()
