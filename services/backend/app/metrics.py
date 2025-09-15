"""
Prometheus metrics for AnimeDashboard Backend API
Provides instrumentation for HTTP requests, database operations, and Redis cache operations.
"""

from prometheus_client import Counter, Histogram, generate_latest

# HTTP request metrics
http_requests_total = Counter(
    "anime_dashboard_http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

http_request_duration_seconds = Histogram(
    "anime_dashboard_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Redis cache metrics (Application-level cache hit/miss tracking)
redis_cache_operations_total = Counter(
    "anime_dashboard_redis_cache_operations_total", "Total Redis cache operations", ["operation", "cache_key_type"]
)

# Database metrics (Application-level query tracking)
database_queries_total = Counter(
    "anime_dashboard_database_queries_total", "Total database queries executed", ["query_type"]
)

analytics_queries_duration_seconds = Histogram(
    "anime_dashboard_analytics_queries_duration_seconds",
    "Analytics query execution time in seconds",
    ["query_type"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

# Note: Infrastructure metrics (connection pools, memory usage, etc.)
# are now handled by dedicated exporters:
# - PostgreSQL metrics: postgres-exporter (port 9187)
# - Redis metrics: redis-exporter (port 9121)


class MetricsCollector:
    """Centralized metrics collection for the backend API"""

    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        http_requests_total.labels(method=method, endpoint=endpoint, status_code=str(status_code)).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

    def record_cache_operation(self, operation: str, cache_key_type: str):
        """Record Redis cache operation (hit, miss, error)"""
        redis_cache_operations_total.labels(operation=operation, cache_key_type=cache_key_type).inc()

    def record_database_query(self, query_type: str, duration: float):
        """Record database query execution"""
        database_queries_total.labels(query_type=query_type).inc()
        analytics_queries_duration_seconds.labels(query_type=query_type).observe(duration)


# Global metrics collector instance
metrics = MetricsCollector()


def get_metrics_content() -> bytes:
    """Return Prometheus metrics in the expected format"""
    return generate_latest()
