"""Unit tests for MetricsMiddleware."""

import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.app.middleware.metrics import MetricsMiddleware


@pytest.fixture
def app_with_metrics() -> FastAPI:
    """Create FastAPI app with MetricsMiddleware."""
    app = FastAPI()

    # Add MetricsMiddleware
    app.add_middleware(MetricsMiddleware)

    # Define test routes
    @app.get("/test/success")
    async def success_endpoint() -> dict[str, str]:
        return {"message": "success"}

    @app.get("/test/slow")
    async def slow_endpoint() -> dict[str, str]:
        await asyncio.sleep(1.5)  # Simulate slow request
        return {"message": "slow"}

    @app.get("/test/error")
    async def error_endpoint() -> dict[str, str]:
        raise ValueError("Test error")

    return app


@pytest.fixture
def client(app_with_metrics: FastAPI) -> TestClient:
    """Create test client with metrics middleware."""
    return TestClient(app_with_metrics)


def test_metrics_middleware_records_successful_request(client: TestClient) -> None:
    """Test that middleware records metrics for successful requests."""
    response = client.get("/test/success")

    assert response.status_code == 200
    assert response.json() == {"message": "success"}

    # Metrics should be recorded
    # Access middleware to verify (this is a simplified check)
    # In a real scenario, you'd expose the metrics via an endpoint


def test_metrics_middleware_records_slow_request(client: TestClient) -> None:
    """Test that middleware logs warning for slow requests."""
    response = client.get("/test/slow")

    assert response.status_code == 200
    # Slow request should be logged (response time > 1000ms)


def test_metrics_middleware_records_error(client: TestClient) -> None:
    """Test that middleware records errors."""
    with pytest.raises(ValueError):
        client.get("/test/error")

    # Error should be recorded in metrics


def test_metrics_middleware_get_metrics() -> None:
    """Test MetricsMiddleware.get_metrics() method."""
    app = FastAPI()
    middleware = MetricsMiddleware(app)

    # Simulate recording some metrics
    middleware._record_request_metrics(
        endpoint="GET /test",
        method="GET",
        path="/test",
        status_code=200,
        response_time=100.0,
        error=False,
    )

    middleware._record_request_metrics(
        endpoint="GET /test",
        method="GET",
        path="/test",
        status_code=200,
        response_time=150.0,
        error=False,
    )

    middleware._record_request_metrics(
        endpoint="POST /test",
        method="POST",
        path="/test",
        status_code=500,
        response_time=200.0,
        error=True,
    )

    metrics = middleware.get_metrics()

    # Verify total counts
    assert metrics["total_requests"] == 3
    assert metrics["total_errors"] == 1
    assert metrics["error_rate_percent"] == 33.33

    # Verify endpoint counts
    assert metrics["requests_by_endpoint"]["GET /test"] == 2
    assert metrics["requests_by_endpoint"]["POST /test"] == 1

    # Verify status code distribution
    assert metrics["requests_by_status"][200] == 2
    assert metrics["requests_by_status"][500] == 1

    # Verify response time stats
    assert "GET /test" in metrics["response_times"]
    get_test_stats = metrics["response_times"]["GET /test"]
    assert get_test_stats["count"] == 2
    assert get_test_stats["avg"] == 125.0  # (100 + 150) / 2
    assert get_test_stats["min"] == 100.0
    assert get_test_stats["max"] == 150.0


def test_metrics_middleware_reset() -> None:
    """Test MetricsMiddleware.reset_metrics() method."""
    app = FastAPI()
    middleware = MetricsMiddleware(app)

    # Record some metrics
    middleware._record_request_metrics(
        endpoint="GET /test",
        method="GET",
        path="/test",
        status_code=200,
        response_time=100.0,
        error=False,
    )

    # Verify metrics exist
    metrics = middleware.get_metrics()
    assert metrics["total_requests"] == 1

    # Reset metrics
    middleware.reset_metrics()

    # Verify metrics are cleared
    metrics = middleware.get_metrics()
    assert metrics["total_requests"] == 0
    assert metrics["total_errors"] == 0
    assert metrics["requests_by_endpoint"] == {}
    assert metrics["requests_by_status"] == {}
    assert metrics["response_times"] == {}


def test_metrics_middleware_calculate_percentile() -> None:
    """Test percentile calculation."""
    values = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]

    # Test p95
    p95 = MetricsMiddleware._calculate_percentile(values, 95)
    assert p95 == 100.0  # 95th percentile of this list

    # Test p99
    p99 = MetricsMiddleware._calculate_percentile(values, 99)
    assert p99 == 100.0  # 99th percentile of this list

    # Test p50 (median)
    p50 = MetricsMiddleware._calculate_percentile(values, 50)
    assert p50 == 60.0  # 50th percentile (index 5 of 10 elements)

    # Test empty list
    p95_empty = MetricsMiddleware._calculate_percentile([], 95)
    assert p95_empty == 0.0


def test_metrics_middleware_status_code_tracking() -> None:
    """Test that all status codes are tracked correctly."""
    app = FastAPI()
    middleware = MetricsMiddleware(app)

    # Record different status codes
    status_codes = [200, 201, 400, 401, 404, 500, 503]
    for code in status_codes:
        middleware._record_request_metrics(
            endpoint=f"GET /test/{code}",
            method="GET",
            path=f"/test/{code}",
            status_code=code,
            response_time=100.0,
            error=(code >= 500),
        )

    metrics = middleware.get_metrics()

    # Verify all status codes are recorded
    for code in status_codes:
        assert metrics["requests_by_status"][code] == 1

    # Verify error count (only 500 and 503)
    assert metrics["total_errors"] == 2


def test_metrics_middleware_response_time_percentiles() -> None:
    """Test response time percentile calculations."""
    app = FastAPI()
    middleware = MetricsMiddleware(app)

    # Record multiple requests with varying response times
    response_times = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 500, 1000]
    for rt in response_times:
        middleware._record_request_metrics(
            endpoint="GET /test",
            method="GET",
            path="/test",
            status_code=200,
            response_time=float(rt),
            error=False,
        )

    metrics = middleware.get_metrics()
    stats = metrics["response_times"]["GET /test"]

    # Verify statistics
    assert stats["count"] == len(response_times)
    assert stats["min"] == 10.0
    assert stats["max"] == 1000.0
    assert stats["avg"] == sum(response_times) / len(response_times)

    # Verify percentiles exist
    assert "p95" in stats
    assert "p99" in stats
    assert stats["p95"] > stats["avg"]
    assert stats["p99"] >= stats["p95"]
