"""
AnimeDashboard Backend API
FastAPI application that serves analytics data from the ETL pipeline.
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import existing ETL components
import os
etl_path = Path("/shared/etl") if os.path.exists("/shared/etl") else Path(__file__).parent.parent.parent / "etl"
sys.path.append(str(etl_path))
from src.config import get_settings
from src.loaders.database import DatabaseLoader

# Import routers
from .routers import analytics, health
from .services.redis_client import connect_redis, disconnect_redis

# Add ETL source to Python path so we can import existing components


logging.basicConfig(level=logging.INFO)  # Add this line

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("AnimeDashboard API starting up")
    print("LIFESPAN STARTING")  # Add this

    try:
        db_loader = DatabaseLoader()
        if db_loader.test_connection():
            logger.info("Database connection successful")
        else:
            logger.error("Database connection failed")
    except Exception as e:
        logger.error("Failed to initialize database connection", error=str(e))

    try:
        settings = get_settings()
        await connect_redis(settings.redis_url)
    except Exception as e:
        logger.error("Failed to initialize Redis connection", error=str(e))

    yield  # App runs here

    # Shutdown logic
    logger.info("AnimeDashboard API shutting down")
    await disconnect_redis()
    print("LIFESPAN ENDING")  # Add this


# Initialize FastAPI app
app = FastAPI(
    title="AnimeDashboard API",
    description="Analytics API for anime data from Jikan snapshots",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:3001",  # Alternative React port
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])


# Root endpoint
@app.get("/")
def read_root():
    """Root endpoint with API information"""
    return {
        "message": "AnimeDashboard API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
