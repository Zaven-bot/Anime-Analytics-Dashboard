"""
Unit tests for FastAPI Analytics API endpoints
Tests the router logic, dependency injection, and response models
"""

import json
from unittest.mock import AsyncMock, Mock, patch
from datetime import date, datetime

import pytest
from httpx import AsyncClient, ASGITransport

# Import our FastAPI app and routers
from services.backend.app.main import app
from services.backend.app.routers.analytics import get_analytics_service
from services.backend.app.services.analytics import AnalyticsService


@pytest.mark.asyncio
class TestAnalyticsEndpoints:
    """Base test class for Analytics API endpoints"""

    @pytest.fixture
    async def client(self):
        """Create an HTTP client for testing."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client"""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None  # Default: no cache hit
        mock_redis.set.return_value = True
        mock_redis.expire.return_value = True
        return mock_redis

    @pytest.fixture
    def mock_analytics_service(self, mock_redis_client):
        """Mock AnalyticsService with test data"""
        service = Mock(spec=AnalyticsService)
        service.redis_client = mock_redis_client
        
        # Mock database stats response
        service.get_database_stats = AsyncMock(return_value={
            "total_snapshots": 1250,
            "unique_anime": 892,
            "latest_snapshot_date": "2025-09-13",
            "snapshot_types": [
                {"type": "top", "count": 425, "latest_date": "2025-09-13"},
                {"type": "airing", "count": 325, "latest_date": "2025-09-13"},
                {"type": "upcoming", "count": 275, "latest_date": "2025-09-13"},
                {"type": "movie", "count": 225, "latest_date": "2025-09-13"}
            ]
        })
        
        # Mock top anime response
        service.get_top_rated_anime = AsyncMock(return_value={
            "data": [
                {
                    "id": 5114,
                    "title": "Fullmetal Alchemist: Brotherhood",
                    "score": 9.1,
                    "rank": 1,
                    "popularity": 3,
                    "genres": ["Action", "Adventure", "Drama", "Fantasy", "Military"],
                    "synopsis": "Edward Elric, a young, brilliant alchemist...",
                    "episodes": 64,
                    "status": "Finished Airing",
                    "airing_start": "2009-04-05",
                    "airing_end": "2010-07-04"
                }
            ],
            "pagination": {
                "last_visible_page": 1,
                "has_next_page": False,
                "current_page": 1,
                "items": {"count": 1, "total": 1, "per_page": 10}
            }
        })
        
        # Mock genre distribution response
        service.get_genre_distribution = AsyncMock(return_value=[
            {"genre": "Action", "count": 145, "percentage": 25.5},
            {"genre": "Comedy", "count": 98, "percentage": 17.2},
            {"genre": "Drama", "count": 87, "percentage": 15.3}
        ])
        
        # Mock seasonal trends response
        service.get_seasonal_trends = AsyncMock(return_value=[
            {"year": 2023, "season": "Spring", "anime_count": 45, "avg_score": 7.2},
            {"year": 2023, "season": "Summer", "anime_count": 52, "avg_score": 7.1},
            {"year": 2023, "season": "Fall", "anime_count": 48, "avg_score": 7.4}
        ])
        
        return service

    async def test_get_database_overview_success(self, client, mock_analytics_service):
        """Test successful database overview retrieval"""
        # Override the dependency for this test
        app.dependency_overrides[get_analytics_service] = lambda: mock_analytics_service
        
        response = await client.get("/api/v1/analytics/stats/overview")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert data["total_snapshots"] == 1250
        assert data["unique_anime"] == 892
        assert data["latest_snapshot_date"] == "2025-09-13"
        assert len(data["snapshot_types"]) == 4
        
        # Validate snapshot type structure
        snapshot_type = data["snapshot_types"][0]
        assert snapshot_type["type"] == "top"
        assert snapshot_type["count"] == 425
        assert snapshot_type["latest_date"] == "2025-09-13"
        
        # Clean up dependency override
        app.dependency_overrides.clear()

import json
from unittest.mock import AsyncMock, Mock, patch
from datetime import date, datetime

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

# Import our FastAPI app and routers
from services.backend.app.main import app
from services.backend.app.routers.analytics import get_analytics_service
from services.backend.app.services.analytics import AnalyticsService


