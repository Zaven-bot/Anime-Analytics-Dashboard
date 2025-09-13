import sys
from datetime import datetime, timezone
from pathlib import Path

import structlog
from fastapi import APIRouter, HTTPException

from ..services.redis_client import get_redis_client

# Add ETL source to Python path
import os
etl_path = Path("/shared/etl") if os.path.exists("/shared/etl") else Path(__file__).parent.parent.parent.parent / "etl"
sys.path.append(str(etl_path))
from src.config import get_settings
from src.loaders.database import DatabaseLoader

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/health")
def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "AnimeDashboard API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with database and Redis connectivity"""
    health_status = {
        "status": "healthy",
        "service": "AnimeDashboard API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "database": "unknown",
            "redis": "unknown",
            "configuration": "unknown",
        },
    }

    try:
        # Test configuration
        settings = get_settings()
        if settings:
            health_status["checks"]["configuration"] = "healthy"
        else:
            health_status["checks"]["configuration"] = "unhealthy"

        # Test database connection
        db_loader = DatabaseLoader()
        if db_loader.test_connection():
            health_status["checks"]["database"] = "healthy"
        else:
            health_status["checks"]["database"] = "unhealthy"
            health_status["status"] = "degraded"

        # Test Redis connection
        redis_client = get_redis_client()
        if redis_client:
            try:
                await redis_client.ping()
                health_status["checks"]["redis"] = "healthy"
            except Exception as e:
                logger.warning("Redis ping failed", error=str(e))
                health_status["checks"]["redis"] = "unhealthy"
                health_status["status"] = "degraded"
        else:
            health_status["checks"]["redis"] = "not_connected"
            health_status["status"] = "degraded"

    except Exception as e:
        logger.error("Health check failed", error=str(e))
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        raise HTTPException(status_code=503, detail=health_status)

    # Overall status
    if any(check not in ["healthy", "not_connected"] for check in health_status["checks"].values()):
        health_status["status"] = "degraded"

    return health_status
