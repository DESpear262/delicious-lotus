# Troubleshooting Guide

Complete guide for diagnosing and resolving common issues with the FFmpeg Backend Service.

## Table of Contents

- [Service Health Checks](#service-health-checks)
- [Common Issues](#common-issues)
- [Database Problems](#database-problems)
- [Redis Problems](#redis-problems)
- [Worker Problems](#worker-problems)
- [FFmpeg Problems](#ffmpeg-problems)
- [S3/Storage Problems](#s3storage-problems)
- [Performance Issues](#performance-issues)
- [Debugging Tools](#debugging-tools)

## Service Health Checks

### Quick Health Check

```bash
# Check all services
curl http://localhost:8000/api/v1/health

# Expected response
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "ffmpeg": "available"
  },
  "version": "0.1.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Detailed Health Check

```bash
# Detailed health endpoint
curl http://localhost:8000/api/v1/health/detailed

# Expected response includes
{
  "status": "healthy",
  "services": {
    "database": {
      "status": "healthy",
      "pool_size": 20,
      "active_connections": 5,
      "response_time_ms": 2
    },
    "redis": {
      "status": "healthy",
      "queue_depth": 3,
      "connected_clients": 4,
      "response_time_ms": 1
    },
    "ffmpeg": {
      "status": "available",
      "version": "7.0.2"
    }
  },
  "workers": {
    "active": 2,
    "busy": 1,
    "idle": 1
  }
}
```

### Component-Level Checks

```bash
# Check Docker services status
docker-compose ps

# Check container logs
docker-compose logs -f api       # API server logs
docker-compose logs -f worker    # Worker logs
docker-compose logs -f db        # Database logs
docker-compose logs -f redis     # Redis logs

# Check resource usage
docker stats

# Check network connectivity
docker-compose exec api ping db
docker-compose exec api ping redis
```

## Common Issues

### Issue: Service Won't Start

**Symptoms**:
- `docker-compose up` fails
- Containers exit immediately
- Error messages in logs

**Diagnosis**:
```bash
# Check service status
docker-compose ps

# View recent logs
docker-compose logs --tail=50

# Check for port conflicts
lsof -i :8000  # API port
lsof -i :5432  # PostgreSQL port
lsof -i :6379  # Redis port
```

**Solutions**:

1. **Port Already in Use**:
```bash
# Change ports in docker-compose.yml or stop conflicting service
# Kill process using port
kill -9 $(lsof -t -i:8000)

# Or use different port
export API_PORT=8001
docker-compose up
```

2. **Environment Variables Missing**:
```bash
# Copy and configure .env file
cp .env.example .env
# Edit .env with required values
nano .env
```

3. **Docker Resources Insufficient**:
```bash
# Check Docker resources
docker system df
docker system prune  # Clean up unused resources

# Increase Docker memory/CPU in Docker Desktop settings
```

### Issue: 500 Internal Server Error

**Symptoms**:
- API returns 500 errors
- Generic error messages
- No specific error details

**Diagnosis**:
```bash
# Check API logs
docker-compose logs api | grep ERROR

# Check for stack traces
docker-compose logs api --tail=100

# Test database connection
docker-compose exec api python -c "from db.session import engine; print(engine)"

# Test Redis connection
docker-compose exec api python -c "from redis import Redis; r = Redis.from_url('redis://redis:6379'); print(r.ping())"
```

**Solutions**:

1. **Database Connection Failed**:
```bash
# Verify DATABASE_URL
docker-compose exec api env | grep DATABASE_URL

# Test PostgreSQL connection
docker-compose exec db psql -U ffmpeg -d ffmpeg_backend -c "SELECT 1;"

# Restart database
docker-compose restart db
```

2. **Redis Connection Failed**:
```bash
# Verify REDIS_URL
docker-compose exec api env | grep REDIS_URL

# Test Redis connection
docker-compose exec redis redis-cli ping

# Restart Redis
docker-compose restart redis
```

### Issue: Jobs Stuck in Queue

**Symptoms**:
- Compositions remain in "queued" status
- No worker activity
- Jobs not processing

**Diagnosis**:
```bash
# Check worker status
docker-compose ps worker

# Check Redis queue depth
docker-compose exec redis redis-cli LLEN rq:queue:default

# Check for failed jobs
docker-compose exec redis redis-cli LLEN rq:queue:failed

# View worker logs
docker-compose logs worker --tail=50

# Check worker processes
docker-compose exec worker ps aux | grep rq
```

**Solutions**:

1. **Workers Not Running**:
```bash
# Start workers
docker-compose up -d worker

# Scale workers
docker-compose up -d --scale worker=4
```

2. **Workers Crashed**:
```bash
# View crash logs
docker-compose logs worker

# Restart workers
docker-compose restart worker

# Check for worker errors
docker-compose exec worker rq info
```

3. **Queue Backed Up**:
```bash
# Clear failed jobs (use with caution)
docker-compose exec redis redis-cli DEL rq:queue:failed

# Requeue failed jobs
docker-compose exec api python -c "
from rq import Queue
from redis import Redis
redis = Redis.from_url('redis://redis:6379')
failed = Queue('failed', connection=redis)
failed.requeue_all()
"
```

## Database Problems

### Issue: Database Connection Pool Exhausted

**Symptoms**:
- "connection pool limit reached" errors
- Slow API responses
- Timeouts

**Diagnosis**:
```bash
# Check active connections
docker-compose exec db psql -U ffmpeg -d ffmpeg_backend -c "
SELECT count(*) as connections, state
FROM pg_stat_activity
WHERE datname = 'ffmpeg_backend'
GROUP BY state;
"

# Check long-running queries
docker-compose exec db psql -U ffmpeg -d ffmpeg_backend -c "
SELECT pid, age(clock_timestamp(), query_start), usename, query
FROM pg_stat_activity
WHERE state != 'idle' AND query NOT ILIKE '%pg_stat_activity%'
ORDER BY query_start DESC;
"
```

**Solutions**:

1. **Increase Pool Size**:
```python
# In src/db/session.py
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=30,  # Increase from 20
    max_overflow=20,  # Increase from 10
)
```

2. **Kill Long-Running Queries**:
```bash
# Kill specific query
docker-compose exec db psql -U ffmpeg -d ffmpeg_backend -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE pid = <PID>;
"
```

### Issue: Slow Database Queries

**Diagnosis**:
```bash
# Enable query logging
docker-compose exec db psql -U ffmpeg -d ffmpeg_backend -c "
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s
SELECT pg_reload_conf();
"

# Check missing indexes
docker-compose exec db psql -U ffmpeg -d ffmpeg_backend -c "
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY correlation;
"
```

**Solutions**:

1. **Add Missing Indexes**:
```sql
-- Composition queries
CREATE INDEX IF NOT EXISTS idx_composition_status ON compositions(status);
CREATE INDEX IF NOT EXISTS idx_composition_created_at ON compositions(created_at DESC);

-- Job queries
CREATE INDEX IF NOT EXISTS idx_job_composition_id ON jobs(composition_id);
CREATE INDEX IF NOT EXISTS idx_job_status ON jobs(status);
```

2. **Vacuum and Analyze**:
```bash
docker-compose exec db psql -U ffmpeg -d ffmpeg_backend -c "
VACUUM ANALYZE compositions;
VACUUM ANALYZE jobs;
"
```

## Redis Problems

### Issue: Redis Memory Full

**Symptoms**:
- "OOM command not allowed" errors
- Jobs fail to enqueue
- Redis becomes unresponsive

**Diagnosis**:
```bash
# Check Redis memory usage
docker-compose exec redis redis-cli INFO memory

# Check key count
docker-compose exec redis redis-cli DBSIZE

# Find large keys
docker-compose exec redis redis-cli --bigkeys
```

**Solutions**:

1. **Clear Old Data**:
```bash
# Delete old job data (use with caution)
docker-compose exec redis redis-cli SCAN 0 MATCH "rq:job:*" COUNT 1000 | xargs redis-cli DEL

# Set TTL on keys
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

2. **Increase Memory Limit**:
```bash
# In docker-compose.yml
redis:
  command: redis-server --maxmemory 4gb --maxmemory-policy allkeys-lru
```

### Issue: Redis Connection Timeouts

**Diagnosis**:
```bash
# Check Redis latency
docker-compose exec redis redis-cli --latency

# Check slow log
docker-compose exec redis redis-cli SLOWLOG GET 10

# Monitor commands
docker-compose exec redis redis-cli MONITOR
```

**Solutions**:

1. **Adjust Timeout Settings**:
```python
# In Redis connection configuration
redis_client = Redis.from_url(
    REDIS_URL,
    socket_timeout=10,  # Increase timeout
    socket_connect_timeout=10,
    retry_on_timeout=True
)
```

## Worker Problems

### Issue: FFmpeg Process Hangs

**Symptoms**:
- Worker stuck on job for extended period
- No progress updates
- High CPU usage

**Diagnosis**:
```bash
# Check running FFmpeg processes
docker-compose exec worker ps aux | grep ffmpeg

# Check FFmpeg progress
docker-compose exec worker tail -f /tmp/ffmpeg_progress.log

# Check system resources
docker stats worker
```

**Solutions**:

1. **Set FFmpeg Timeout**:
```python
# In FFmpeg command execution
subprocess.run(
    ffmpeg_command,
    timeout=3600,  # 1 hour max
    check=True
)
```

2. **Kill Stuck Process**:
```bash
# Kill FFmpeg process
docker-compose exec worker pkill -9 ffmpeg

# Restart worker
docker-compose restart worker
```

### Issue: Temporary Files Not Cleaned Up

**Symptoms**:
- Disk space filling up
- `/tmp` directory growing
- Worker running out of disk space

**Diagnosis**:
```bash
# Check disk usage
docker-compose exec worker df -h

# Check /tmp directory size
docker-compose exec worker du -sh /tmp/*

# List old temporary files
docker-compose exec worker find /tmp -type f -mtime +1 -ls
```

**Solutions**:

1. **Manual Cleanup**:
```bash
# Remove old files
docker-compose exec worker find /tmp -type f -mtime +1 -delete

# Clean up specific job
docker-compose exec worker rm -rf /tmp/job_<JOB_ID>
```

2. **Automated Cleanup** (add to worker code):
```python
import atexit
import shutil
import tempfile

# Register cleanup on exit
def cleanup_temp_files(temp_dir):
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

temp_dir = tempfile.mkdtemp(prefix="job_")
atexit.register(cleanup_temp_files, temp_dir)
```

## FFmpeg Problems

### Issue: FFmpeg Command Fails

**Diagnosis**:
```bash
# Check FFmpeg installation
docker-compose exec worker ffmpeg -version

# Test FFmpeg with sample file
docker-compose exec worker ffmpeg -i /path/to/test.mp4 -f null -

# Check FFmpeg logs
docker-compose logs worker | grep ffmpeg
```

**Common FFmpeg Error Solutions**:

1. **Invalid Input File**:
```bash
# Verify file exists and is readable
ffprobe /path/to/input.mp4

# Check file format
file /path/to/input.mp4
```

2. **Codec Not Supported**:
```bash
# List available codecs
ffmpeg -codecs | grep <codec_name>

# Install additional codecs (if needed)
apt-get update && apt-get install -y ffmpeg-extra
```

3. **Out of Memory**:
```bash
# Reduce memory usage with streaming
ffmpeg -i input.mp4 -c:v libx264 -preset ultrafast -threads 2 output.mp4
```

## S3/Storage Problems

### Issue: S3 Upload/Download Failures

**Diagnosis**:
```bash
# Test S3 credentials
docker-compose exec worker python -c "
import boto3
s3 = boto3.client('s3')
print(s3.list_buckets())
"

# Check S3 configuration
docker-compose exec worker env | grep AWS
docker-compose exec worker env | grep S3
```

**Solutions**:

1. **Invalid Credentials**:
```bash
# Verify AWS credentials
aws configure list

# Set credentials in environment
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

2. **Network Issues**:
```bash
# Test S3 connectivity
curl -I https://s3.amazonaws.com

# Check bucket access
aws s3 ls s3://your-bucket-name/
```

3. **Presigned URL Expired**:
```python
# Increase URL expiration time
url = s3_client.generate_presigned_url(
    'get_object',
    Params={'Bucket': bucket, 'Key': key},
    ExpiresIn=7200  # 2 hours instead of 1
)
```

## Performance Issues

### Issue: Slow API Response Times

**Diagnosis**:
```bash
# Measure endpoint latency
time curl http://localhost:8000/api/v1/health

# Use API benchmarking tool
ab -n 1000 -c 10 http://localhost:8000/api/v1/health

# Check database query performance
docker-compose exec db psql -U ffmpeg -d ffmpeg_backend -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
"
```

**Solutions**:

1. **Enable Database Query Caching**:
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_composition_cached(composition_id: str):
    return db.query(Composition).filter_by(id=composition_id).first()
```

2. **Add Database Indexes**:
```sql
CREATE INDEX CONCURRENTLY idx_composition_lookup
ON compositions(id, status, created_at);
```

3. **Optimize Database Queries**:
```python
# Use eager loading to avoid N+1 queries
compositions = db.query(Composition)\
    .options(joinedload(Composition.jobs))\
    .all()
```

## Debugging Tools

### Logging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
docker-compose up

# Follow specific service logs
docker-compose logs -f api
docker-compose logs -f worker

# Search logs for errors
docker-compose logs api | grep -i error
docker-compose logs api | grep -C 5 "composition_id"
```

### Interactive Debugging

```bash
# Open Python shell in API container
docker-compose exec api python

# Test database queries
docker-compose exec api python -c "
from db.session import SessionLocal
from db.models.composition import Composition
db = SessionLocal()
print(db.query(Composition).count())
"

# Test Redis operations
docker-compose exec api python -c "
from redis import Redis
r = Redis.from_url('redis://redis:6379')
print(r.keys('*'))
"
```

### Monitoring Commands

```bash
# Monitor Redis queue in real-time
watch -n 1 'docker-compose exec redis redis-cli LLEN rq:queue:default'

# Monitor database connections
watch -n 5 'docker-compose exec db psql -U ffmpeg -d ffmpeg_backend -c "
SELECT count(*) FROM pg_stat_activity WHERE datname = 'ffmpeg_backend'"'

# Monitor worker resource usage
docker stats --no-stream worker
```

### API Request Tracing

```bash
# Enable request tracing
curl -H "X-Debug: true" http://localhost:8000/api/v1/compositions/{id}

# Check request ID in logs
docker-compose logs api | grep "request_id=<REQUEST_ID>"

# Trace complete request flow
docker-compose logs api worker | grep "composition_id=<COMPOSITION_ID>" | sort
```

## Getting Help

If you're still experiencing issues:

1. **Check Logs**: Collect relevant logs from all services
2. **Check Documentation**: Review API docs and examples
3. **Search Issues**: Search GitHub issues for similar problems
4. **Create Issue**: Open a new issue with:
   - Detailed description
   - Steps to reproduce
   - Environment information
   - Relevant logs
   - Expected vs actual behavior
