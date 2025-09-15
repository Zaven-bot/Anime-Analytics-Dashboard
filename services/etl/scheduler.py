#!/usr/bin/env python3
"""
ETL Scheduler - Automated daily data collection
====================================================
This is the MAIN AUTOMATION FILE that replaces manual ETL runs.

WHAT IT DOES:
- Automatically runs all ETL jobs on a schedule
- Handles errors gracefully without crashing
- Logs everything for monitoring
- Can run once immediately or continuously as a daemon

SCHEDULE CONFIGURATION (you can modify these times):
- Full ETL: Every 5 Minutes (all jobs)

USAGE:
- python scheduler.py --run-once     # Run all jobs immediately
- python scheduler.py --daemon       # Run continuously with schedule
- python scheduler.py --test-schedule # Show when jobs will run

REPLACES: Manual "python b_test_jobs.py" commands
"""

import asyncio
import time
from datetime import datetime

import schedule  # Third-party library for scheduling
from main import ETLPipeline

# IMPORT EXISTING ETL COMPONENTS (main.py ETL pipeline)
from src.config import get_settings
from src.logging_config import setup_logging
from src.metrics_server import etl_metrics

# Set up logging once at module level
logger = setup_logging("scheduler")


class ETLScheduler:
    """
    Automated ETL job scheduler
    ===========================

    This class manages the automatic execution of ETL pipeline.
    It's a wrapper around the existing ETLPipeline class with scheduling added.

    KEY METHODS TO CUSTOMIZE:
    - schedule_daily_jobs(): Modify the schedule times here
    - _run_daily_job(): The main job runner (calls existing ETL pipeline)
    - run_scheduler(): The continuous loop that checks for scheduled jobs

    CONFIGURATION POINTS:
    - Schedule times: Currently 2:00 AM for full ETL, 1:00 AM for top anime
    - Job frequency: Every 6 hours for seasonal updates
    - Error handling: Logs errors but doesn't crash the scheduler
    """

    def __init__(self):
        # USE EXISTING ETL PIPELINE
        self.pipeline = ETLPipeline()  # From main.py
        self.settings = get_settings()  # Your existing config

        # Start metrics server for continuous monitoring
        try:
            etl_metrics.start_server()
            etl_metrics.update_pipeline_health(True)
            logger.info("ETL metrics server started successfully")
        except Exception as e:
            logger.error("Failed to start ETL metrics server", error=str(e))

        # CONCURRENCY PROTECTION - prevents multiple jobs from running simultaneously
        self.is_running = False  # Simple flag to prevent job overlap

    async def run_daily_etl(self):
        """
        Run all ETL jobs for daily data collection
        ==========================================

        This is the MAIN WORKHORSE METHOD that:
        1. Tests database/API connections first
        2. Runs ALL ETL jobs using existing pipeline
        3. Logs results and handles errors gracefully

        WHAT IT CALLS:
        - self.pipeline.test_connections() - Existing connection tests
        - self.pipeline.run_all_jobs() - Existing ETL job runner

        ERROR HANDLING:
        - Connection failures: Logs error and stops execution
        - ETL failures: Logs error but doesn't crash scheduler
        - Always returns status for monitoring

        CUSTOMIZE: Modify which jobs run by editing pipeline.run_all_jobs()
        """
        logger.info("Starting daily ETL run", timestamp=datetime.now().isoformat())

        try:
            # STEP 1: TEST CONNECTIONS FIRST
            connections = self.pipeline.test_connections()  # From main.py
            if not all(connections.values()):
                logger.error("Connection test failed", connections=connections)
                return {"status": "failed", "error": "Connection test failed"}

            # STEP 2: RUN ALL ETL JOBS
            result = await self.pipeline.run_all_jobs()  # From main.py

            logger.info("Daily ETL completed", status=result["status"], summary=result.get("summary", ""))

            return result

        except Exception as e:
            # ERROR HANDLING: Log but don't crash the scheduler
            logger.error("Daily ETL failed", error=str(e), exc_info=True)
            return {"status": "failed", "error": str(e)}

    def schedule_daily_jobs(self):
        """
        Schedule ETL jobs to run daily at specified times
        ================================================

        THIS IS WHERE YOU CUSTOMIZE THE SCHEDULE!
        Modify these times to change when jobs run:

        CURRENT SCHEDULE:
        - Every 5 Minutes: Full ETL (all jobs)

        SCHEDULE SYNTAX:
        - schedule.every().day.at("HH:MM") - Daily at specific time
        - schedule.every(N).hours - Every N hours
        - schedule.every().monday.at("HH:MM") - Weekly on specific day

        TO CUSTOMIZE: Change the times or add new schedules here
        """

        # MAIN DAILY ETL - All jobs at Every Hour
        schedule.every(5).minutes.do(self._run_daily_job)
        logger.info("ETL jobs scheduled", daily_full_run="Every 5 Minutes")

    def _run_daily_job(self):
        """
        Wrapper to run async daily ETL in scheduled context
        ===================================================

        This is called by the schedule library when it's time to run the daily ETL.

        WHY THIS EXISTS:
        - The schedule library is synchronous but our ETL is async
        - This bridges the gap by running async code in a sync context
        - Includes concurrency protection to prevent overlapping jobs

        CONCURRENCY PROTECTION:
        - Checks if_running flag to prevent multiple jobs simultaneously
        - This prevents database conflicts and API rate limit issues

        DON'T MODIFY: This is infrastructure code - modify run_daily_etl()
        """
        # PREVENT CONCURRENT JOBS - Critical for database integrity
        if self.is_running:
            logger.warning("ETL job already running, skipping scheduled run")
            return

        self.is_running = True
        try:
            # RUN THE ASYNC ETL IN SYNC CONTEXT
            result = asyncio.run(self.run_daily_etl())
            logger.info("Scheduled daily ETL completed", result=result)
        except Exception as e:
            logger.error("Scheduled daily ETL failed", error=str(e))
        finally:
            # ALWAYS RESET THE FLAG - ensures scheduler can run again
            self.is_running = False

    def _run_specific_job(self, job_name: str):
        """
        Run a specific ETL job (not all jobs)
        =====================================

        This runs only ONE job type instead of the full ETL pipeline.
        Used for frequent updates of specific data types.

        USAGE EXAMPLES:
        - job_name="top_anime" - Only update top anime rankings
        - job_name="seasonal_current" - Only update current season anime
        - job_name="popular_movies" - Only update movie data

        JOBS AVAILABLE (from ETL_JOBS config):
        - All job names from src/config.py ETL_JOBS dictionary

        CUSTOMIZE: Add more specific job schedules in schedule_daily_jobs()
        """
        # PREVENT CONCURRENT JOBS - Same protection as full ETL
        if self.is_running:
            logger.warning("ETL job already running, skipping specific job", job=job_name)
            return

        self.is_running = True
        try:
            # RUN SINGLE JOB using existing pipeline method
            result = asyncio.run(self.pipeline.run_job(job_name))  # From main
            logger.info("Scheduled job completed", job=job_name, result=result)
        except Exception as e:
            logger.error("Scheduled job failed", job=job_name, error=str(e))
        finally:
            # ALWAYS RESET THE FLAG
            self.is_running = False

    def run_scheduler(self):
        """
        Main scheduler loop - runs continuously
        ======================================

        THIS IS THE DAEMON MODE - runs forever checking for scheduled jobs.

        WHAT IT DOES:
        1. Sets up the schedule using schedule_daily_jobs()
        2. Tests initial connections to verify everything works
        3. Runs an infinite loop checking for pending jobs every 60 seconds
        4. Handles errors gracefully without crashing

        USAGE:
        - python scheduler.py --daemon  (runs this method)
        - Docker: command: python scheduler.py --daemon

        ERROR RECOVERY:
        - Connection errors: Logs error, continues running
        - Schedule errors: Waits 5 minutes, then retries
        - Keyboard interrupt: Graceful shutdown

        MONITORING: Check logs for "ETL scheduler daemon" messages
        """
        logger.info("Starting ETL scheduler daemon")

        # SET UP THE SCHEDULE - calls customization point
        self.schedule_daily_jobs()

        # INITIAL CONNECTION TEST - verify everything works at startup
        try:
            connections = self.pipeline.test_connections()  # From main.py
            logger.info("Initial connection test", connections=connections)
        except Exception as e:
            logger.error("Initial connection test failed", error=str(e))

        # MAIN SCHEDULER LOOP - runs forever until stopped
        while True:
            try:
                # CHECK FOR PENDING JOBS - scheduled jobs get executed
                schedule.run_pending()

                # WAIT 60 SECONDS - prevents excessive CPU usage
                time.sleep(60)  # Check every minute for due jobs

            except KeyboardInterrupt:
                # GRACEFUL SHUTDOWN - user pressed Ctrl+C
                logger.info("ETL scheduler stopped by user")
                break
            except Exception as e:
                # ERROR RECOVERY - log error and keep running
                logger.error("Scheduler error", error=str(e))
                time.sleep(300)  # Wait 5 minutes on error before retrying

    def run_once_now(self):
        """
        Run ETL once immediately (for testing/manual trigger)
        ====================================================

        This bypasses the schedule and runs all ETL jobs RIGHT NOW.

        WHEN TO USE:
        - Testing: Make sure everything works before scheduling
        - Manual updates: Force an immediate data refresh
        - Initial setup: Populate database with fresh data
        - Emergency updates: React to important anime news/releases

        USAGE:
        - python scheduler.py --run-once  (calls this method)
        - In code: scheduler.run_once_now()

        REPLACES: Manual "python b_test_jobs.py" workflow

        RETURNS: Full result dictionary with job statuses
        """
        logger.info("Running ETL once immediately")

        # RUN THE SAME DAILY ETL LOGIC - no scheduling involved
        result = asyncio.run(self.run_daily_etl())
        return result


