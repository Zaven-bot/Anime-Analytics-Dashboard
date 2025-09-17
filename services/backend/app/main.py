"""
AnimeDashboard Backend API
FastAPI application that serves analytics data with direct database access.
"""

from contextlib import asynccontextmanager

from .logging_config import setup_logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import config, test_database_connection
from .middleware import MetricsMiddleware

# Import routers
from .routers import analytics, health
from .services.redis_client import connect_redis, disconnect_redis

# Set up structured logging
logger = setup_logging("backend-main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("AnimeDashboard API starting up")
    print("LIFESPAN STARTING")  # Add this

    try:
        if test_database_connection():
            logger.info("Database connection successful")
        else:
            logger.error("Database connection failed")
    except Exception as e:
        logger.error("Failed to initialize database connection", error=str(e))

    try:
        await connect_redis(config.redis_url)
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

# Add metrics middleware for Prometheus instrumentation
app.add_middleware(MetricsMiddleware)

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
