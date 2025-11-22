# Load Testing Guide

This directory contains load tests for the FFmpeg Backend API, designed to verify the system can handle concurrent job processing and maintain acceptable performance under load.

## Test Types

### 1. Locust Load Tests (`locustfile.py`)
HTTP-based load testing using Locust framework.

#### User Types:
- **CompositionUser**: Simulates typical user behavior (create, poll, download)
- **HealthCheckUser**: Simulates health monitoring
- **BurstLoadUser**: Simulates burst traffic patterns
- **SustainedLoadUser**: Simulates sustained load over time

#### Running Locust Tests:

```bash
# Basic load test with 5 concurrent users
locust -f tests/load/locustfile.py --users 5 --spawn-rate 1 --host http://localhost:8000

# Run for 30 minutes with 10 users
locust -f tests/load/locustfile.py --users 10 --spawn-rate 2 --run-time 30m --host http://localhost:8000

# Headless mode for CI/CD
locust -f tests/load/locustfile.py --headless --users 10 --spawn-rate 2 --run-time 10m --host http://localhost:8000 --html=report.html

# With web UI (default port 8089)
locust -f tests/load/locustfile.py --host http://localhost:8000
# Then open http://localhost:8089 in browser
```

#### Locust Metrics:
- **Requests per second (RPS)**: Target > 10 RPS
- **Response time**: P50 < 500ms, P95 < 2000ms
- **Failure rate**: < 1%

### 2. Pytest Load Tests (`test_concurrent_load.py`)
Programmatic load tests using pytest and pytest-benchmark.

#### Test Categories:
- **TestConcurrentSimpleCompositions**: 5 concurrent simple (2-clip) compositions
- **TestConcurrentComplexCompositions**: 5 concurrent complex (10-clip) compositions
- **TestMixedWorkload**: Mixed simple and complex compositions
- **TestSystemMetrics**: Memory usage and response time consistency

#### Running Pytest Load Tests:

```bash
# Run all load tests
pytest tests/load/test_concurrent_load.py -v

# Run specific test class
pytest tests/load/test_concurrent_load.py::TestConcurrentSimpleCompositions -v

# Run with benchmark plugin
pytest tests/load/test_concurrent_load.py --benchmark-only

# Run with coverage
pytest tests/load/test_concurrent_load.py --cov=src --cov-report=html

# Run load tests marked as benchmark
pytest tests/load/ -m benchmark -v
```

#### Pytest Metrics:
- **5 Simple Compositions**: Avg response time < 1s, Max < 2s
- **5 Complex Compositions**: Avg response time < 2s, Max < 4s
- **Mixed Workload**: Total time < 10s
- **Throughput**: > 10 compositions/second
- **Memory Usage**: Increase < 500MB for 20 compositions
- **Response Time P95**: < 2s

## Performance Baselines

### API Response Times
- **Create Composition (Simple)**: < 500ms (average), < 1000ms (P95)
- **Create Composition (Complex)**: < 1000ms (average), < 2000ms (P95)
- **Get Status**: < 100ms (average), < 200ms (P95)
- **Get Metadata**: < 200ms (average), < 400ms (P95)
- **Get Download URL**: < 300ms (average), < 600ms (P95)

### Concurrent Processing
- **5 Concurrent Simple**: All complete within 5 seconds
- **5 Concurrent Complex**: All complete within 10 seconds
- **Mixed Workload (3 simple + 2 complex)**: All complete within 10 seconds

### System Resources (per worker)
- **CPU Usage**: < 80% average under normal load
- **Memory Usage**: < 2GB per worker process
- **Redis Queue Depth**: < 100 jobs queued
- **Database Connections**: < 20 active connections
- **S3 Bandwidth**: Depends on video sizes, monitor for throttling

### Throughput
- **API Requests**: > 100 requests/second
- **Composition Creation**: > 10 compositions/second
- **Job Processing**: 5 simultaneous workers

## Load Test Scenarios

### Scenario 1: Normal Load
- **Users**: 5-10 concurrent users
- **Duration**: 30 minutes
- **Pattern**: Steady composition creation and status polling
- **Expected**: All requests successful, response times within SLA

```bash
locust -f tests/load/locustfile.py --users 10 --spawn-rate 2 --run-time 30m --host http://localhost:8000
```

### Scenario 2: Peak Load
- **Users**: 25-50 concurrent users
- **Duration**: 15 minutes
- **Pattern**: High composition creation rate
- **Expected**: Some queue buildup, but no failures

```bash
locust -f tests/load/locustfile.py --users 50 --spawn-rate 5 --run-time 15m --host http://localhost:8000
```

### Scenario 3: Burst Load
- **Users**: Start with 10, spike to 100, back to 10
- **Duration**: 10 minutes
- **Pattern**: Sudden traffic spike
- **Expected**: Graceful degradation, recovery after spike

```bash
# Use Locust web UI to manually adjust user count during test
locust -f tests/load/locustfile.py --host http://localhost:8000
```

### Scenario 4: Sustained Load
- **Users**: 20 concurrent users
- **Duration**: 2 hours
- **Pattern**: Steady load over extended period
- **Expected**: No memory leaks, stable performance