class TestAnalyticsEndpoints:
    """Test suite for analytics API endpoints"""

    @pytest.fixture
    async def client(self):
        """Create an HTTP client for testing."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client"""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None  # Default: no cache hit
        mock_redis.set.return_value = True
        mock_redis.expire.return_value = True
        return mock_redis

    @pytest.fixture
    def mock_analytics_service(self, mock_redis_client):
        """Mock AnalyticsService with test data"""
        service = Mock(spec=AnalyticsService)
        service.redis_client = mock_redis_client
        
        # Mock database stats response
        service.get_database_stats = AsyncMock(return_value={
            "total_snapshots": 1250,
            "unique_anime": 892,
            "latest_snapshot_date": "2025-09-13",
            "snapshot_types": [
                {"type": "top", "count": 425, "latest_date": "2025-09-13"},
                {"type": "airing", "count": 325, "latest_date": "2025-09-13"},
                {"type": "upcoming", "count": 275, "latest_date": "2025-09-13"},
                {"type": "movie", "count": 225, "latest_date": "2025-09-13"}
            ]
        })
        
        # Mock top anime response
        service.get_top_rated_anime = AsyncMock(return_value=[
            {
                "mal_id": 5114,
                "title": "Fullmetal Alchemist: Brotherhood",
                "score": 9.64,
                "rank": 1,
                "popularity": 3,
                "genres": ["Action", "Adventure", "Drama", "Fantasy", "Military"],
                "studios": ["Bones"]
            },
            {
                "mal_id": 28977,
                "title": "Gintama°",
                "score": 9.25,
                "rank": 2,
                "popularity": 154,
                "genres": ["Comedy", "Drama", "Action"],
                "studios": ["Bandai Namco Pictures"]
            }
        ])
        
        # Mock genre distribution response
        service.get_genre_distribution = AsyncMock(return_value={
            "genres": [
                {
                    "genre": "Action",
                    "anime_count": 45,
                    "mention_count": 45,
                    "anime_percentage": 18.0,
                    "mention_percentage": 12.5
                },
                {
                    "genre": "Drama", 
                    "anime_count": 38,
                    "mention_count": 38,
                    "anime_percentage": 15.2,
                    "mention_percentage": 10.6
                }
            ],
            "total_anime": 250,
            "total_genre_mentions": 360,
            "snapshot_date": "2025-09-13",
            "snapshot_type": "top"
        })
        
        # Mock seasonal trends response
        service.get_seasonal_trends = AsyncMock(return_value={
            "trends": [
                {
                    "season": "fall",
                    "year": 2024,
                    "anime_count": 25,
                    "avg_score": 7.45,
                    "total_scored_by": 125000,
                    "avg_scored_by": 5000.0,
                    "avg_rank": 1500.0,
                    "avg_popularity": 800.0,
                    "total_members": 750000,
                    "avg_members": 30000.0,
                    "total_favorites": 15000,
                    "avg_favorites": 600.0,
                    "latest_snapshot_date": "2025-09-13"
                }
            ],
            "total_periods": 12
        })
        
        return service

    @pytest.fixture(autouse=True)
    def override_dependencies(self, mock_analytics_service):
        """Override FastAPI dependencies for testing"""
        app.dependency_overrides[get_analytics_service] = lambda: mock_analytics_service


class TestDatabaseStatsEndpoint(TestAnalyticsEndpoints):
    """Test /stats/overview endpoint"""

    async def test_get_database_overview_success(self, client):
        """Test successful database overview retrieval"""
        response = await client.get("/api/v1/analytics/stats/overview")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert data["total_snapshots"] == 1250
        assert data["unique_anime"] == 892
        assert data["latest_snapshot_date"] == "2025-09-13"
        assert len(data["snapshot_types"]) == 4
        
        # Validate snapshot type structure
        snapshot_type = data["snapshot_types"][0]
        assert snapshot_type["type"] == "top"
        assert snapshot_type["count"] == 425
        assert snapshot_type["latest_date"] == "2025-09-13"

    async def test_get_database_overview_service_error(self, client, mock_analytics_service):
        """Test database overview with service error"""
        mock_analytics_service.get_database_stats.side_effect = Exception("Database connection failed")
        
        response = await client.get("/api/v1/analytics/stats/overview")
        assert response.status_code == 500
        
        error_data = response.json()
        assert "Database connection failed" in error_data["detail"]


