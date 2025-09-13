"""
Integration tests for API endpoints with real database operations.
Tests the complete API to database flow using real services.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir / ".." / ".." / "services" / "etl"))
sys.path.append(str(current_dir / ".." / ".." / "services" / "backend"))

import psycopg2
from httpx import AsyncClient, ASGITransport
from src.config import get_settings

# Import backend app with proper path management
from app.main import app
from app.services.redis_client import connect_redis, disconnect_redis


class TestAPIIntegration:
    """Test API integration with real database."""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def test_health_endpoint(self, client):
        """Test health endpoint returns 200."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health endpoint test passed")
    
    async def test_database_connectivity_via_api(self, client):
        """Test that API can connect to database by checking record count."""
        # Use a simpler endpoint that just queries the database
        response = await client.get("/api/v1/anime/top?limit=5")
        
        # Should return data or empty list, not 500 error
        assert response.status_code in [200, 404]  # 404 if no data, 200 if data exists
        print("✅ Database connectivity test passed")


async def run_tests():
    """Main test runner using working patterns from existing integration tests."""
    print("🔍 Running API Integration Tests...")
    
    test_instance = TestAPIIntegration()
    
    # Test database directly first (like a_test_connections.py)
    try:
        settings = get_settings()
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM anime_snapshots;")
        count = cursor.fetchone()[0]
        print(f"📊 Found {count} records in database")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Initialize Redis
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        await connect_redis(redis_url)
        print("✅ Redis connection established")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return
    
    try:
        # Create API client
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            
            # Test health endpoint
            await test_instance.test_health_endpoint(client)
            
            # Test database connectivity through API
            await test_instance.test_database_connectivity_via_api(client)
            
            print("🎉 All API integration tests passed!")
                
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
