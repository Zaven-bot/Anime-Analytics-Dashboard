"""
Integration tests for Redis cache operations with real Redis instance.
Tests the complete caching flow using real Redis services.
"""

import asyncio
import os
import sys
from pathlib import Path
import redis.asyncio as redis

# Add paths for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir / ".." / ".." / "services" / "etl"))
sys.path.append(str(current_dir / ".." / ".." / "services" / "backend"))

from src.config import get_settings
from app.services.redis_client import connect_redis, disconnect_redis, get_redis_client


class TestRedisCacheIntegration:
    """Test Redis caching integration with real Redis instance."""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client = None
    
    async def setup_redis(self):
        """Setup Redis connection for testing."""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        await connect_redis(redis_url)
        self.redis_client = get_redis_client()
        assert self.redis_client is not None, "Redis client should be initialized"
        
        # Clear test keys
        await self.redis_client.flushdb()
        print("✅ Redis setup complete")
    
    async def test_basic_redis_operations(self):
        """Test basic Redis set/get operations."""
        # Test string operations
        await self.redis_client.set("test:key", "test_value", ex=30)
        value = await self.redis_client.get("test:key")
        assert value == "test_value"
        
        # Test expiration
        ttl = await self.redis_client.ttl("test:key")
        assert 0 < ttl <= 30
        
        print("✅ Basic Redis operations test passed")
    
    async def test_cache_with_json_data(self):
        """Test caching with JSON-like data."""
        import json
        
        test_data = {
            "total_anime": 1000,
            "cache_hit": True,
            "timestamp": "2025-09-13T17:00:00Z"
        }
        
        # Store as JSON string
        await self.redis_client.set("test:json", json.dumps(test_data), ex=60)
        
        # Retrieve and parse
        cached_json = await self.redis_client.get("test:json")
        cached_data = json.loads(cached_json)
        
        assert cached_data["total_anime"] == 1000
        assert cached_data["cache_hit"] is True
        
        print("✅ JSON cache operations test passed")
    
    async def test_cache_expiration(self):
        """Test cache expiration behavior."""
        # Set a key with 1 second expiration
        await self.redis_client.set("test:expire", "expiring_value", ex=1)
        
        # Should exist immediately
        value = await self.redis_client.get("test:expire")
        assert value == "expiring_value"
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be None after expiration
        value = await self.redis_client.get("test:expire")
        assert value is None
        
        print("✅ Cache expiration test passed")
    
    async def test_concurrent_cache_access(self):
        """Test concurrent access to cache."""
        async def cache_operation(key_suffix):
            key = f"test:concurrent:{key_suffix}"
            await self.redis_client.set(key, f"value_{key_suffix}", ex=30)
            value = await self.redis_client.get(key)
            return value == f"value_{key_suffix}"
        
        # Run multiple concurrent operations
        tasks = [cache_operation(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All operations should succeed
        assert all(results)
        
        print("✅ Concurrent cache access test passed")


async def run_tests():
    """Main test runner for Redis cache integration tests."""
    print("🔍 Running Redis Cache Integration Tests...")
    
    test_instance = TestRedisCacheIntegration()
    
    try:
        # Setup Redis connection
        await test_instance.setup_redis()
        
        # Run tests
        await test_instance.test_basic_redis_operations()
        await test_instance.test_cache_with_json_data()
        await test_instance.test_cache_expiration()
        await test_instance.test_concurrent_cache_access()
        
        print("🎉 All Redis cache integration tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Cleanup Redis connection
        await disconnect_redis()


if __name__ == "__main__":
    asyncio.run(run_tests())