def main():
    """
    Main entry point for ETL scheduler
    =================================

    This handles command-line arguments and routes to appropriate methods.

    COMMAND LINE OPTIONS:
    --run-once: Run ETL immediately and exit (replaces your manual runs)
    --daemon: Run continuously with scheduled jobs (production mode)
    --test-schedule: Show when jobs are scheduled without running them

    USAGE EXAMPLES:
    python scheduler.py --run-once     # Manual run (like  b_test_jobs.py)
    python scheduler.py --daemon       # Continuous automation
    python scheduler.py --test-schedule # Preview schedule times
    python scheduler.py                # Show help/usage
    """
    import argparse

    parser = argparse.ArgumentParser(description="ETL Scheduler - Automated daily data collection")
    parser.add_argument("--run-once", action="store_true", help="Run ETL once immediately and exit")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon (continuous scheduling)")
    parser.add_argument("--test-schedule", action="store_true", help="Test scheduling (shows next run times)")

    args = parser.parse_args()

    # CREATE SCHEDULER INSTANCE
    scheduler = ETLScheduler()

    if args.run_once:
        # IMMEDIATE EXECUTION MODE - replaces your manual ETL runs
        result = scheduler.run_once_now()
        print(f"ETL completed: {result}")

    elif args.test_schedule:
        # PREVIEW MODE - show when jobs will run without executing them
        scheduler.schedule_daily_jobs()
        print("Scheduled jobs:")
        for job in schedule.get_jobs():
            print(f"  - {job.job_func.__name__}: next run at {job.next_run}")

    elif args.daemon:
        # CONTINUOUS MODE - production automation
        scheduler.run_scheduler()

    else:
        # HELP MODE - show usage information
        print("ETL Scheduler Usage:")
        print("  --run-once     Run ETL immediately")
        print("  --daemon       Run continuously with scheduled jobs")
        print("  --test-schedule Show scheduled job times")
        print("\nScheduled times:")
        print("  - Full ETL: Every 5 Minutes")


if __name__ == "__main__":
    main()
