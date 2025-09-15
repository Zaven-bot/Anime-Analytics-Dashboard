"""
Unit tests for Redis caching functionality
Tests cache behavior, TTL management, and fallback scenarios
"""

import json
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

import pytest

from services.backend.app.services.redis_client import get_redis_client, disconnect_redis, connect_redis
from services.backend.app.services.analytics import AnalyticsService


class TestRedisCaching:
    """Test Redis caching functionality"""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client with standard behavior"""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None  # Default: cache miss
        mock_redis.set.return_value = True
        mock_redis.expire.return_value = True
        mock_redis.ping.return_value = True
        return mock_redis

    @pytest.fixture 
    def analytics_service(self, mock_redis_client):
        """Analytics service with mocked Redis"""
        return AnalyticsService(redis_client=mock_redis_client)

    def test_cache_key_generation(self, analytics_service):
        """Test that cache keys are generated consistently"""
        # Test cache key generation method
        key1 = analytics_service._get_cache_key("test", param1="value1", param2="value2")
        key2 = analytics_service._get_cache_key("test", param2="value2", param1="value1")
        
        # Keys should be identical regardless of parameter order
        assert key1 == key2
        assert key1.startswith("anime:test:")
        assert "param1:value1" in key1
        assert "param2:value2" in key1

    @pytest.mark.asyncio
    async def test_cache_miss_behavior(self, analytics_service, mock_redis_client):
        """Test behavior when cache key doesn't exist (cache miss)"""
        # Setup: Redis returns None (cache miss)
        mock_redis_client.get.return_value = None
        
        result = await analytics_service._get_cached_data("test:key")
        
        # Should return None for cache miss
        assert result is None
        
        # Redis should have been queried
        mock_redis_client.get.assert_called_once_with("test:key")

    @pytest.mark.asyncio
    async def test_cache_hit_behavior(self, analytics_service, mock_redis_client):
        """Test behavior when cache key exists (cache hit)"""
        # Setup: Redis returns cached data
        cached_data = {"cached": "result", "timestamp": "2025-09-13"}
        mock_redis_client.get.return_value = json.dumps(cached_data)
        
        result = await analytics_service._get_cached_data("test:key")
        
        # Should return cached data
        assert result == cached_data
        mock_redis_client.get.assert_called_once_with("test:key")

    @pytest.mark.asyncio
    async def test_cache_set_with_ttl(self, analytics_service, mock_redis_client):
        """Test caching data with appropriate TTL"""
        test_data = {"result": "data"}
        cache_key = "test:cache:key"
        ttl_seconds = 300
        
        await analytics_service._set_cached_data(cache_key, test_data, ttl_seconds)
        
        # Verify Redis setex call (combines set and expire)
        mock_redis_client.setex.assert_called_once_with(cache_key, ttl_seconds, json.dumps(test_data))

    @pytest.mark.asyncio
    async def test_cache_error_fallback(self, analytics_service, mock_redis_client):
        """Test fallback behavior when Redis operations fail"""
        # Setup: Redis operations raise exceptions
        mock_redis_client.get.side_effect = ConnectionError("Redis connection failed")
        
        # Should not raise exception, should return None gracefully
        result = await analytics_service._get_cached_data("test:key")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_set_error_fallback(self, analytics_service, mock_redis_client):
        """Test fallback when cache setting fails"""
        # Setup: Redis set operation fails
        mock_redis_client.set.side_effect = ConnectionError("Redis connection failed")
        
        test_data = {"test": "data"}
        
        # Should not raise exception
        try:
            await analytics_service._set_cached_data("test:key", test_data, 300)
            # Should complete without error
        except Exception as e:
            pytest.fail(f"Cache set error should be handled gracefully, but got: {e}")

    @pytest.mark.asyncio
    async def test_malformed_cached_data(self, analytics_service, mock_redis_client):
        """Test handling of malformed/corrupted cached data"""
        # Setup: Redis returns invalid JSON
        mock_redis_client.get.return_value = "invalid json data {{"
        
        result = await analytics_service._get_cached_data("test:key")
        
        # Should handle JSON parse error and return None
        assert result is None

    def test_cache_ttl_configuration(self, analytics_service):
        """Test that cache TTL settings are properly configured"""
        # Verify TTL settings exist and are reasonable
        assert hasattr(analytics_service, 'cache_ttl')
        assert isinstance(analytics_service.cache_ttl, dict)
        
        # Check specific TTL values
        assert analytics_service.cache_ttl["database_stats"] == 300  # 5 minutes
        assert analytics_service.cache_ttl["top_rated"] == 600  # 10 minutes
        assert analytics_service.cache_ttl["genre_distribution"] == 1800  # 30 minutes
        assert analytics_service.cache_ttl["seasonal_trends"] == 900  # 15 minutes