```bash
locust -f tests/load/locustfile.py --users 20 --spawn-rate 2 --run-time 2h --host http://localhost:8000
```

### Scenario 5: Stress Test
- **Users**: Incrementally increase until failure
- **Duration**: Until system degradation
- **Pattern**: Find breaking point
- **Expected**: Identify maximum capacity

```bash
# Manually increase users in web UI
locust -f tests/load/locustfile.py --host http://localhost:8000
```

## Monitoring During Load Tests

### Key Metrics to Monitor

#### Application Metrics
```bash
# Monitor API logs
docker-compose logs -f api

# Monitor worker logs
docker-compose logs -f worker

# Monitor metrics endpoint
watch -n 1 'curl -s http://localhost:8000/health/detailed | jq'
```

#### System Metrics

**CPU Usage**:
```bash
# Docker stats
docker stats

# System CPU
top -o cpu
```

**Memory Usage**:
```bash
# Docker memory
docker stats --format "table {{.Name}}\t{{.MemUsage}}"

# System memory
free -h  # Linux
vm_stat  # macOS
```

**Redis Queue Depth**:
```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Check queue length
LLEN rq:queue:default
LLEN rq:queue:high
LLEN rq:queue:low

# Monitor in real-time
MONITOR
```

**Database Connections**:
```bash
# Connect to PostgreSQL
docker-compose exec db psql -U postgres -d ffmpeg_backend

# Check active connections
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

# Check connection details
SELECT pid, usename, application_name, client_addr, state, query
FROM pg_stat_activity
WHERE datname = 'ffmpeg_backend';
```

**S3 Bandwidth**:
```bash
# Monitor S3 metrics in AWS CloudWatch
# Or use local MinIO metrics if using MinIO
```

### Prometheus & Grafana (Optional)

For production-grade monitoring:

```yaml
# docker-compose.override.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## Interpreting Results

### Success Criteria

✅ **All tests pass**:
- No HTTP errors (4xx, 5xx)
- Response times within SLA
- Memory usage stable
- No resource exhaustion

✅ **Performance targets met**:
- Throughput > 10 compositions/second
- P95 response time < 2 seconds
- 5 concurrent jobs complete successfully

✅ **System stability**:
- No memory leaks over 30 minutes
- CPU usage < 80%
- Database connections < 20
- Redis queue processes smoothly

### Warning Signs

⚠️ **Performance degradation**:
- Response times increasing over time
- Throughput declining
- Queue depth growing unbounded

⚠️ **Resource issues**:
- Memory usage growing linearly
- CPU at 100% sustained
- Database connection pool exhausted
- Redis memory near limit

⚠️ **Error rates**:
- > 1% failure rate
- Timeouts increasing
- Database deadlocks
- S3 throttling errors

### Failure Scenarios

❌ **System overload**:
- API returning 503 Service Unavailable
- Workers crashing
- Database connections rejected
- Out of memory errors

## Troubleshooting

### High Response Times
- Check worker count: `docker-compose ps worker`
- Check Redis queue: `docker-compose exec redis redis-cli LLEN rq:queue:default`
- Check database queries: `EXPLAIN ANALYZE <query>`
- Check S3 latency

### Memory Leaks
- Profile with memory_profiler
- Check for unclosed connections
- Review FFmpeg temp file cleanup
- Monitor garbage collection

### Queue Buildup
- Increase worker count
- Optimize job processing time
- Check for stuck jobs: `docker-compose exec redis redis-cli LLEN rq:queue:failed`
- Increase RQ timeout

### Database Slowness
- Add indexes: `CREATE INDEX ...`
- Optimize queries
- Increase connection pool size
- Enable query logging

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Load Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Start services
        run: docker-compose up -d

      - name: Wait for services
        run: ./scripts/wait-for-services.sh

      - name: Run Locust load test
        run: |
          pip install locust
          locust -f tests/load/locustfile.py \
            --headless \
            --users 10 \
            --spawn-rate 2 \
            --run-time 5m \
            --host http://localhost:8000 \
            --html=locust-report.html

      - name: Run pytest load tests
        run: pytest tests/load/ -v --benchmark-only

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: |
            locust-report.html
            .benchmarks/
```

## Best Practices

1. **Baseline first**: Establish baseline performance before making changes
2. **Isolate tests**: Run load tests on dedicated test environment
3. **Monitor everything**: CPU, memory, disk, network, application metrics
4. **Gradual ramp-up**: Start with low load and gradually increase
5. **Document results**: Keep records of test results over time
6. **Test regularly**: Run load tests before releases and after major changes
7. **Realistic data**: Use production-like data and scenarios
8. **Clean state**: Reset database and Redis between test runs
9. **Multiple iterations**: Run tests multiple times for consistency
10. **Analyze failures**: Investigate and fix root causes of failures

## Additional Resources

- [Locust Documentation](https://docs.locust.io/)
- [pytest-benchmark Documentation](https://pytest-benchmark.readthedocs.io/)
- [Load Testing Best Practices](https://grafana.com/blog/2024/01/30/load-testing-best-practices/)
- [Performance Testing Guide](https://www.nginx.com/blog/testing-the-performance-of-nginx-and-nginx-plus-web-servers/)
