"""
ETL Metrics Server for Prometheus
Provides metrics collection and HTTP server for ETL pipeline monitoring.
"""

import threading
import time
from typing import Optional

import structlog
from prometheus_client import Counter, Gauge, Histogram, generate_latest, start_http_server

logger = structlog.get_logger(__name__)


# ETL Job Metrics
etl_job_duration_seconds = Histogram(
    "anime_dashboard_etl_job_duration_seconds",
    "ETL job execution time in seconds",
    ["job_type"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0, 1800.0],  # up to 30 minutes
)

etl_job_runs_total = Counter("anime_dashboard_etl_job_runs_total", "Total ETL job runs", ["job_type", "status"])

etl_records_processed_total = Counter(
    "anime_dashboard_etl_records_processed_total", "Total records processed by ETL", ["job_type", "operation"]
)

# Jikan API Metrics
jikan_api_requests_total = Counter(
    "anime_dashboard_jikan_api_requests_total", "Total requests to Jikan API", ["status_code", "endpoint_type"]
)

jikan_api_request_duration_seconds = Histogram(
    "anime_dashboard_jikan_api_request_duration_seconds",
    "Jikan API request duration in seconds",
    ["endpoint_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

jikan_rate_limit_hits_total = Counter("anime_dashboard_jikan_rate_limit_hits_total", "Total Jikan API rate limit hits")

# ETL Pipeline Health Metrics
etl_job_records_per_run = Histogram(
    "anime_dashboard_etl_job_records_per_run",
    "Number of records processed per job run",
    ["job_type"],
    buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500],
)

etl_pipeline_health = Gauge(
    "anime_dashboard_etl_pipeline_health", "ETL pipeline health status (1=healthy, 0=unhealthy)"
)

# ETL Database Operations
etl_database_operations_duration_seconds = Histogram(
    "anime_dashboard_etl_database_operations_duration_seconds",
    "Database operation duration in ETL pipeline",
    ["operation_type"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)


class ETLMetricsServer:
    """
    Standalone metrics server for ETL pipeline.
    Runs HTTP server on dedicated port for Prometheus scraping.
    """

    def __init__(self, port: int = 9090):
        self.port = port
        self.server_thread: Optional[threading.Thread] = None
        self.running = False

    def start_server(self):
        """Start the HTTP server for metrics"""
        if self.running:
            logger.warning("Metrics server already running")
            return

        try:
            start_http_server(self.port)
            self.running = True
            logger.info("ETL metrics server started", port=self.port)
        except Exception as e:
            logger.error("Failed to start ETL metrics server", error=str(e), port=self.port)
            raise

    def record_job_start(self, job_type: str):
        """Record when a job starts"""
        logger.debug("Recording job start", job_type=job_type)

    def record_job_completion(self, job_type: str, status: str, duration: float, records_processed: int):
        """Record job completion with metrics"""
        # Record job execution
        etl_job_runs_total.labels(job_type=job_type, status=status).inc()
        etl_job_duration_seconds.labels(job_type=job_type).observe(duration)

        # Record processing volume
        if status == "success":
            etl_records_processed_total.labels(job_type=job_type, operation="processed").inc(records_processed)
            etl_job_records_per_run.labels(job_type=job_type).observe(records_processed)

        logger.info(
            "ETL job metrics recorded",
            job_type=job_type,
            status=status,
            duration=duration,
            records_processed=records_processed,
        )

    def record_jikan_request(self, endpoint_type: str, status_code: int, duration: float):
        """Record Jikan API request metrics"""
        jikan_api_requests_total.labels(status_code=str(status_code), endpoint_type=endpoint_type).inc()

        jikan_api_request_duration_seconds.labels(endpoint_type=endpoint_type).observe(duration)

        # Track rate limiting
        if status_code == 429:
            jikan_rate_limit_hits_total.inc()
            logger.warning("Jikan API rate limit hit", endpoint_type=endpoint_type)

    def record_database_operation(self, operation_type: str, duration: float):
        """Record database operation metrics"""
        etl_database_operations_duration_seconds.labels(operation_type=operation_type).observe(duration)

    def update_pipeline_health(self, is_healthy: bool):
        """Update pipeline health status"""
        etl_pipeline_health.set(1 if is_healthy else 0)

    def get_metrics_content(self) -> bytes:
        """Get metrics in Prometheus format"""
        return generate_latest()


# Global metrics server instance
etl_metrics = ETLMetricsServer()


class ETLJobMetrics:
    """Context manager for tracking individual ETL job execution"""

    def __init__(self, job_type: str):
        self.job_type = job_type
        self.start_time = None
        self.records_processed = 0
        self.status = "failed"

    def __enter__(self):
        self.start_time = time.time()
        etl_metrics.record_job_start(self.job_type)
        logger.info("ETL job tracking started", job_type=self.job_type)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time if self.start_time else 0

        # Determine status based on exception
        if exc_type is None:
            self.status = "success" if self.records_processed > 0 else "success_no_data"
        else:
            self.status = "failed"

        etl_metrics.record_job_completion(self.job_type, self.status, duration, self.records_processed)

        logger.info(
            "ETL job tracking completed",
            job_type=self.job_type,
            status=self.status,
            duration=duration,
            records_processed=self.records_processed,
        )

    def add_processed_records(self, count: int):
        """Add to the count of processed records"""
        self.records_processed += count
