from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, HTTPException, Response

from ..database import database_engine, test_database_connection
from ..metrics import get_metrics_content
from ..metrics import metrics as metrics_collector
from ..services.redis_client import get_redis_client

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
        # Configuration is always healthy with environment variables
        health_status["checks"]["configuration"] = "healthy"

        # Test database connection
        if test_database_connection():
            health_status["checks"]["database"] = "healthy"
            # Update database connection metrics using centralized function
            metrics_collector.update_connection_metrics(database_engine, None)
        else:
            health_status["checks"]["database"] = "unhealthy"
            health_status["status"] = "degraded"

        # Test Redis connection
        redis_client = get_redis_client()
        if redis_client:
            try:
                await redis_client.ping()
                health_status["checks"]["redis"] = "healthy"
                # Update Redis connection pool metrics using centralized function
                metrics_collector.update_connection_metrics(None, redis_client)
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


@router.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    metrics_content = get_metrics_content()
    return Response(content=metrics_content, media_type="text/plain; version=0.0.4; charset=utf-8")
