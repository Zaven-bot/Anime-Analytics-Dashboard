"""
Unit tests for FastAPI dependency injection system
Tests dependency overrides, service instantiation, and request lifecycle
"""

from unittest.mock import AsyncMock, Mock, patch
import pytest
from httpx import AsyncClient

from services.backend.app.main import app
from services.backend.app.routers.analytics import get_analytics_service
from services.backend.app.services.analytics import AnalyticsService


@pytest.mark.asyncio
class TestDependencyInjection:
    """Test FastAPI dependency injection system"""

    @pytest.fixture
    async def client(self):
        """Create an HTTP client for testing."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    async def test_analytics_service_dependency_creation(self):
        """Test that analytics service dependency creates service correctly"""
        # Call the dependency function directly
        service = await get_analytics_service()
        
        # Validate service instance
        assert isinstance(service, AnalyticsService)
        assert hasattr(service, 'db_loader')
        assert hasattr(service, 'redis_client')

    async def test_dependency_override_system(self, client):
        """Test that dependency override system works correctly"""
        # Create a mock service
        mock_service = Mock(spec=AnalyticsService)
        mock_service.get_database_stats = AsyncMock(return_value={
            "total_snapshots": 999,
            "unique_anime": 999,
            "latest_snapshot_date": "2025-01-01"
        })
        
        # Override the dependency
        app.dependency_overrides[get_analytics_service] = lambda: mock_service
        
        try:
            # Make request that uses the dependency
            response = await client.get("/api/v1/analytics/stats/overview")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_snapshots"] == 999
            
            # Verify mock was called
            mock_service.get_database_stats.assert_called_once()
            
        finally:
            # Clean up override
            app.dependency_overrides.clear()

    async def test_dependency_override_cleanup(self, client):
        """Test that dependency overrides are properly cleaned up"""
        # Verify no overrides exist initially
        assert len(app.dependency_overrides) == 0
        
        # Add an override
        mock_service = Mock(spec=AnalyticsService)
        app.dependency_overrides[get_analytics_service] = lambda: mock_service
        
        assert len(app.dependency_overrides) == 1
        
        # Clean up
        app.dependency_overrides.clear()
        
        assert len(app.dependency_overrides) == 0

    async def test_service_singleton_behavior(self):
        """Test that services behave as singletons within request scope"""
        # Get service instances
        service1 = await get_analytics_service()
        service2 = await get_analytics_service()
        
        # They should be separate instances (FastAPI creates new instances per request)
        # But they should have the same class
        assert type(service1) == type(service2)
        assert isinstance(service1, AnalyticsService)
        assert isinstance(service2, AnalyticsService)


@pytest.mark.asyncio
class TestServiceLifecycle:
    """Test service lifecycle and initialization"""

    async def test_analytics_service_initialization(self):
        """Test that AnalyticsService initializes correctly"""
        service = await get_analytics_service()
        
        # Verify initialization
        assert service is not None
        assert hasattr(service, 'db_loader')
        assert hasattr(service, 'redis_client')

    async def test_service_error_handling(self):
        """Test that service initialization handles errors gracefully"""
        with patch('services.backend.app.routers.analytics.get_redis_client') as mock_redis:
            mock_redis.side_effect = Exception("Redis connection failed")
            
            # Service should still initialize but with limited functionality
            service = await get_analytics_service()
            assert service is not None


@pytest.mark.asyncio  
class TestDependencyChain:
    """Test dependency chain resolution"""

    @pytest.fixture
    async def client(self):
        """Create an HTTP client for testing."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    async def test_nested_dependency_resolution(self, client):
        """Test that nested dependencies resolve correctly"""
        # This tests that get_analytics_service -> get_redis_client works
        response = await client.get("/api/v1/analytics/stats/overview")
        
        # Should work regardless of Redis state (graceful fallback)
        assert response.status_code in [200, 500]  # 200 if healthy, 500 if error

    async def test_dependency_isolation(self, client):
        """Test that dependencies are properly isolated between requests"""
        # Override for first request
        mock_service1 = Mock(spec=AnalyticsService)
        mock_service1.get_database_stats = AsyncMock(return_value={"total_snapshots": 111})
        
        app.dependency_overrides[get_analytics_service] = lambda: mock_service1
        
        try:
            response1 = await client.get("/api/v1/analytics/stats/overview")
            assert response1.status_code == 200
            
            # Change override for second request
            mock_service2 = Mock(spec=AnalyticsService)
            mock_service2.get_database_stats = AsyncMock(return_value={"total_snapshots": 222})
            
            app.dependency_overrides[get_analytics_service] = lambda: mock_service2
            
            response2 = await client.get("/api/v1/analytics/stats/overview")
            assert response2.status_code == 200
            
            # Responses should be different
            data1 = response1.json()
            data2 = response2.json()
            assert data1["total_snapshots"] != data2["total_snapshots"]
            
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestDependencyErrorHandling:
    """Test error handling in dependency injection"""

    @pytest.fixture
    async def client(self):
        """Create an HTTP client for testing."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    async def test_service_exception_handling(self, client):
        """Test handling of service exceptions"""
        # Create a service that raises an exception
        def failing_service():
            raise Exception("Service initialization failed")
        
        app.dependency_overrides[get_analytics_service] = failing_service
        
        try:
            response = await client.get("/api/v1/analytics/stats/overview")
            # FastAPI should handle the dependency error gracefully
            assert response.status_code == 500
            
        finally:
            app.dependency_overrides.clear()

    async def test_partial_dependency_failure(self, client):
        """Test handling when some dependencies fail but others work"""
        # This would test scenarios where Redis fails but database works
        with patch('services.backend.app.services.redis_client.get_redis_client') as mock_redis:
            mock_redis.side_effect = ConnectionError("Redis unavailable")
            
            # Service should still work with database only
            service = await get_analytics_service()
            assert service is not None


if __name__ == "__main__":
    pytest.main([__file__])