class TestRedisConnectionManagement:
    """Test Redis connection lifecycle management"""

    @pytest.mark.asyncio
    async def test_redis_connection_creation(self):
        """Test Redis connection is created properly"""
        with patch('services.backend.app.services.redis_client.redis.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_from_url.return_value = mock_redis
            
            await connect_redis("redis://localhost:6379")
            
            # Verify connection was created with proper configuration
            mock_from_url.assert_called_once()

    @pytest.mark.asyncio 
    async def test_redis_connection_cleanup(self):
        """Test Redis connection is properly cleaned up"""
        # Setup mock Redis client
        mock_redis = AsyncMock()
        
        with patch('services.backend.app.services.redis_client._redis_client', mock_redis):
            await disconnect_redis()
            
            # Verify connection was closed
            mock_redis.aclose.assert_called_once()

    def test_redis_client_getter(self):
        """Test Redis client dependency getter"""
        with patch('services.backend.app.services.redis_client._redis_client', "test_client"):
            result = get_redis_client()
            assert result == "test_client"

    @pytest.mark.asyncio
    async def test_redis_connection_failure_handling(self):
        """Test handling of Redis connection failures"""
        with patch('services.backend.app.services.redis_client.redis.from_url') as mock_from_url:
            # Simulate connection failure
            mock_from_url.side_effect = ConnectionError("Cannot connect to Redis")
            
            # Should raise the connection error after logging
            with pytest.raises(ConnectionError, match="Cannot connect to Redis"):
                await connect_redis("redis://localhost:6379")


class TestAnalyticsServiceCaching:
    """Test caching behavior in Analytics Service methods"""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client"""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None  # Default cache miss
        mock_redis.set.return_value = True
        mock_redis.expire.return_value = True
        return mock_redis

    @pytest.fixture
    def analytics_service(self, mock_redis_client):
        """Analytics service with mocked Redis"""
        service = AnalyticsService(redis_client=mock_redis_client)
        return service

    @pytest.mark.asyncio
    async def test_database_stats_caching(self, analytics_service, mock_redis_client):
        """Test that database stats are cached properly"""
        # Mock database session and query results
        with patch('services.backend.app.services.analytics.get_database_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = mock_session
            
            # Mock different query types used in get_database_stats
            mock_result_scalar = Mock()
            mock_result_scalar.scalar.return_value = 100
            
            # Mock result for latest_date query (should return datetime)
            mock_date_result = Mock()
            mock_date_result.scalar.return_value = datetime(2025, 9, 15, 10, 0, 0)
            
            # Mock the iteration result  
            mock_row = Mock()
            mock_row.snapshot_type = "top_anime"
            mock_row.count = 50
            mock_row.latest_date = None
            mock_result_iter = [mock_row]  # Direct list for iteration
            
            # Set up execute to return different results for different queries
            mock_session.execute.side_effect = [
                mock_result_scalar,    # total_snapshots query
                mock_result_iter,      # snapshot_types query (directly iterable) 
                mock_date_result,      # latest_date query (datetime object)
                mock_result_scalar     # unique_anime query
            ]
            
            # First call should hit database and cache result
            result = await analytics_service.get_database_stats()
            
            # Verify database was queried
            mock_get_session.assert_called_once()
            
            # Verify caching was attempted (should try to setex cache)
            mock_redis_client.setex.assert_called()

    @pytest.mark.asyncio
    async def test_cached_data_returned(self, analytics_service, mock_redis_client):
        """Test that cached data is returned when available"""
        # Setup cached data
        cached_stats = {
            "total_snapshots": 1000,
            "unique_anime": 500,
            "cached": True
        }
        mock_redis_client.get.return_value = json.dumps(cached_stats)
        
        with patch('services.backend.app.services.analytics.get_database_session') as mock_get_session:
            result = await analytics_service.get_database_stats()
            
            # Should return cached data
            assert result == cached_stats
            
            # Database should not be queried since we got cache hit
            mock_get_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_bypass_on_error(self, analytics_service, mock_redis_client):
        """Test that database is queried when cache fails"""
        # Setup cache failure
        mock_redis_client.get.side_effect = ConnectionError("Redis unavailable")
        
        with patch('services.backend.app.services.analytics.get_database_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = mock_session
            
            # Mock different query types used in get_database_stats
            mock_result_scalar = Mock()
            mock_result_scalar.scalar.return_value = 50
            
            # Mock result for latest_date query (should return datetime)
            mock_date_result = Mock()
            mock_date_result.scalar.return_value = datetime(2025, 9, 15, 12, 0, 0)
            
            # Mock the iteration result
            mock_row = Mock()
            mock_row.snapshot_type = "top_anime"
            mock_row.count = 25
            mock_row.latest_date = None
            mock_result_iter = [mock_row]  # Direct list for iteration
            
            # Set up execute to return different results for different queries
            mock_session.execute.side_effect = [
                mock_result_scalar,    # total_snapshots query
                mock_result_iter,      # snapshot_types query (directly iterable)
                mock_date_result,      # latest_date query (datetime object)
                mock_result_scalar     # unique_anime query
            ]
            
            result = await analytics_service.get_database_stats()
            
            # Should fallback to database when cache fails
            mock_get_session.assert_called_once()
            assert result is not None


class TestCacheKeyCollisions:
    """Test cache key generation for collision avoidance"""

    @pytest.fixture
    def analytics_service(self):
        """Analytics service instance"""
        return AnalyticsService()

    def test_different_methods_different_keys(self, analytics_service):
        """Test that different methods generate different cache keys"""
        key1 = analytics_service._get_cache_key("database_stats")
        key2 = analytics_service._get_cache_key("top_rated", snapshot_type="top")
        key3 = analytics_service._get_cache_key("genre_distribution", snapshot_type="top")
        
        # All keys should be different
        assert key1 != key2
        assert key2 != key3
        assert key1 != key3

    def test_same_params_same_key(self, analytics_service):
        """Test that identical parameters produce identical keys"""
        key1 = analytics_service._get_cache_key("test", param1="value1", param2="value2")
        key2 = analytics_service._get_cache_key("test", param1="value1", param2="value2") 
        
        assert key1 == key2

    def test_different_params_different_keys(self, analytics_service):
        """Test that different parameters produce different keys"""
        key1 = analytics_service._get_cache_key("test", param1="value1")
        key2 = analytics_service._get_cache_key("test", param1="value2")
        
        assert key1 != key2


if __name__ == "__main__":
    pytest.main([__file__])
