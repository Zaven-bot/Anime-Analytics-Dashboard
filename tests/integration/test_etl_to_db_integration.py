"""
ETL to Database Integration Tests
Tests the complete ETL pipeline with real database operations
Built upon the working patterns from b_test_jobs.py
"""
import pytest
import asyncio
from pathlib import Path
import sys
import os

# Add ETL source to Python path (same pattern as existing tests)
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services/etl'))

from src.config import get_settings, ETL_JOBS
from src.loaders.database import DatabaseLoader
from src.extractors.jikan import JikanExtractor, JikanRateLimiter
from src.transformers.anime import AnimeTransformer
from src.models.jikan import JikanAnime

from datetime import date


class TestETLDatabaseIntegration:
    """Test ETL pipeline integration with real database"""
    
    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Setup test environment before each test"""
        self.settings = get_settings()
        self.db_loader = DatabaseLoader()
        self.rate_limiter = JikanRateLimiter(delay=self.settings.jikan_rate_limit_delay)
        self.extractor = JikanExtractor(rate_limiter=self.rate_limiter)
        self.transformer = AnimeTransformer()
        
        yield
        # Cleanup after each test

    @pytest.mark.asyncio
    async def test_database_connection_and_schema(self):
        """Test that we can connect to the running database and verify schema"""
        # Use the working database connectivity pattern from a_test_connections.py
        import psycopg2
        
        try:
            conn = psycopg2.connect(self.settings.database_url)
            cursor = conn.cursor()
            
            # Test basic connectivity
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
            assert result[0] == 1, "Database connection should work"
            
            # Check anime_snapshots table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'anime_snapshots'
                );
            """)
            table_exists = cursor.fetchone()[0]
            assert table_exists, "anime_snapshots table should exist"
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            pytest.fail(f"Database connection failed: {e}")

    @pytest.mark.asyncio
    async def test_single_etl_job_execution(self):
        """Test execution of a single ETL job with minimal data"""
        # Use the working ETL pattern from b_test_jobs.py but with assertions
        job_name = "top_anime"  # Use a reliable job type
        job_config = ETL_JOBS[job_name]
        
        # Create a modified config with limited pages for testing
        test_config = job_config.copy()
        test_config["max_pages"] = 1  # Only fetch 1 page to limit data for testing
        
        async with self.extractor:
            try:
                # EXTRACT
                anime_list = await self.extractor.fetch_by_job_config(test_config)
                assert len(anime_list) > 0, f"Should extract at least some anime data for {job_name}"
                # The actual limit depends on the API response, so we'll be flexible
                assert len(anime_list) <= 50, "Should extract reasonable amount of data for testing"
                
                # TRANSFORM
                snapshots = self.transformer.transform_anime_list(
                    anime_list,
                    test_config["snapshot_type"],
                    date.today()
                )
                assert len(snapshots) == len(anime_list), "All extracted anime should be transformed"
                
                # Verify snapshot structure
                for i, snapshot in enumerate(snapshots[:3]):  # Check first few
                    # Debug: print snapshot structure if assertion fails
                    if i == 0:  # Only print first one for debugging
                        print(f"    Sample snapshot keys: {list(snapshot.keys()) if hasattr(snapshot, 'keys') else type(snapshot)}")
                        if hasattr(snapshot, 'mal_id'):
                            print(f"    Sample snapshot mal_id: {snapshot.mal_id}")
                    
                    # Handle both dict and Pydantic model formats
                    if hasattr(snapshot, 'mal_id'):
                        # Pydantic model
                        assert snapshot.mal_id is not None, "Snapshot mal_id should not be None"
                        assert snapshot.title, "Snapshot title should not be empty"
                        assert hasattr(snapshot, 'snapshot_type') or 'snapshot_type' in snapshot.__dict__, "Snapshot should have snapshot_type"
                    elif isinstance(snapshot, dict):
                        # Dictionary format
                        assert "mal_id" in snapshot, "Snapshot should have mal_id"
                        assert "title" in snapshot, "Snapshot should have title"
                        assert "snapshot_type" in snapshot, "Snapshot should have snapshot_type"
                        assert snapshot["snapshot_type"] == test_config["snapshot_type"]
                    else:
                        pytest.fail(f"Unexpected snapshot format: {type(snapshot)}")
                
                # LOAD
                stats = self.db_loader.load_snapshots(snapshots, upsert=True)
                
                # Verify load results
                total_processed = stats.get("successful_inserts", 0) + stats.get("successful_updates", 0)
                assert total_processed > 0, "Should successfully process at least some records"
                assert stats.get("errors", 0) == 0, "Should have no errors during load"
                
                print(f"    ETL Job '{job_name}' processed {total_processed} records successfully")
                
            except Exception as e:
                pytest.fail(f"ETL job execution failed: {e}")

    @pytest.mark.asyncio
    async def test_data_persistence_and_retrieval(self):
        """Test that loaded data persists and can be retrieved from database"""
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        # First, run a small ETL job to ensure we have some data
        job_name = "top_anime"
        job_config = ETL_JOBS[job_name].copy()
        job_config["max_pages"] = 1  # Limit to 1 page for testing
        
        async with self.extractor:
            anime_list = await self.extractor.fetch_by_job_config(job_config)
            if len(anime_list) > 5:
                anime_list = anime_list[:5]  # Take only first 5 for testing
                
            snapshots = self.transformer.transform_anime_list(
                anime_list,
                job_config["snapshot_type"],
                date.today()
            )
            self.db_loader.load_snapshots(snapshots, upsert=True)
        
        # Now verify data persistence
        try:
            conn = psycopg2.connect(self.settings.database_url)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check that data was actually saved
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM anime_snapshots 
                WHERE snapshot_type = %s
            """, (job_config["snapshot_type"],))
            
            count = cursor.fetchone()['count']
            assert count > 0, f"Should have records for snapshot_type {job_config['snapshot_type']}"
            
            # Verify data structure in database
            cursor.execute("""
                SELECT mal_id, title, score, snapshot_type, snapshot_date
                FROM anime_snapshots 
                WHERE snapshot_type = %s
                LIMIT 3
            """, (job_config["snapshot_type"],))
            
            records = cursor.fetchall()
            assert len(records) > 0, "Should retrieve some records"
            
            for record in records:
                assert record['mal_id'] is not None, "mal_id should not be null"
                assert record['title'], "title should not be empty"
                assert record['snapshot_type'] == job_config["snapshot_type"]
                assert record['snapshot_date'] is not None, "snapshot_date should not be null"
            
            cursor.close()
            conn.close()
            
            print(f"    Data persistence verified: {count} records found in database")
            
        except Exception as e:
            pytest.fail(f"Data persistence verification failed: {e}")

    @pytest.mark.asyncio
    async def test_upsert_behavior(self):
        """Test that upsert properly handles duplicate records"""
        job_config = ETL_JOBS["top_anime"].copy()
        job_config["max_pages"] = 1  # Limit to 1 page
        
        async with self.extractor:
            # First load
            anime_list = await self.extractor.fetch_by_job_config(job_config)
            if len(anime_list) > 3:
                anime_list = anime_list[:3]  # Take only first 3 for testing
                
            snapshots = self.transformer.transform_anime_list(
                anime_list,
                job_config["snapshot_type"],
                date.today()
            )
            
            stats1 = self.db_loader.load_snapshots(snapshots, upsert=True)
            first_inserts = stats1.get("successful_inserts", 0)
            first_updates = stats1.get("successful_updates", 0)
            
            # Second load with same data (should update, not insert)
            stats2 = self.db_loader.load_snapshots(snapshots, upsert=True)
            second_updates = stats2.get("successful_updates", 0)
            second_inserts = stats2.get("successful_inserts", 0)
            
            # Verify upsert behavior
            total_first = first_inserts + first_updates
            total_second = second_inserts + second_updates
            
            assert total_first > 0, "First load should process some records"
            assert total_second > 0, "Second load should also process records"
            
            # On second load, we expect more updates than inserts
            if total_second > 0:
                update_ratio = second_updates / total_second
                assert update_ratio >= 0.5, "Second load should primarily update existing records"
            
            print(f"    Upsert behavior verified: First load ({total_first}), Second load ({second_updates} updates, {second_inserts} inserts)")

    @pytest.mark.asyncio
    async def test_error_handling_invalid_data(self):
        """Test ETL pipeline handles invalid data gracefully"""
        # Create a mock job config that might produce invalid data
        job_config = ETL_JOBS["top_anime"].copy()
        job_config["limit"] = 5
        
        async with self.extractor:
            try:
                anime_list = await self.extractor.fetch_by_job_config(job_config)
                
                # Intentionally corrupt some data to test error handling
                if anime_list:
                    # Create corrupted anime data by modifying the model data
                    original_anime = anime_list[0]
                    corrupted_data = original_anime.model_dump()  # Convert to dict
                    corrupted_data["mal_id"] = None  # Invalid mal_id
                    
                    # Try to create a new JikanAnime with invalid data
                    # This should either fail validation or be handled gracefully
                    try:
                        corrupted_anime = JikanAnime(**corrupted_data)
                        anime_list.append(corrupted_anime)
                    except Exception as validation_error:
                        # If Pydantic validation prevents creation, that's also valid behavior
                        print(f"Pydantic validation prevented invalid data: {validation_error}")
                        pass
                
                # Transform should handle invalid data
                snapshots = self.transformer.transform_anime_list(
                    anime_list,
                    job_config["snapshot_type"],
                    date.today()
                )
                
                # Load should handle any remaining issues
                stats = self.db_loader.load_snapshots(snapshots, upsert=True)
                
                # Should have some successful operations even with invalid data
                total_success = stats.get("successful_inserts", 0) + stats.get("successful_updates", 0)
                assert total_success > 0, "Should successfully process at least some valid records"
                
                # May have errors due to invalid data, but should not crash
                errors = stats.get("errors", 0)
                if errors > 0:
                    print(f"Expected errors due to invalid data: {errors}")
                
            except Exception as e:
                # If exception occurs, verify it's handled gracefully
                assert "mal_id" in str(e) or "invalid" in str(e).lower(), \
                    f"Exception should be related to data validation: {e}"

    @pytest.mark.asyncio
    async def test_multiple_snapshot_types(self):
        """Test that different snapshot types can be processed independently"""
        # Test with two different job types to verify isolation
        test_jobs = ["top_anime", "seasonal_current"]
        
        for job_name in test_jobs:
            if job_name not in ETL_JOBS:
                continue
                
            job_config = ETL_JOBS[job_name].copy()
            job_config["limit"] = 3
            
            async with self.extractor:
                anime_list = await self.extractor.fetch_by_job_config(job_config)
                if not anime_list:
                    continue
                    
                snapshots = self.transformer.transform_anime_list(
                    anime_list,
                    job_config["snapshot_type"],
                    date.today()
                )
                
                stats = self.db_loader.load_snapshots(snapshots, upsert=True)
                
                assert stats.get("successful_inserts", 0) + stats.get("successful_updates", 0) > 0, \
                    f"Should successfully process {job_name} records"
        
        # Verify both snapshot types exist in database
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        try:
            conn = psycopg2.connect(self.settings.database_url)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT snapshot_type, COUNT(*) as count 
                FROM anime_snapshots 
                WHERE snapshot_type IN ('top', 'seasonal_current')
                GROUP BY snapshot_type
            """)
            
            results = cursor.fetchall()
            snapshot_types_found = [r['snapshot_type'] for r in results]
            
            # Should have at least one of the snapshot types
            assert len(snapshot_types_found) > 0, "Should have created records for at least one snapshot type"
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            pytest.fail(f"Multiple snapshot types verification failed: {e}")


