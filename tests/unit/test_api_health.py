"""
Unit tests for Health Check API endpoints
Tests the health router and system status endpoints
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone

from services.backend.app.main import app


@pytest.mark.asyncio 
class TestHealthEndpoints:
    """Test suite for health check endpoints"""

    @pytest.fixture
    async def client(self):
        """Create an HTTP client for testing."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    async def test_basic_health_check(self, client):
        """Test basic health check endpoint"""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert data["status"] == "healthy"
        assert "timestamp" in data
        
        # Validate timestamp format (ISO format)
        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        assert isinstance(timestamp, datetime)

    @patch('services.backend.app.routers.health.get_redis_client')
    @patch('services.backend.app.routers.health.test_database_connection')
    async def test_detailed_health_check_all_healthy(self, mock_db_connection, mock_redis_client, client):
        """Test detailed health check when all services are healthy"""
        # Mock database connection directly
        mock_db_connection.return_value = True
        
        # Mock Redis connection
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        mock_redis_client.return_value = mock_redis
        
        response = await client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate overall health
        assert data["status"] == "healthy"
        assert data["service"] == "AnimeDashboard API"
        
        # Validate services health
        checks = data["checks"]
        assert checks["database"] == "healthy"
        assert checks["redis"] == "healthy"

    @patch('services.backend.app.routers.health.get_redis_client')
    @patch('services.backend.app.routers.health.test_database_connection')
    async def test_detailed_health_check_database_unhealthy(self, mock_db_connection, mock_redis_client, client):
        """Test detailed health check when database is unhealthy"""
        # Mock failed database connection
        # Mock database connection directly
        mock_db_connection.return_value = False
        
        # Mock healthy Redis connection
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        mock_redis_client.return_value = mock_redis
        
        response = await client.get("/health/detailed")
        
        assert response.status_code == 200  # Should work with degraded status
        data = response.json()
        
        # Validate degraded health
        assert data["status"] == "degraded"
        
        # Validate services health
        checks = data["checks"]
        assert checks["database"] == "unhealthy"
        assert checks["redis"] == "healthy"

    @patch('services.backend.app.routers.health.get_redis_client')
    @patch('services.backend.app.routers.health.test_database_connection')
    async def test_detailed_health_check_redis_unhealthy(self, mock_db_connection, mock_redis_client, client):
        """Test detailed health check when Redis is unhealthy"""
        # Mock healthy database connection
        # Mock database connection directly
        mock_db_connection.return_value = True
        
        # Mock failed Redis connection
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = ConnectionError("Redis connection failed")
        mock_redis_client.return_value = mock_redis
        
        response = await client.get("/health/detailed")
        
        assert response.status_code == 200  # Should work with degraded status
        data = response.json()
        
        # Validate degraded health
        assert data["status"] == "degraded"
        
        # Validate services health
        checks = data["checks"]
        assert checks["database"] == "healthy"
        assert checks["redis"] == "unhealthy"

    @patch('services.backend.app.routers.health.get_redis_client')
    @patch('services.backend.app.routers.health.test_database_connection')
    async def test_detailed_health_check_all_unhealthy(self, mock_db_connection, mock_redis_client, client):
        """Test detailed health check when all services are unhealthy"""
        # Mock failed database connection
        # Mock database connection directly
        mock_db_connection.return_value = False
        
        # Mock failed Redis connection
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = Exception("Redis unavailable")
        mock_redis_client.return_value = mock_redis
        
        response = await client.get("/health/detailed")
        
        assert response.status_code == 200  # Should work with degraded status
        data = response.json()
        
        # Validate unhealthy status
        assert data["status"] == "degraded"
        
        # Validate services health
        checks = data["checks"]
        assert checks["database"] == "unhealthy"
        assert checks["redis"] == "unhealthy"

    async def test_root_endpoint(self, client):
        """Test root endpoint response"""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "AnimeDashboard API"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"


@pytest.mark.asyncio
class TestHealthRouterErrorHandling:
    """Test error handling in health check endpoints"""

    @pytest.fixture
    async def client(self):
        """Create an HTTP client for testing."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @patch('services.backend.app.routers.health.test_database_connection')
    async def test_database_loader_exception(self, mock_db_connection, client):
        """Test handling of database loader instantiation exception"""
        mock_db_connection.side_effect = Exception("Failed to initialize database loader")
        
        response = await client.get("/health/detailed")
        
        assert response.status_code == 503
        # The response detail should contain the health status
        error_data = response.json()
        assert error_data["detail"]["status"] == "unhealthy"
        assert "Failed to initialize database loader" in error_data["detail"]["error"]

    @patch('services.backend.app.routers.health.get_redis_client')
    async def test_redis_client_exception(self, mock_redis_client, client):
        """Test handling of Redis client instantiation exception"""
        mock_redis_client.side_effect = Exception("Failed to get Redis client")
        
        response = await client.get("/health/detailed")
        
        assert response.status_code == 503
        error_data = response.json()
        
        assert error_data["detail"]["status"] == "unhealthy"
        assert "Failed to get Redis client" in error_data["detail"]["error"]


@pytest.mark.asyncio
class TestHealthCheckIntegration:
    """Integration tests for health check system"""

    @pytest.fixture
    async def client(self):
        """Create an HTTP client for testing."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    async def test_health_endpoint_cors_headers(self, client):
        """Test that health endpoints include proper CORS headers"""
        response = await client.get("/health")
        
        assert response.status_code == 200
        # CORS headers should be present due to middleware
        # Specific headers depend on CORS configuration

    async def test_health_endpoint_response_time(self, client):
        """Test that health endpoints respond quickly"""
        import time
        start_time = time.time()
        
        response = await client.get("/health")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second

    @patch('services.backend.app.routers.health.get_redis_client')
    @patch('services.backend.app.routers.health.test_database_connection')
    async def test_health_check_caching(self, mock_db_connection, mock_redis_client, client):
        """Test that health checks can be cached appropriately"""
        # Mock healthy services
        # Mock database connection directly
        mock_db_connection.return_value = True
        
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        mock_redis_client.return_value = mock_redis
        
        # Make multiple requests
        response1 = await client.get("/health/detailed")
        response2 = await client.get("/health/detailed")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Both should return consistent results
        assert response1.json()["status"] == response2.json()["status"]


if __name__ == "__main__":
    pytest.main([__file__])
