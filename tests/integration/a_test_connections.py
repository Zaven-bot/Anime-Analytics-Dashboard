"""Test database and API connectivity"""

import pytest
import asyncio
import psycopg2
import sys
import os

# Add ETL src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../etl'))

from src.config import get_settings
from src.extractors.jikan import JikanExtractor

class TestConnections:
    """Test connectivity to external services"""
    
    def test_database_connection(self):
        """Test database connectivity and basic schema"""
        settings = get_settings()
        
        try:
            conn = psycopg2.connect(settings.database_url)
            cursor = conn.cursor()
            
            # Test basic connectivity
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
            assert result[0] == 1
            
            # Check table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'anime_snapshots'
                );
            """)
            table_exists = cursor.fetchone()[0]
            assert table_exists, "anime_snapshots table does not exist"
            
            # Check required columns exist
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'anime_snapshots'
                AND column_name IN ('mal_id', 'title', 'snapshot_type', 'snapshot_date')
            """)
            columns = [row[0] for row in cursor.fetchall()]
            assert len(columns) == 4, f"Missing required columns. Found: {columns}"
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    async def test_api_connection(self):
        """Test Jikan API connectivity"""
        try:
            extractor = JikanExtractor()
            
            async with extractor:
                # Test minimal API call
                result = await extractor._make_request('/anime', {'limit': 1})
                
                # Verify response structure
                assert 'data' in result
                assert 'pagination' in result
                assert isinstance(result['data'], list)
                
                return True
                
        except Exception as e:
            print(f"API connection failed: {e}")
            return False


if __name__ == "__main__":
    # Run tests directly
    import asyncio
    
    print("🔍 Testing Connections...")
    
    conn_test = TestConnections()
    
    # Test database
    db_ok = conn_test.test_database_connection()
    print(f"Database: {'✅' if db_ok else '❌'}")
    
    # Test API
    api_ok = asyncio.run(conn_test.test_api_connection())
    print(f"API: {'✅' if api_ok else '❌'}")
    
    if db_ok and api_ok:
        print("✅ All connection tests passed!")
    else:
        print("❌ Some connection tests failed!")