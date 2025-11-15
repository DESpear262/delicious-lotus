# Load Testing Guide

This directory contains load testing scripts and test data for the AI Video Generation Pipeline. Load testing validates performance under concurrent load and identifies system bottlenecks.

## Quick Start

### Prerequisites

```bash
# Install Locust
pip install locust

# Verify installation
locust --version
```

### Basic Usage

```bash
# 1. Navigate to load test directory
cd tests/load

# 2. Run with web UI (recommended for first-time use)
locust -f locustfile.py --host=http://your-ecs-service:8000

# 3. Open browser to http://localhost:8089
# 4. Set number of users and spawn rate
# 5. Start test and monitor results
```

## Test Scenarios

### Scenario 1: Health Check
**Endpoint:** `GET /health`
**Target:** 100 requests/second
**Expected:** <50ms response time, 0% errors

```bash
locust -f locustfile.py --host=http://your-api:8000 \
       --tags health --users=10 --spawn-rate=5 --run-time=2m
```

### Scenario 2: Video Generation Submission
**Endpoint:** `POST /api/v1/generations`
**Load Profile:** 5-20 concurrent users
**Success Criteria:** 100% success at 5 users, <500ms response time

```bash
locust -f locustfile.py --host=http://your-api:8000 \
       --tags generation --users=5 --spawn-rate=1 --run-time=5m
```

### Scenario 3: Status Polling
**Endpoint:** `GET /api/v1/generations/{id}`
**Load Profile:** 10 users polling every 5 seconds
**Success Criteria:** <200ms response time

```bash
locust -f locustfile.py --host=http://your-api:8000 \
       --tags polling --users=10 --spawn-rate=2 --run-time=5m
```

### Scenario 4: Asset Upload
**Endpoint:** `POST /api/v1/assets/upload`
**Load Profile:** 3 concurrent uploads, 5MB files
**Success Criteria:** <10s upload time

```bash
locust -f locustfile.py --host=http://your-api:8000 \
       --tags upload --users=3 --spawn-rate=1 --run-time=3m
```

### Scenario 5: End-to-End Workflow
**Flow:** Submit → Poll → Download
**Load Profile:** 2-3 concurrent workflows
**Success Criteria:** 90% success rate

```bash
locust -f locustfile.py --host=http://your-api:8000 \
       --tags e2e --users=3 --spawn-rate=1 --run-time=10m
```

## Load Profiles

### Baseline Test (MVP Validation)
**Purpose:** Validate 5 concurrent user requirement
**Duration:** 10 minutes
**Command:**
```bash
locust -f locustfile.py --host=http://your-api:8000 \
       --shape=BaselineLoadShape --headless \
       --csv=results/baseline
```

### Stress Test
**Purpose:** Identify bottlenecks at 2x load
**Users:** 10 concurrent
**Duration:** 5 minutes
**Command:**
```bash
locust -f locustfile.py --host=http://your-api:8000 \
       --shape=StressTestShape --headless \
       --csv=results/stress
```

### Spike Test
**Purpose:** Test autoscaling and recovery
**Pattern:** 0→20 users in 1 minute, hold 2 minutes
**Command:**
```bash
locust -f locustfile.py --host=http://your-api:8000 \
       --shape=SpikeTestShape --headless \
       --csv=results/spike
```

### Endurance Test
**Purpose:** Detect memory leaks and stability issues
**Users:** 5 concurrent
**Duration:** 30 minutes
**Command:**
```bash
locust -f locustfile.py --host=http://your-api:8000 \
       --shape=EnduranceTestShape --headless \
       --csv=results/endurance
```

## Test Data

### Prompts (`test-data/prompts.json`)
Contains 30 sample video generation prompts covering various:
- Product showcases
- Brand videos
- Advertisements
- Explainer videos
- Corporate content

Prompts vary in:
- Length (15s, 30s, 45s, 60s)
- Complexity
- Category/industry
- Style requirements

### Sample Assets (`test-data/sample-logo.png`)
5MB placeholder image for testing asset upload performance.

## Monitoring During Tests

### CloudWatch Metrics to Watch
```bash
# CPU Utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=video-gen-service \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T01:00:00Z \
  --period 60 \
  --statistics Average
```

Monitor:
- **ECS Task CPU:** Should stay <70%
- **ECS Task Memory:** Should stay <80%
- **RDS Connections:** Watch for connection pool exhaustion
- **ALB Response Time:** Track API latency
- **ALB 5xx Errors:** Should be 0%

### Application Logs
```bash
# Tail application logs during test
aws logs tail /ecs/video-generation-api --follow

# Watch for:
# - Database connection errors
# - Timeout errors
# - Memory warnings
# - Slow query logs
```

## Interpreting Results

### Key Metrics

1. **Response Time Percentiles**
   - **p50 (median):** Typical user experience
   - **p95:** 95% of requests faster than this
   - **p99:** Slowest 1% of requests
   - **Target:** p95 <500ms for generation submission, p95 <200ms for status polling

2. **Throughput**
   - Requests per second (RPS)
   - **Target:** Sustain 5 concurrent users without errors

3. **Error Rate**
   - Percentage of failed requests
   - **Target:** <1% error rate at baseline load, 0% at MVP load

