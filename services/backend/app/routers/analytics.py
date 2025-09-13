"""
Analytics API endpoints
Serves aggregated analytics data from the ETL pipeline
"""

import sys
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query

from ..models.responses import (
    AnimeItem,
    DatabaseStatsResponse,
    GenreDistribution,
    GenreDistributionResponse,
    SeasonalTrend,
    SeasonalTrendsResponse,
    SnapshotTypeInfo,
    TopAnimeResponse,
)
from ..services.analytics import AnalyticsService
from ..services.redis_client import get_redis

# Add ETL source to Python path
etl_path = Path(__file__).parent.parent.parent.parent / "etl"
sys.path.append(str(etl_path))


logger = structlog.get_logger(__name__)
router = APIRouter()


async def get_analytics_service(
    redis_client=Depends(get_redis),  # Inject Redis client dependency
) -> AnalyticsService:
    return AnalyticsService(redis_client=redis_client)


@router.get("/stats/overview", response_model=DatabaseStatsResponse)
# @log_timing("database_stats_endpoint")  # Add this line
async def get_database_overview(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Get overall database statistics and snapshot information"""
    try:
        stats = await analytics_service.get_database_stats()

        # Convert to response model
        snapshot_types = [SnapshotTypeInfo(**snapshot_type) for snapshot_type in stats["snapshot_types"]]

        return DatabaseStatsResponse(
            total_snapshots=stats["total_snapshots"],
            unique_anime=stats["unique_anime"],
            latest_snapshot_date=stats["latest_snapshot_date"],
            snapshot_types=snapshot_types,
        )

    except Exception as e:
        logger.error("Failed to get database overview", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve database stats: {str(e)}")


@router.get("/anime/top-rated", response_model=TopAnimeResponse)
async def get_top_rated_anime(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    limit: int = Query(10, ge=1, le=50, description="Number of anime to return"),
    snapshot_type: str = Query(
        "top",
        description="Snapshot type to query",
    ),
):
    """Get top-rated anime from latest snapshots"""
    try:
        anime_data = await analytics_service.get_top_rated_anime(limit=limit, snapshot_type=snapshot_type)

        # Convert to response model
        anime_items = [AnimeItem(**anime) for anime in anime_data]

        return TopAnimeResponse(
            data=anime_items,
            total_results=len(anime_items),
            snapshot_type=snapshot_type,
        )

    except Exception as e:
        logger.error("Failed to get top rated anime", error=str(e), snapshot_type=snapshot_type)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve top rated anime: {str(e)}")


@router.get("/anime/genre-distribution", response_model=GenreDistributionResponse)
async def get_genre_distribution(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    snapshot_type: str = Query("top", description="Snapshot type to analyze"),
):
    """Get genre distribution from latest snapshots with both coverage and
    frequency percentages"""
    try:
        distribution_data = await analytics_service.get_genre_distribution(snapshot_type=snapshot_type)

        # Convert to response model
        genres = [GenreDistribution(**genre) for genre in distribution_data["genres"]]

        return GenreDistributionResponse(
            genres=genres,
            total_anime=distribution_data["total_anime"],
            total_genre_mentions=distribution_data["total_genre_mentions"],
            snapshot_date=distribution_data["snapshot_date"],
            snapshot_type=snapshot_type,
        )

    except Exception as e:
        logger.error(
            "Failed to get genre distribution",
            error=str(e),
            snapshot_type=snapshot_type,
        )
        raise HTTPException(status_code=500, detail=f"Failed to retrieve genre distribution: {str(e)}")


@router.get("/trends/seasonal", response_model=SeasonalTrendsResponse)
async def get_seasonal_trends(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    try:
        trends_data = await analytics_service.get_seasonal_trends()

        # Convert to response model
        trends = [SeasonalTrend(**trend) for trend in trends_data["trends"]]

        return SeasonalTrendsResponse(trends=trends, total_periods=trends_data["total_periods"])

    except Exception as e:
        logger.error("Failed to get seasonal trends", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve seasonal trends: {str(e)}")


@router.get("/health")
async def analytics_health(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Analytics service health check"""
    try:
        # Test database connection through analytics service
        stats = await analytics_service.get_database_stats()
        return {
            "status": "healthy",
            "service": "analytics",
            "total_snapshots": stats["total_snapshots"],
            "unique_anime": stats["unique_anime"],
        }
    except Exception as e:
        logger.error("Analytics health check failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Analytics service unhealthy: {str(e)}")
