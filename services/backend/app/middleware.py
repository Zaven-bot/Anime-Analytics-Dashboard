"""
Middleware for automatic metrics collection and request tracing in FastAPI
Tracks HTTP requests, response times, integrates with Prometheus metrics,
and adds correlation IDs for distributed request tracing.
"""

import time
import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .logging_config import setup_logging
from .metrics import metrics

logger = setup_logging("backend-middleware")


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically collect HTTP request metrics and add request tracing.

    Features:
    - Tracks request duration, status codes, and endpoints for Prometheus
    - Generates correlation IDs for distributed tracing
    - Injects structured logging context with request metadata
    - Adds X-Request-ID header to responses for client-side correlation
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request, add correlation ID, collect metrics, and log structured data"""
        start_time = time.time()

        # Generate or extract correlation ID
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())

        # Add request ID to request state for access in route handlers
        request.state.request_id = request_id

        # Configure structured logging context with request metadata
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
        )

        # Log request start
        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            user_agent=request.headers.get("user-agent", "unknown"),
            client_ip=request.client.host if request.client else "unknown",
        )

        # Extract request info
        method = request.method
        endpoint = self._normalize_endpoint(request.url.path)

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time
            status_code = response.status_code

            # Add correlation ID to response headers
            response.headers["x-request-id"] = request_id

            # Record metrics
            metrics.record_http_request(method=method, endpoint=endpoint, status_code=status_code, duration=duration)

            # Log request completion with structured data
            logger.info(
                "request_completed",
                request_id=request_id,
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                duration=duration,
                user_agent=request.headers.get("user-agent", "unknown"),
                response_size=response.headers.get("content-length", "unknown"),
            )

            return response

        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            metrics.record_http_request(method=method, endpoint=endpoint, status_code=500, duration=duration)

            # Log error with correlation context
            logger.error(
                "request_error",
                request_id=request_id,
                method=method,
                endpoint=endpoint,
                duration=duration,
                error=str(e),
                error_type=type(e).__name__,
            )

            raise
        finally:
            # Clear logging context
            structlog.contextvars.clear_contextvars()

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
