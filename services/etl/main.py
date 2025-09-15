"""
Main ETL Pipeline Orchestrator
Coordinates the entire Extract -> Transform -> Load process.
"""

import asyncio
import os
import sys
from datetime import date
from typing import Any, Dict, cast

from src.config import ETL_JOBS, get_settings
from src.extractors.jikan import JikanExtractor
from src.loaders.database import DatabaseLoader
from src.logging_config import setup_logging
from src.metrics_server import ETLJobMetrics, etl_metrics
from src.transformers.anime import AnimeTransformer

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# SET UP LOGGING
logger = setup_logging("etl.pipeline")


class ETLPipeline:
    """
    Main ETL Pipeline orchestrator.
    Coordinates extraction, transformation, and loading of anime data.
    """

    def __init__(self):
        self.settings = get_settings()
        self.extractor = None
        self.transformer = AnimeTransformer()
        self.loader = DatabaseLoader()

        # Start metrics server
        try:
            etl_metrics.start_server()
            etl_metrics.update_pipeline_health(True)
        except Exception as e:
            logger.error("Failed to start metrics server", error=str(e))

        # Pipeline statistics
        self.pipeline_stats = {
            "jobs_executed": 0,
            "total_anime_processed": 0,
            "total_snapshots_loaded": 0,
            "errors": [],
        }

    async def run_job(self, job_name: str) -> Dict[str, Any]:
        """
        Run a single ETL job by name.

        Args:
            job_name: Name of the job from ETL_JOBS config

        Returns:
            Dictionary with job execution results
        """
        if job_name not in ETL_JOBS:
            raise ValueError(f"Unknown job: {job_name}")

        job_config = cast(Dict[str, Any], ETL_JOBS[job_name])

        logger.info("Starting ETL job", job_name=job_name, description=job_config.get("description", ""))

        job_result: Dict[str, Any] = {
            "job_name": job_name,
            "status": "failed",
            "extraction": {},
            "transformation": {},
            "loading": {},
            "error": None,
        }

        # Use metrics context manager for job tracking
        with ETLJobMetrics(job_name) as job_metrics:
            try:
                # Initialize extractor
                self.extractor = JikanExtractor()

                async with self.extractor:
                    # EXTRACT
                    logger.info("Starting extraction phase", job_name=job_name)
                    anime_list = await self.extractor.fetch_by_job_config(job_config)

                    job_result["extraction"] = {
                        "anime_count": len(anime_list),
                        "status": "success",
                    }

                    logger.info(
                        "Extraction completed",
                        job_name=job_name,
                        anime_count=len(anime_list),
                    )

                    if not anime_list:
                        logger.warning("No anime data extracted", job_name=job_name)
                        job_result["status"] = "success_no_data"
                        return job_result

                    # TRANSFORM
                    logger.info("Starting transformation phase", job_name=job_name)
                    snapshots = self.transformer.transform_anime_list(
                        anime_list, job_config["snapshot_type"], date.today()
                    )

                    transformation_summary = self.transformer.get_transformation_summary()
                job_result["transformation"] = transformation_summary

                logger.info(
                    "Transformation completed",
                    job_name=job_name,
                    snapshots_count=len(snapshots),
                    **transformation_summary["stats"],
                )

                if not snapshots:
                    logger.warning("No valid snapshots after transformation", job_name=job_name)
                    job_result["status"] = "success_no_valid_data"
                    return job_result

                # LOAD
                logger.info("Starting loading phase", job_name=job_name)
                loading_stats = self.loader.load_snapshots(snapshots, upsert=True)

                job_result["loading"] = loading_stats

                logger.info("Loading completed", job_name=job_name, **loading_stats)

                # Update pipeline statistics
                self.pipeline_stats["jobs_executed"] += 1
                self.pipeline_stats["total_anime_processed"] += len(anime_list)
                self.pipeline_stats["total_snapshots_loaded"] += loading_stats["successful_inserts"]

                # Track processed records for metrics
                job_metrics.add_processed_records(loading_stats["successful_inserts"])

                job_result["status"] = "success"

            # Freak accident
            except Exception as e:
                error_msg = f"ETL job failed: {str(e)}"
                logger.error("ETL job failed", job_name=job_name, error=error_msg)

                job_result["error"] = error_msg
                job_result["status"] = "failed"

                self.pipeline_stats["errors"].append({"job_name": job_name, "error": error_msg})

        return job_result

    async def run_all_jobs(self) -> Dict[str, Any]:
        """
        Run all configured ETL jobs.

        Returns:
            Dictionary with results from all jobs
        """
        logger.info("Starting full ETL pipeline", total_jobs=len(ETL_JOBS))

        pipeline_result: Dict[str, Any] = {"status": "completed", "jobs": {}, "summary": {}}

        # Reset pipeline statistics
        self.pipeline_stats = {
            "jobs_executed": 0,
            "total_anime_processed": 0,
            "total_snapshots_loaded": 0,
            "errors": [],
        }

        # Run each job
        for job_name in ETL_JOBS.keys():
            try:
                job_result = await self.run_job(job_name)
                pipeline_result["jobs"][job_name] = job_result

                logger.info("Job completed", job_name=job_name, status=job_result["status"])

            except Exception as e:
                error_msg = f"Failed to run job {job_name}: {str(e)}"
                logger.error("Job execution failed", job_name=job_name, error=error_msg)

                pipeline_result["jobs"][job_name] = {
                    "status": "failed",
                    "error": error_msg,
                }

                self.pipeline_stats["errors"].append({"job_name": job_name, "error": error_msg})

        # Create summary
        successful_jobs = sum(1 for job in pipeline_result["jobs"].values() if job["status"].startswith("success"))
        failed_jobs = len(ETL_JOBS) - successful_jobs

        pipeline_result["summary"] = {
            "total_jobs": len(ETL_JOBS),
            "successful_jobs": successful_jobs,
            "failed_jobs": failed_jobs,
            "pipeline_stats": self.pipeline_stats,
        }

        if failed_jobs > 0:
            pipeline_result["status"] = "completed_with_errors"

        logger.info("ETL pipeline completed", **pipeline_result["summary"])

        return pipeline_result

    def test_connections(self) -> Dict[str, bool]:
        """Test all external connections"""
        logger.info("Testing ETL connections")

        connections = {
            "database": self.loader.test_connection(),
            "jikan_api": True,  # We'll test this during actual extraction
        }

        logger.info("Connection tests completed", **connections)
        return connections