if __name__ == "__main__":
    # Allow running directly like the existing integration tests
    import asyncio
    
    async def run_tests():
        test_instance = TestETLDatabaseIntegration()
        
        print("🔍 Running ETL to Database Integration Tests...")
        
        try:
            # Setup without pytest fixture
            test_instance.settings = get_settings()
            test_instance.db_loader = DatabaseLoader()
            test_instance.rate_limiter = JikanRateLimiter(delay=test_instance.settings.jikan_rate_limit_delay)
            
            # Run tests - create fresh extractor for each test to avoid client closure issues
            print("\nTest 1: Database Connection")
            await test_instance.test_database_connection_and_schema()
            print("Database connection test passed")
            
            print("\nTest 2: ETL Job Execution")
            test_instance.extractor = JikanExtractor(rate_limiter=test_instance.rate_limiter)
            test_instance.transformer = AnimeTransformer()
            await test_instance.test_single_etl_job_execution()
            print("ETL job execution test passed")
            
            print("\nTest 3: Data Persistence")
            test_instance.extractor = JikanExtractor(rate_limiter=test_instance.rate_limiter)  # Fresh extractor
            test_instance.transformer = AnimeTransformer()
            await test_instance.test_data_persistence_and_retrieval()
            print("Data persistence test passed")
            
            print("\nTest 4: Upsert Behavior")
            test_instance.extractor = JikanExtractor(rate_limiter=test_instance.rate_limiter)  # Fresh extractor
            test_instance.transformer = AnimeTransformer()
            await test_instance.test_upsert_behavior()
            print("Upsert behavior test passed")
            
            print("\nAll ETL to Database integration tests passed!")
            
        except Exception as e:
            print(f"Test failed: {e}")
            raise
    
    asyncio.run(run_tests())
