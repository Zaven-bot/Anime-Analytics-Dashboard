"""Simple integration test runner for ETL pipeline"""

import asyncio
import argparse
import sys
import os

# Add ETL src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../etl'))

from src.config import get_settings, ETL_JOBS
from src.extractors.jikan import JikanExtractor
from src.transformers.anime import AnimeTransformer
from src.loaders.database import DatabaseLoader
from src.extractors.jikan import JikanRateLimiter
from a_test_connections import TestConnections
from datetime import date

async def test_etl_job(job_name: str, rate_limiter: JikanRateLimiter):
    """Test a single ETL job end-to-end"""
    print(f"🔍 Testing ETL job: {job_name}")
    
    job_config = ETL_JOBS[job_name]
    
    # Initialize ETL components
    extractor = JikanExtractor(rate_limiter=rate_limiter)
    transformer = AnimeTransformer()
    loader = DatabaseLoader()
    
    try:
        async with extractor:
            # EXTRACT
            print("  📥 Extracting...")
            anime_list = await extractor.fetch_by_job_config(job_config)
            print(f"     Extracted: {len(anime_list)} records")
            
            if not anime_list:
                print("  ❌ No data extracted!")
                return False
            
            # TRANSFORM
            print("  🔄 Transforming...")
            snapshots = transformer.transform_anime_list(
                anime_list,
                job_config["snapshot_type"],
                date.today()
            )
            print(f"     Transformed: {len(snapshots)} snapshots")
            
            # LOAD
            print("  💾 Loading...")
            stats = loader.load_snapshots(snapshots, upsert=True)
            
            inserts = stats.get("successful_inserts", 0)
            updates = stats.get("successful_updates", 0)
            errors = stats.get("errors", 0)
            
            print(f"     Loaded: {inserts} new + {updates} updated")
            
            if errors > 0:
                print(f"     ⚠️  Errors: {errors}")
                for error in stats.get("error_details", [])[:3]:  # Show first 3 errors
                    print(f"        - {error}")
            
            return errors == 0
            
    except Exception as e:
        print(f"  ❌ ETL job failed: {e}")
        return False

async def run_integration_tests(job_name=None):
    """Run integration tests"""
    print("🚀 Starting Integration Tests")
    print("=" * 50)
    
    # Test connections first
    print("1️⃣ Testing Connections...")
    conn_test = TestConnections()
    
    db_ok = conn_test.test_database_connection()
    if not db_ok:
        print("❌ Database connection failed - stopping tests")
        return False
    
    api_ok = await conn_test.test_api_connection()
    if not api_ok:
        print("❌ API connection failed - stopping tests")
        return False
    
    print("✅ All connections successful!\n")
    
    # Test ETL pipeline
    print("2️⃣ Testing ETL Pipeline...")
    
    settings = get_settings()
    rate_limiter = JikanRateLimiter(delay=settings.jikan_rate_limit_delay)
    
    if job_name:
        # Test specific job
        success = await test_etl_job(job_name, rate_limiter)
        print(f"✅ Job '{job_name}' completed!" if success else f"❌ Job '{job_name}' failed!")
        return success
    else:
        # Test all jobs concurrently

        print("Concurrently testing all ETL jobs...\n")
        job_names = list(ETL_JOBS.keys())
        tasks = {job_name: test_etl_job(job_name, rate_limiter) for job_name in job_names}

        # Run all jobs in parallel, returning them in order
        results_raw = await asyncio.gather(*tasks.values())

        # Reconstruct results dictionary
        results = dict(zip(job_names, results_raw))

        # Summary
        print("\n📊 Integration Test Results:")
        print("=" * 50)
        successful = sum(results.values())
        total = len(results)

        for job_name, success in results.items():
            status = "✅" if success else "❌"
            print(f"{status} {job_name}")

        print(f"\n🎯 Overall: {successful}/{total} jobs successful")
        return successful == total


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Simple ETL Integration Tests")
    parser.add_argument("--job", type=str, help="Test specific job", 
                       choices=list(ETL_JOBS.keys()))
    parser.add_argument("--connections-only", action="store_true", 
                       help="Test connections only")
    
    args = parser.parse_args()
    
    if args.connections_only:
        # Quick connection test only
        conn_test = TestConnections()
        db_ok = conn_test.test_database_connection() 
        api_ok = await conn_test.test_api_connection()
        
        print(f"Database: {'✅' if db_ok else '❌'}")
        print(f"API: {'✅' if api_ok else '❌'}")
        return
    
    # Full integration tests  
    success = await run_integration_tests(args.job)
    
    if success:
        print("\n🎉 All integration tests passed!")
    else:
        print("\n💥 Some integration tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())