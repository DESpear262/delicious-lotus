"""Middleware for collecting API metrics and request/response statistics."""

import time
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.logging_config import get_logger

logger = get_logger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting API performance metrics.

    Tracks:
    - Request/response times per endpoint
    - Status code distribution
    - Endpoint usage counts
    - Error rates
    """

    def __init__(self, app: ASGIApp) -> None:
        """Initialize metrics middleware."""
        super().__init__(app)
        self._metrics: dict[str, Any] = {
            "requests_total": 0,
            "requests_by_endpoint": defaultdict(int),
            "requests_by_status": defaultdict(int),
            "response_times": defaultdict(list),
            "errors_total": 0,
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:  # type: ignore[override]
        """
        Process each request and collect metrics.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            Response: HTTP response
        """
        # Start timing
        start_perf = time.perf_counter()

        # Extract endpoint info
        endpoint = f"{request.method} {request.url.path}"

        # Process request
        response = None
        error = None

        try:
            response = await call_next(request)
        except Exception as e:
            error = e
            logger.error(
                f"Error processing request: {e}",
                exc_info=True,
                extra={"endpoint": endpoint, "method": request.method, "path": request.url.path},
            )
            raise
        finally:
            # Calculate response time
            end_perf = time.perf_counter()
            response_time = (end_perf - start_perf) * 1000  # milliseconds

            # Record metrics
            self._record_request_metrics(
                endpoint=endpoint,
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code if response else 500,
                response_time=response_time,
                error=error is not None,
            )

        return response

    def _record_request_metrics(
        self,
        endpoint: str,
        method: str,
        path: str,
        status_code: int,
        response_time: float,
        error: bool,
    ) -> None:
        """
        Record metrics for a request.

        Args:
            endpoint: Endpoint identifier (method + path)
            method: HTTP method
            path: URL path
            status_code: HTTP status code
            response_time: Response time in milliseconds
            error: Whether an error occurred
        """
        # Update counters
        self._metrics["requests_total"] += 1
        self._metrics["requests_by_endpoint"][endpoint] += 1
        self._metrics["requests_by_status"][status_code] += 1

        # Record response time
        self._metrics["response_times"][endpoint].append(response_time)

        # Track errors
        if error or status_code >= 500:
            self._metrics["errors_total"] += 1

        # Log metrics with structured context
        logger.info(
            f"Request processed: {endpoint}",
            extra={
                "method": method,
                "path": path,
                "status_code": status_code,
                "response_time_ms": round(response_time, 2),
                "error": error,
            },
        )

        # Log slow requests (> 1 second)
        if response_time > 1000:
            logger.warning(
                f"Slow request detected: {endpoint} took {response_time:.2f}ms",
                extra={
                    "method": method,
                    "path": path,
                    "response_time_ms": round(response_time, 2),
                },
            )

    def get_metrics(self) -> dict[str, Any]:
        """
        Get collected metrics.

        Returns:
            dict: Metrics including request counts, response times, error rates
        """
        # Calculate response time statistics
        response_time_stats = {}
        for endpoint, times in self._metrics["response_times"].items():
            if times:
                response_time_stats[endpoint] = {
                    "count": len(times),
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "p95": self._calculate_percentile(times, 95),
                    "p99": self._calculate_percentile(times, 99),
                }

        # Calculate error rate
        total_requests = self._metrics["requests_total"]
        error_rate = (
            (self._metrics["errors_total"] / total_requests * 100) if total_requests > 0 else 0.0
        )

        return {
            "total_requests": self._metrics["requests_total"],
            "total_errors": self._metrics["errors_total"],
            "error_rate_percent": round(error_rate, 2),
            "requests_by_endpoint": dict(self._metrics["requests_by_endpoint"]),
            "requests_by_status": dict(self._metrics["requests_by_status"]),
            "response_times": response_time_stats,
        }

    def reset_metrics(self) -> None:
        """Reset all collected metrics."""
        self._metrics = {
            "requests_total": 0,
            "requests_by_endpoint": defaultdict(int),
            "requests_by_status": defaultdict(int),
            "response_times": defaultdict(list),
            "errors_total": 0,
        }
        logger.info("Metrics reset")

    @staticmethod
    def _calculate_percentile(values: list[float], percentile: int) -> float:
        """
        Calculate percentile value from list.

        Args:
            values: List of numeric values
            percentile: Percentile to calculate (0-100)

        Returns:
            float: Percentile value
        """
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * (percentile / 100.0))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]
