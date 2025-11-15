# Performance Tuning Guide

Comprehensive guide for optimizing the FFmpeg Backend Service for production workloads.

## Table of Contents

- [Database Optimization](#database-optimization)
- [Redis Optimization](#redis-optimization)
- [Worker Optimization](#worker-optimization)
- [FFmpeg Optimization](#ffmpeg-optimization)
- [API Server Optimization](#api-server-optimization)
- [Infrastructure Sizing](#infrastructure-sizing)
- [Monitoring and Profiling](#monitoring-and-profiling)

## Database Optimization

### Connection Pooling

Optimal connection pool configuration for high-throughput scenarios:

```python
# src/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=30,  # Number of permanent connections
    max_overflow=20,  # Additional connections under load
    pool_timeout=30,  # Timeout for getting connection from pool
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connections before use
)
```

**Recommendations**:
- `pool_size`: 20-30 for production (2-3x number of API workers)
- `max_overflow`: 10-20 (50% of pool_size)
- `pool_recycle`: 3600 (1 hour) to prevent stale connections
- `pool_pre_ping`: True for reliability

### Index Optimization

Essential indexes for high-performance queries:

```sql
-- Composition lookups
CREATE INDEX CONCURRENTLY idx_composition_status ON compositions(status);
CREATE INDEX CONCURRENTLY idx_composition_created_at ON compositions(created_at DESC);
CREATE INDEX CONCURRENTLY idx_composition_user_id ON compositions(user_id) WHERE user_id IS NOT NULL;

-- Job queries
CREATE INDEX CONCURRENTLY idx_job_composition_id ON jobs(composition_id);
CREATE INDEX CONCURRENTLY idx_job_status ON jobs(status);
CREATE INDEX CONCURRENTLY idx_job_created_at ON jobs(created_at DESC);

-- Composite indexes for common queries
CREATE INDEX CONCURRENTLY idx_composition_lookup
ON compositions(status, created_at DESC)
WHERE status IN ('pending', 'queued', 'processing');
```

### Query Optimization

**Use Eager Loading**:
```python
# Bad: N+1 query problem
compositions = db.query(Composition).all()
for comp in compositions:
    print(comp.jobs)  # Each iteration queries database

# Good: Eager loading
from sqlalchemy.orm import joinedload

compositions = db.query(Composition)\
    .options(joinedload(Composition.jobs))\
    .all()
```

**Use Pagination**:
```python
# Bad: Loading all compositions
compositions = db.query(Composition).all()

# Good: Paginated query
compositions = db.query(Composition)\
    .order_by(Composition.created_at.desc())\
    .limit(50)\
    .offset((page - 1) * 50)\
    .all()
```

**Use Selective Loading**:
```python
# Bad: Loading all columns
compositions = db.query(Composition).all()

# Good: Only load needed columns
compositions = db.query(
    Composition.id,
    Composition.title,
    Composition.status
).all()
```

### Database Configuration

PostgreSQL configuration for production (`postgresql.conf`):

```ini
# Connection Settings
max_connections = 200
shared_buffers = 4GB  # 25% of system RAM
effective_cache_size = 12GB  # 75% of system RAM
maintenance_work_mem = 1GB
work_mem = 64MB

# WAL Settings
wal_buffers = 16MB
min_wal_size = 1GB
max_wal_size = 4GB
checkpoint_completion_target = 0.9

# Query Planning
random_page_cost = 1.1  # For SSD storage
effective_io_concurrency = 200  # For SSD storage
default_statistics_target = 100

# Parallel Query
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8

# Logging
log_min_duration_statement = 1000  # Log queries > 1s
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
```

## Redis Optimization

### Memory Configuration

```bash
# redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru  # Evict least recently used keys

# Persistence
save 900 1      # Save if 1 key changed in 15 minutes
save 300 10     # Save if 10 keys changed in 5 minutes
save 60 10000   # Save if 10000 keys changed in 1 minute

# AOF Persistence (more durable)
appendonly yes
appendfsync everysec
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
```

### Connection Pooling

```python
# src/workers/redis_client.py
from redis import ConnectionPool, Redis

# Create connection pool
redis_pool = ConnectionPool.from_url(
    REDIS_URL,
    max_connections=50,  # Maximum connections
    socket_timeout=5,
    socket_connect_timeout=5,
    socket_keepalive=True,
    socket_keepalive_options={
        1: 1,  # TCP_KEEPIDLE
        2: 3,  # TCP_KEEPINTVL
        3: 5,  # TCP_KEEPCNT
    },
    retry_on_timeout=True,
)

# Use pool for connections
redis_client = Redis(connection_pool=redis_pool)
```

### Queue Optimization

**Job TTL and Cleanup**:
```python
from rq import Queue
from redis import Redis

redis_conn = Redis.from_url(REDIS_URL)

# Set job result TTL
queue = Queue(
    'default',
    connection=redis_conn,
    default_timeout=3600,  # Job timeout: 1 hour
    result_ttl=600,  # Keep results for 10 minutes
    failure_ttl=86400,  # Keep failures for 24 hours
)
```

**Queue Priorities**:
```python
# Create priority queues
high_queue = Queue('high', connection=redis_conn)
default_queue = Queue('default', connection=redis_conn)
low_queue = Queue('low', connection=redis_conn)

# Workers listen to queues in priority order
# rq worker high default low
```

## Worker Optimization

### Worker Configuration

**Optimal Worker Count**:
```bash
# Formula: (CPU cores / 2) = concurrent workers
# For 8-core machine:
docker-compose up -d --scale worker=4

# Or configure in docker-compose.yml
worker:
  deploy:
    replicas: 4
```

**Worker Resource Limits**:
```yaml
# docker-compose.yml
worker:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
      reservations:
        cpus: '1.0'
        memory: 2G
```

### Concurrency Settings

```python
# Environment variables
WORKER_CONCURRENCY=2  # Jobs per worker
WORKER_TIMEOUT=3600  # 1 hour max per job
WORKER_MAX_JOBS=100  # Process 100 jobs before restart
```

### Job Processing Optimization

**Parallel Processing**:
```python
import multiprocessing

def process_clips_parallel(clips: List[str]) -> List[str]:
    """Process multiple clips in parallel."""
    with multiprocessing.Pool(processes=4) as pool:
        results = pool.map(process_single_clip, clips)
    return results
```

**Streaming for Large Files**:
```python
import asyncio

async def download_large_file(url: str, destination: str):
    """Stream download for large files."""
    async with httpx.AsyncClient() as client:
        async with client.stream('GET', url) as response:
            with open(destination, 'wb') as f:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    f.write(chunk)
```

### Memory Management

**Temporary File Cleanup**:
```python
import tempfile
import shutil
import atexit

class TemporaryWorkspace:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="ffmpeg_job_")
        atexit.register(self.cleanup)

    def cleanup(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def __enter__(self):
        return self.temp_dir

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

# Usage
with TemporaryWorkspace() as workspace:
    # Process files in workspace
    process_video(workspace)
    # Automatic cleanup on exit
```

## FFmpeg Optimization

### Encoding Presets

**Fast Encoding (Lower Quality)**:
```python
ffmpeg_cmd = [
    'ffmpeg',
    '-i', input_file,
    '-c:v', 'libx264',
    '-preset', 'ultrafast',  # Fastest encoding
    '-crf', '28',  # Lower quality
    '-c:a', 'aac',
    '-b:a', '128k',
    output_file
]
```

**Balanced Encoding (Recommended)**:
```python
ffmpeg_cmd = [
    'ffmpeg',
    '-i', input_file,
    '-c:v', 'libx264',
    '-preset', 'medium',  # Balanced speed/quality
    '-crf', '23',  # Good quality
    '-c:a', 'aac',
    '-b:a', '192k',
    '-movflags', '+faststart',  # Enable progressive download
    output_file
]
```

**High Quality Encoding**:
```python
ffmpeg_cmd = [
    'ffmpeg',
    '-i', input_file,
    '-c:v', 'libx264',
    '-preset', 'slow',  # Better compression
    '-crf', '18',  # High quality
    '-c:a', 'aac',
    '-b:a', '256k',
    '-movflags', '+faststart',
    output_file
]
```

### Hardware Acceleration

**NVIDIA GPU (NVENC)**:
```python
ffmpeg_cmd = [
    'ffmpeg',
    '-hwaccel', 'cuda',
    '-i', input_file,
    '-c:v', 'h264_nvenc',  # NVIDIA hardware encoder
    '-preset', 'p4',  # NVENC preset (p1-p7)
    '-rc', 'vbr',
    '-cq', '23',
    '-b:v', '5M',
    '-c:a', 'aac',
    output_file
]
```

**Intel Quick Sync (QSV)**:
```python
ffmpeg_cmd = [
    'ffmpeg',
    '-hwaccel', 'qsv',
    '-i', input_file,
    '-c:v', 'h264_qsv',
    '-preset', 'medium',
    '-global_quality', '23',
    '-c:a', 'aac',
    output_file
]
```

### Multi-Threading

```python
import os

# Use all available CPU cores
cpu_count = os.cpu_count() or 4

ffmpeg_cmd = [
    'ffmpeg',
    '-threads', str(cpu_count),  # Encoding threads
    '-i', input_file,
    '-c:v', 'libx264',
    '-preset', 'medium',
    '-crf', '23',
    '-filter_complex_threads', str(cpu_count),  # Filter threads
    output_file
]
```

### Two-Pass Encoding

For better quality at target bitrate:

```python
# First pass
ffmpeg_cmd_pass1 = [
    'ffmpeg',
    '-y',
    '-i', input_file,
    '-c:v', 'libx264',
    '-b:v', '2M',
    '-pass', '1',
    '-f', 'null',
    '/dev/null'
]

# Second pass
ffmpeg_cmd_pass2 = [
    'ffmpeg',
    '-i', input_file,
    '-c:v', 'libx264',
    '-b:v', '2M',
    '-pass', '2',
    '-c:a', 'aac',
    output_file
]
```

## API Server Optimization

### Async Operations

**Use Async Database Queries**:
```python
from sqlalchemy.ext.asyncio import AsyncSession

async def get_composition(db: AsyncSession, composition_id: str):
    result = await db.execute(
        select(Composition).filter_by(id=composition_id)
    )
    return result.scalar_one_or_none()
```

**Parallel API Calls**:
```python
import asyncio
import httpx

async def fetch_multiple_urls(urls: List[str]) -> List[dict]:
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]
```

### Caching

**Response Caching**:
```python
from functools import lru_cache
from fastapi import Response

@lru_cache(maxsize=128)
def get_cached_compositions(status: str, limit: int = 50):
    return db.query(Composition)\
        .filter_by(status=status)\
        .limit(limit)\
        .all()

@app.get("/api/v1/compositions")
async def list_compositions(
    status: str = "completed",
    response: Response = None
):
    # Set cache headers
    response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutes
    return get_cached_compositions(status)
```

**Redis Caching**:
```python
import json
from redis import Redis

redis_client = Redis.from_url(REDIS_URL)

async def get_composition_cached(composition_id: str):
    # Try cache first
    cached = redis_client.get(f"composition:{composition_id}")
    if cached:
        return json.loads(cached)

    # Fetch from database
    composition = await db.get(Composition, composition_id)

    # Store in cache (5 minute TTL)
    redis_client.setex(
        f"composition:{composition_id}",
        300,
        json.dumps(composition.dict())
    )

    return composition
```

### Uvicorn Configuration

```bash
# Production Uvicorn settings
uvicorn src.app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \  # Number of worker processes (2-4x CPU cores)
  --loop uvloop \  # Use uvloop for better performance
  --http h11 \  # HTTP protocol implementation
  --log-level info \
  --access-log \
  --proxy-headers \  # Trust proxy headers
  --forwarded-allow-ips='*'
```

## Infrastructure Sizing

### Small Deployment (< 100 compositions/day)

```yaml
API Servers: 1-2 instances
- CPU: 2 cores
- Memory: 2 GB
- Disk: 20 GB

Workers: 2 instances
- CPU: 4 cores
- Memory: 4 GB
- Disk: 50 GB

Database (PostgreSQL):
- CPU: 2 cores
- Memory: 4 GB
- Disk: 100 GB SSD

Redis:
- CPU: 1 core
- Memory: 2 GB
- Disk: 10 GB
```

### Medium Deployment (100-1000 compositions/day)

```yaml
API Servers: 2-4 instances
- CPU: 4 cores
- Memory: 4 GB
- Disk: 20 GB

Workers: 4-8 instances
- CPU: 8 cores
- Memory: 8 GB
- Disk: 100 GB SSD

Database (PostgreSQL):
- CPU: 4-8 cores
- Memory: 16 GB
- Disk: 500 GB SSD
- IOPS: 3000+

Redis:
- CPU: 2 cores
- Memory: 4 GB
- Disk: 20 GB
```

### Large Deployment (> 1000 compositions/day)

```yaml
API Servers: 4-8+ instances (auto-scaling)
- CPU: 8 cores
- Memory: 8 GB
- Disk: 20 GB

Workers: 8-16+ instances (auto-scaling)
- CPU: 16 cores (or GPU-enabled)
- Memory: 16 GB
- Disk: 200 GB SSD

Database (PostgreSQL):
- CPU: 8-16 cores
- Memory: 32-64 GB
- Disk: 1-2 TB SSD
- IOPS: 10000+
- Read Replicas: 2+

Redis:
- CPU: 4 cores
- Memory: 8-16 GB
- Disk: 50 GB
- Cluster: Yes (for HA)
```

## Monitoring and Profiling

### Performance Metrics

**Key Metrics to Monitor**:
1. API Response Time (P50, P95, P99)
2. Worker Job Processing Time
3. Database Query Time
4. Redis Queue Depth
5. FFmpeg Processing Time
6. S3 Upload/Download Speed
7. CPU/Memory Usage
8. Disk I/O

**Prometheus Metrics**:
```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

# Job metrics
job_processing_time = Histogram('job_processing_seconds', 'Job processing time')
active_jobs = Gauge('active_jobs', 'Number of active jobs')
queue_depth = Gauge('queue_depth', 'Redis queue depth', ['queue_name'])
```

### Profiling Tools

**Python Profiling**:
```bash
# Install profiling tools
pip install py-spy memory_profiler

# Profile running worker
py-spy record -o profile.svg --pid <WORKER_PID>

# Memory profiling
python -m memory_profiler worker.py
```

**Database Profiling**:
```sql
-- Enable pg_stat_statements
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- View slow queries
SELECT query, calls, total_time, mean_time, max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 20;
```

**Load Testing**:
```bash
# Install load testing tool
pip install locust

# Run load test
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

### Optimization Checklist

- [ ] Database indexes created for all common queries
- [ ] Connection pooling configured appropriately
- [ ] Redis memory limits and eviction policy set
- [ ] Worker count matches CPU core count
- [ ] FFmpeg preset optimized for use case
- [ ] Temporary file cleanup automated
- [ ] Response caching implemented
- [ ] Monitoring and alerting configured
- [ ] Load testing performed
- [ ] Resource limits set in production
