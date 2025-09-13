"""
Shared Redis client with FastAPI lifecycle management
"""

import sys
from pathlib import Path
from typing import Optional

import redis.asyncio as redis
import structlog

# ETL config import
import os
etl_path = Path("/shared/etl") if os.path.exists("/shared/etl") else Path(__file__).parent.parent.parent.parent / "etl"
sys.path.append(str(etl_path))
from src.config import get_settings

logger = structlog.get_logger(__name__)

# Global Redis client instance
_redis_client: Optional[redis.Redis] = None


async def connect_redis(redis_url: str) -> redis.Redis:
    """Initialize Redis connection"""
    global _redis_client
    settings = get_settings()
    redis_url = redis_url or settings.redis_url
    try:
        _redis_client = redis.from_url(redis_url, decode_responses=True, health_check_interval=30)
        # Test connection
        await _redis_client.ping()
        logger.info("Redis connection established", url=redis_url)
        return _redis_client
    except Exception as e:
        logger.error("Failed to connect to Redis", error=str(e), url=redis_url)
        _redis_client = None
        raise


async def disconnect_redis():
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        try:
            await _redis_client.aclose()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error("Error closing Redis connection", error=str(e))
        finally:
            _redis_client = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get current Redis client instance"""
    return _redis_client


# FastAPI dependency function
async def get_redis() -> redis.Redis:
    """FastAPI dependency to get Redis client"""
    client = get_redis_client()
    if not client:
        raise RuntimeError("Redis client not initialized")
    return client