4. **Resource Utilization**
   - CPU and memory usage
   - Database connections
   - **Target:** <70% CPU, <80% memory at peak load

### Success Criteria

✅ **PASS:** All metrics within targets
⚠️ **WARNING:** Metrics approaching limits (>90% of target)
❌ **FAIL:** Errors >1% or response times >2x target

### Sample Results Analysis

```
Baseline Test Results (5 users, 10 minutes):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Metric                      | Value    | Target   | Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Requests              | 12,450   | -        | -
Requests/Second             | 20.75    | >10      | ✅ PASS
Error Rate                  | 0.2%     | <1%      | ✅ PASS

Response Times (Generation):
  p50                       | 245ms    | <500ms   | ✅ PASS
  p95                       | 478ms    | <500ms   | ✅ PASS
  p99                       | 892ms    | <1000ms  | ✅ PASS

Response Times (Polling):
  p50                       | 87ms     | <200ms   | ✅ PASS
  p95                       | 156ms    | <200ms   | ✅ PASS
  p99                       | 234ms    | <300ms   | ✅ PASS

Resource Utilization:
  CPU (avg)                 | 45%      | <70%     | ✅ PASS
  Memory (avg)              | 62%      | <80%     | ✅ PASS
  DB Connections (peak)     | 8        | <20      | ✅ PASS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VERDICT: ✅ System meets MVP performance requirements
```

## Troubleshooting

### Common Issues

#### 1. Connection Refused
```
Error: Connection refused to http://localhost:8000
```

**Solution:** Verify service is running and accessible
```bash
# Check service status
curl http://your-api:8000/health

# Verify ECS task is running
aws ecs list-tasks --cluster video-gen-cluster
```

#### 2. High Error Rate
```
Error rate >5% during baseline test
```

**Solution:** Check application logs for errors
```bash
# Common causes:
# - Database connection pool exhausted
# - Memory limits exceeded
# - AI API rate limiting
# - Network timeouts
```

#### 3. Slow Response Times
```
p95 response time >1s for generation submission
```

**Solution:** Identify bottleneck
```bash
# Check CloudWatch metrics:
# - CPU usage >80%: Increase task CPU
# - Memory usage >90%: Increase task memory
# - DB connections maxed: Increase connection pool
# - High DB query time: Optimize queries or add indexes
```

#### 4. Out of Memory
```
Task killed due to memory limit
```

**Solution:** Increase ECS task memory allocation
```bash
# Update task definition in Terraform:
# memory = 4096  # Increase from 2048 to 4096
```

### Performance Tuning Checklist

- [ ] Database connection pool configured (min: 5, max: 20)
- [ ] ECS task resources adequate (CPU: 1024, Memory: 2048+)
- [ ] Request timeouts configured (30s standard, 600s for long operations)
- [ ] Redis caching enabled for frequently accessed data
- [ ] Database indexes on frequently queried fields
- [ ] CDN configured for static assets
- [ ] Compression enabled for API responses
- [ ] Rate limiting configured to protect against abuse

## Best Practices

### Running Load Tests

1. **Start Small:** Begin with low user counts and gradually increase
2. **Monitor Costs:** Load tests generate API calls that may incur costs (Replicate, AWS)
3. **Test in Isolation:** Run tests during off-peak hours or against staging environment
4. **Baseline First:** Always run baseline test before stress/spike tests
5. **Document Results:** Save CSV results and CloudWatch screenshots

### Test Environment

- Run load tests from EC2 instance in same AWS region (realistic network conditions)
- Use separate test environment/database when possible
- Ensure test data doesn't pollute production metrics
- Clean up generated test data after tests complete

### Continuous Performance Testing

```bash
# Add to CI/CD pipeline (light load test)
locust -f locustfile.py --host=$API_URL \
       --users=3 --spawn-rate=1 --run-time=2m \
       --headless --csv=results/ci \
       --stop-timeout=10

# Parse results and fail if performance degrades
python3 scripts/check_performance.py results/ci_stats.csv
```

## Results Directory

Create a `results/` directory to store test outputs:

```bash
mkdir -p results

# Test outputs will include:
# - results/baseline_stats.csv        - Request statistics
# - results/baseline_exceptions.csv   - Error details
# - results/baseline_failures.csv     - Failed requests
# - results/baseline_stats_history.csv - Time-series data
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Performance Test

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Install Locust
        run: pip install locust

      - name: Run Light Load Test
        run: |
          cd tests/load
          locust -f locustfile.py \
                 --host=${{ secrets.API_URL }} \
                 --users=3 --spawn-rate=1 --run-time=3m \
                 --headless --csv=results/ci

      - name: Check Performance Thresholds
        run: |
          python3 scripts/validate_performance.py results/ci_stats.csv

      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: load-test-results
          path: tests/load/results/
```

## Additional Resources

- [Locust Documentation](https://docs.locust.io/)
- [AWS CloudWatch Metrics](https://docs.aws.amazon.com/cloudwatch/)
- [Performance Testing Best Practices](https://www.thoughtworks.com/insights/blog/performance-testing)
- [../docs/performance.md](../../docs/performance.md) - Performance benchmarks and results

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section above
2. Review application logs in CloudWatch
3. Consult [docs/performance.md](../../docs/performance.md) for optimization recommendations
4. Open an issue in the project repository
