"""
Prometheus metrics for AnimeDashboard Backend API
Provides instrumentation for HTTP requests, database operations, and Redis cache operations.
"""

import structlog
from prometheus_client import Counter, Gauge, Histogram, generate_latest

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

# Redis cache metrics
redis_cache_operations_total = Counter(
    "anime_dashboard_redis_cache_operations_total", "Total Redis cache operations", ["operation", "cache_key_type"]
)

# Database metrics
database_connections_active = Gauge(
    "anime_dashboard_database_connections_active", "Current active database connections"
)

database_queries_total = Counter(
    "anime_dashboard_database_queries_total", "Total database queries executed", ["query_type"]
)

analytics_queries_duration_seconds = Histogram(
    "anime_dashboard_analytics_queries_duration_seconds",
    "Analytics query execution time in seconds",
    ["query_type"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

# Redis connection pool metrics
redis_connection_pool_size = Gauge("anime_dashboard_redis_connection_pool_size", "Current Redis connection pool size")

redis_connection_pool_available = Gauge(
    "anime_dashboard_redis_connection_pool_available", "Available connections in Redis pool"
)


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

    def update_database_connections(self, active_connections: int):
        """Update current database connection count"""
        database_connections_active.set(active_connections)

    def update_redis_pool_stats(self, pool_size: int, available_connections: int):
        """Update Redis connection pool metrics"""
        redis_connection_pool_size.set(pool_size)
        redis_connection_pool_available.set(available_connections)

    def update_connection_metrics(self, database_engine=None, redis_client=None):
        """
        Update both database and Redis connection pool metrics
        This is a centralized function to avoid duplication across services
        """
        logger = structlog.get_logger(__name__)

        try:
            # Database connection pool metrics - SQLAlchemy approach
            if database_engine and hasattr(database_engine, "pool"):
                pool = database_engine.pool

                # Get pool statistics (different SQLAlchemy versions have different attributes)
                if hasattr(pool, "size"):
                    pool_size = pool.size()
                    checked_in = pool.checkedin()
                    checked_out = pool.checkedout()
                    self.update_database_connections(checked_out)
                    logger.debug("Database pool stats", size=pool_size, checked_in=checked_in, checked_out=checked_out)
                else:
                    # Fallback: just track that we have a connection when we create sessions
                    self.update_database_connections(0)  # 0 is failure fallback

            # Redis connection pool metrics - AsyncIO Redis approach
            if redis_client and hasattr(redis_client, "connection_pool"):
                pool = redis_client.connection_pool
                # For redis-py async, we need to check differently
                if hasattr(pool, "_created_connections"):
                    created = getattr(pool, "_created_connections", 0)
                    available_connections = getattr(pool, "_available_connections", [])
                    available_count = len(available_connections) if hasattr(available_connections, "__len__") else 0
                    self.update_redis_pool_stats(created, available_count)
                    logger.debug("Redis pool stats", created=created, available=available_count)
                else:
                    # Fallback: assume basic pool status
                    self.update_redis_pool_stats(0, 0)  # 0 is failure fallback

        except Exception as e:
            logger.debug("Connection metrics update failed", error=str(e))
            # Set basic fallback values so metrics aren't always 0
            if database_engine:
                self.update_database_connections(0)
            if redis_client:
                self.update_redis_pool_stats(0, 0)


# Global metrics collector instance
metrics = MetricsCollector()


def get_metrics_content() -> bytes:
    """Return Prometheus metrics in the expected format"""
    return generate_latest()
