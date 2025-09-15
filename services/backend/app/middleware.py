"""
Middleware for automatic metrics collection in FastAPI
Tracks HTTP requests, response times, and integrates with Prometheus metrics.
"""

import time
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .metrics import metrics

logger = structlog.get_logger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically collect HTTP request metrics for Prometheus.
    Tracks request duration, status codes, and endpoints.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics"""
        start_time = time.time()

        # Extract request info
        method = request.method
        endpoint = self._normalize_endpoint(request.url.path)

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time
            status_code = response.status_code

            # Record metrics
            metrics.record_http_request(method=method, endpoint=endpoint, status_code=status_code, duration=duration)

            # Log request for observability
            logger.info(
                "http_request_completed",
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                duration=duration,
                user_agent=request.headers.get("user-agent", "unknown"),
            )

            return response

        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            metrics.record_http_request(method=method, endpoint=endpoint, status_code=500, duration=duration)

            logger.error("http_request_error", method=method, endpoint=endpoint, duration=duration, error=str(e))

            raise

    def _normalize_endpoint(self, path: str) -> str:
        """
        Normalize endpoint path to reduce cardinality in metrics.
        Replace path parameters with placeholders.
        """
        # Handle common patterns
        if path.startswith("/api/v1/analytics"):
            if path == "/api/v1/analytics/stats/overview":
                return "/api/v1/analytics/stats/overview"
            elif path == "/api/v1/analytics/top-rated":
                return "/api/v1/analytics/top-rated"
            elif path == "/api/v1/analytics/genre-distribution":
                return "/api/v1/analytics/genre-distribution"
            elif path == "/api/v1/analytics/seasonal-trends":
                return "/api/v1/analytics/seasonal-trends"
            else:
                return "/api/v1/analytics/*"

        # Handle health endpoints
        if path.startswith("/health"):
            return "/health"

        # Handle docs
        if path in ["/docs", "/redoc", "/openapi.json"]:
            return path

        # Handle metrics
        if path == "/metrics":
            return "/metrics"

        # Handle root
        if path == "/":
            return "/"

        # Everything else
        return "/*"
