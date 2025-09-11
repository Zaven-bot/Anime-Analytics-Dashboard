"""
Health check endpoints
"""

import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import structlog

# Add ETL source to Python path
etl_path = Path(__file__).parent.parent.parent.parent / "etl"
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
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/health/detailed")
def detailed_health_check():
    """Detailed health check with database connectivity"""
    health_status = {
        "status": "healthy",
        "service": "AnimeDashboard API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "database": "unknown",
            "configuration": "unknown"
        }
    }
    
    try:
        # Test configuration
        settings = get_settings()
        health_status["checks"]["configuration"] = "healthy"
        
        # Test database connection
        db_loader = DatabaseLoader()
        if db_loader.test_connection():
            health_status["checks"]["database"] = "healthy"
        else:
            health_status["checks"]["database"] = "unhealthy"
            health_status["status"] = "degraded"
            
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        raise HTTPException(status_code=503, detail=health_status)
    
    # Overall status
    if any(check != "healthy" for check in health_status["checks"].values()):
        health_status["status"] = "degraded"
    
    return health_status