async def main():
    """Main entry point for ETL pipeline"""
    import argparse

    parser = argparse.ArgumentParser(description="Anime Dashboard ETL Pipeline")
    parser.add_argument("--job", type=str, help="Run specific job")
    parser.add_argument("--test-connections", action="store_true", help="Test connections only")
    parser.add_argument("--list-jobs", action="store_true", help="List available jobs")

    args = parser.parse_args()

    pipeline = ETLPipeline()

    if args.test_connections:
        connections = pipeline.test_connections()
        print("Connection test results:")
        for service, status in connections.items():
            print(f"  {service}: {'✓' if status else '✗'}")
        return

    if args.list_jobs:
        print("Available ETL jobs:")
        for job_name, job_config in ETL_JOBS.items():
            print(f"  {job_name}: {job_config['description']}")
        return

    if args.job:
        # Run specific job
        if args.job not in ETL_JOBS:
            print(f"Error: Unknown job '{args.job}'")
            print("Available jobs:", list(ETL_JOBS.keys()))
            return

        result = await pipeline.run_job(args.job)
        print(f"Job '{args.job}' completed with status: {result['status']}")

        if result["status"] == "failed":
            print(f"Error: {result['error']}")
    else:
        # Run all jobs
        result = await pipeline.run_all_jobs()
        print(f"Pipeline completed with status: {result['status']}")
        print(f"Summary: {result['summary']}")


if __name__ == "__main__":
    asyncio.run(main())