@pytest.mark.asyncio
class TestTopAnimeEndpoint(TestAnalyticsEndpoints):
    """Test /anime/top endpoint"""

    async def test_get_top_anime_success(self, client, mock_analytics_service):
        """Test successful top anime retrieval"""
        app.dependency_overrides[get_analytics_service] = lambda: mock_analytics_service
        
        response = await client.get("/api/v1/analytics/anime/top-rated?snapshot_type=top&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "data" in data
        assert len(data["data"]) >= 1
        
        # Validate anime item structure
        anime = data["data"][0]
        assert anime["mal_id"] == 5114
        assert anime["title"] == "Fullmetal Alchemist: Brotherhood"
        assert anime["score"] == 9.64
        assert anime["rank"] == 1
        
        app.dependency_overrides.clear()

    async def test_get_top_anime_with_filters(self, client, mock_analytics_service):
        """Test top anime with query parameters"""
        app.dependency_overrides[get_analytics_service] = lambda: mock_analytics_service
        
        response = await client.get("/api/v1/analytics/anime/top-rated?snapshot_type=airing&limit=5&min_score=8.0")
        
        assert response.status_code == 200
        app.dependency_overrides.clear()

    async def test_get_top_anime_invalid_snapshot_type(self, client):
        """Test top anime with invalid snapshot type"""
        # Mock the service to return empty results for invalid snapshot types
        mock_service = Mock(spec=AnalyticsService)
        mock_service.get_top_rated_anime = AsyncMock(return_value=[])
        
        app.dependency_overrides[get_analytics_service] = lambda: mock_service
        
        try:
            response = await client.get("/api/v1/analytics/anime/top-rated?snapshot_type=invalid")
            
            # Service handles invalid types gracefully and returns empty results
            assert response.status_code == 200
            data = response.json()
            assert data["data"] == []  # Empty results
            
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestGenreDistributionEndpoint(TestAnalyticsEndpoints):
    """Test /genres/distribution endpoint"""

    async def test_get_genre_distribution_success(self, client, mock_analytics_service):
        """Test successful genre distribution retrieval"""
        app.dependency_overrides[get_analytics_service] = lambda: mock_analytics_service
        
        response = await client.get("/api/v1/analytics/anime/genre-distribution?snapshot_type=top")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "genres" in data
        assert len(data["genres"]) >= 1
        
        # Validate genre structure  
        genre = data["genres"][0]
        assert genre["genre"] == "Action"
        assert genre["anime_count"] == 45
        assert genre["anime_percentage"] == 18.0
        
        app.dependency_overrides.clear()


@pytest.mark.asyncio  
class TestSeasonalTrendsEndpoint(TestAnalyticsEndpoints):
    """Test /seasonal-trends endpoint"""

    async def test_get_seasonal_trends_success(self, client, mock_analytics_service):
        """Test successful seasonal trends retrieval"""
        app.dependency_overrides[get_analytics_service] = lambda: mock_analytics_service
        
        response = await client.get("/api/v1/analytics/trends/seasonal")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "trends" in data
        assert len(data["trends"]) >= 1
        
        # Validate trend structure
        trend = data["trends"][0]
        assert trend["season"] == "fall"  
        assert trend["year"] == 2024
        assert trend["anime_count"] == 25
        assert trend["avg_score"] == 7.45
        
        app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestErrorHandling(TestAnalyticsEndpoints):
    """Test error handling scenarios"""

    async def test_database_connection_error(self, client, mock_analytics_service):
        """Test handling of database connection errors"""
        mock_analytics_service.get_database_stats.side_effect = Exception("Database connection failed")
        app.dependency_overrides[get_analytics_service] = lambda: mock_analytics_service
        
        response = await client.get("/api/v1/analytics/stats/overview")
        assert response.status_code == 500
        
        app.dependency_overrides.clear()

    async def test_redis_connection_error(self, client, mock_analytics_service):
        """Test handling of Redis connection errors"""
        mock_analytics_service.get_top_rated_anime.side_effect = Exception("Redis connection failed")
        app.dependency_overrides[get_analytics_service] = lambda: mock_analytics_service
        
        response = await client.get("/api/v1/analytics/anime/top-rated")
        assert response.status_code == 500
        
        app.dependency_overrides.clear()
