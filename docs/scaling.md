# Scaling Guide
## AI Video Generation Pipeline - Post-MVP Growth Strategy

This guide outlines scaling strategies, capacity planning, and growth recommendations for the AI Video Generation Pipeline as usage increases beyond MVP levels.

**Last Updated:** 2025-11-15
**Version:** 1.0.0 (MVP)
**Current Capacity:** ~5-10 concurrent users, 100 videos/month
**Target Capacity:** 50+ concurrent users, 1000+ videos/month

---

## Table of Contents

1. [Current MVP Capacity](#current-mvp-capacity)
2. [Horizontal Scaling](#horizontal-scaling)
3. [Vertical Scaling](#vertical-scaling)
4. [Database Optimization](#database-optimization)
5. [Caching Strategies](#caching-strategies)
6. [Traffic Projections](#traffic-projections)
7. [When to Scale](#when-to-scale)
8. [Scaling Roadmap](#scaling-roadmap)

---

## Current MVP Capacity

### Infrastructure Configuration

| Component | Configuration | Capacity |
|-----------|--------------|----------|
| **ECS Tasks** | 1 task, 1 vCPU, 2GB RAM | 5-10 concurrent users |
| **RDS** | db.t4g.micro, 20GB, 80 connections | ~50 concurrent connections |
| **ElastiCache** | cache.t4g.micro, single node | ~50 concurrent connections |
| **S3** | Standard storage, no limits | Unlimited (within reason) |
| **Replicate API** | Rate limited by account tier | Variable by plan |

### Performance Baselines

**Request Latency:**
- Health check: <50ms
- Simple API calls: 100-300ms
- Video generation (total): 2-5 minutes
- WebSocket updates: <100ms

**Throughput:**
- API requests: ~100 req/min
- Concurrent video generations: 5 (configurable)
- Database queries: ~500 QPS
- Cache operations: ~1000 OPS

### Bottlenecks

1. **Primary:** Replicate API rate limits and costs
2. **Secondary:** FFmpeg processing (CPU-intensive, single task)
3. **Tertiary:** Database connections (limited to 80 on db.t4g.micro)
4. **Fourth:** Single ECS task (no redundancy)

---

## Horizontal Scaling

Horizontal scaling adds more instances of existing resources.

### ECS Service Scaling

#### Current State
```yaml
Desired count: 1
Min count: 1
Max count: 1
```

#### Scaled Configuration
```yaml
Desired count: 3
Min count: 2  # Redundancy
Max count: 10 # Peak traffic
```

#### Implementation

**1. Update Terraform configuration:**

```hcl
# terraform/terraform.tfvars
desired_count = 3
min_count = 2
max_count = 10
```

**2. Add Application Load Balancer (ALB):**

```hcl
# terraform/modules/alb/main.tf
resource "aws_lb" "main" {
  name               = "${var.environment}-ai-video-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.subnet_ids

  tags = {
    Name = "${var.environment}-ai-video-alb"
  }
}

resource "aws_lb_target_group" "backend" {
  name     = "${var.environment}-backend-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    timeout             = 5
    unhealthy_threshold = 2
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

# HTTPS listener (recommended for production)
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.ssl_certificate_arn  # From ACM

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}
```

**3. Configure Auto-Scaling:**

```hcl
# terraform/modules/ecs/autoscaling.tf
resource "aws_appautoscaling_target" "ecs" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${var.cluster_name}/${var.service_name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# Scale based on CPU utilization
resource "aws_appautoscaling_policy" "cpu" {
  name               = "${var.service_name}-cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0  # Scale at 70% CPU
  }
}

# Scale based on memory utilization
resource "aws_appautoscaling_policy" "memory" {
  name               = "${var.service_name}-memory-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value = 70.0  # Scale at 70% memory
  }
}

# Scale based on request count (custom metric)
resource "aws_appautoscaling_policy" "requests" {
  name               = "${var.service_name}-requests-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
      resource_label         = "${aws_lb.main.arn_suffix}/${aws_lb_target_group.backend.arn_suffix}"
    }
    target_value = 1000.0  # Scale at 1000 requests/target
  }
}
```

**4. Update ECS service to use ALB:**

```hcl
# terraform/modules/ecs/main.tf
resource "aws_ecs_service" "main" {
  # ... existing configuration ...

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "ai-video-backend"
    container_port   = 8000
  }

  depends_on = [var.lb_listener]
}
```

#### Benefits
- High availability (multiple tasks across AZs)
- Automatic failover
- Load distribution
- Zero-downtime deployments

#### Costs
- ALB: ~$16/month base + $0.008/LCU-hour
- Additional ECS tasks: ~$15-36/task/month
- Total for 3 tasks + ALB: ~$70-130/month

### Database Read Replicas

For read-heavy workloads:

```hcl
# terraform/modules/rds/read_replica.tf
resource "aws_db_instance" "read_replica" {
  identifier             = "${var.identifier}-replica"
  replicate_source_db    = aws_db_instance.main.identifier
  instance_class         = var.instance_class
  publicly_accessible    = false
  skip_final_snapshot    = true

  tags = {
    Name = "${var.environment}-db-replica"
  }
}
```

**Configuration in application:**

```python
# backend/app/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Write database (primary)
write_engine = create_engine(os.getenv("DATABASE_URL"))
WriteSession = sessionmaker(bind=write_engine)

# Read database (replica)
read_engine = create_engine(os.getenv("DATABASE_READ_URL"))
ReadSession = sessionmaker(bind=read_engine)

# Use read replica for queries
def get_generations():
    session = ReadSession()
    return session.query(GenerationJob).all()

# Use primary for writes
def create_generation(data):
    session = WriteSession()
    job = GenerationJob(**data)
    session.add(job)
    session.commit()
```

**Benefits:**
- Offload read queries from primary database
- Improved read performance
- Can create multiple replicas in different AZs

**Costs:**
- Same as primary instance: ~$12/month per replica

---

## Vertical Scaling

Vertical scaling increases resources of existing instances.

### ECS Task Scaling

**Current:** 1 vCPU, 2GB RAM

**Recommended tiers:**

| Tier | vCPU | Memory | Monthly Cost (24/7) | Use Case |
|------|------|--------|---------------------|----------|
| **Micro** | 0.5 | 1GB | $18.02 | Very light load |
| **Small** | 1 | 2GB | $36.04 | **Current (MVP)** |
| **Medium** | 2 | 4GB | $72.08 | Moderate load |
| **Large** | 4 | 8GB | $144.16 | Heavy processing |

**When to upgrade:**
- CPU consistently >70%
- Memory consistently >70%
- Video processing taking >5 minutes
- Concurrent generation limit reached

**Implementation:**

```hcl
# terraform/terraform.tfvars
task_cpu    = "2048"  # 2 vCPU
task_memory = "4096"  # 4 GB

terraform apply
```

### RDS Instance Scaling

**Current:** db.t4g.micro (2 vCPU, 1GB RAM, 80 connections)

**Upgrade path:**

| Instance Class | vCPU | RAM | Connections | Monthly Cost | Use Case |
|----------------|------|-----|-------------|--------------|----------|
| **db.t4g.micro** | 2 | 1GB | 80 | $12.26 | **Current (MVP)** |
| **db.t4g.small** | 2 | 2GB | 160 | $24.53 | Growing traffic |
| **db.t4g.medium** | 2 | 4GB | 320 | $49.06 | Moderate load |
| **db.t4g.large** | 2 | 8GB | 640 | $98.11 | High load |
| **db.m6g.large** | 2 | 8GB | 640 | $116.07 | Production-grade |

**When to upgrade:**
- Connection pool exhaustion
- CPU >70%
- Storage I/O bottleneck
- Query latency >500ms

**Implementation:**

```hcl
# terraform/terraform.tfvars
db_instance_class = "db.t4g.small"

terraform apply
# Note: RDS instance change causes brief downtime (1-2 minutes)
```

### ElastiCache Scaling

**Current:** cache.t4g.micro (2 vCPU, 0.5GB RAM)

**Upgrade path:**

| Node Type | vCPU | RAM | Monthly Cost | Use Case |
|-----------|------|-----|--------------|----------|
| **cache.t4g.micro** | 2 | 0.5GB | $11.52 | **Current (MVP)** |
| **cache.t4g.small** | 2 | 1.37GB | $23.36 | Growing cache |
| **cache.t4g.medium** | 2 | 3.09GB | $46.72 | Heavy caching |
| **cache.m6g.large** | 2 | 6.38GB | $91.25 | Production-grade |

**When to upgrade:**
- Cache eviction rate >10%
- Memory usage >80%
- Connection limits reached

**Implementation:**

```hcl
# terraform/terraform.tfvars
redis_node_type = "cache.t4g.small"

terraform apply
```

### Storage Scaling

**RDS Storage:**

```hcl
# Increase storage size (no downtime)
db_allocated_storage = 100  # 100GB instead of 20GB

# Enable autoscaling storage
resource "aws_db_instance" "main" {
  # ... existing config ...

  max_allocated_storage = 200  # Auto-scale up to 200GB
}
```

**S3:** No limits, scales automatically. Monitor costs.

---

## Database Optimization

### Indexing Strategy

**Current indexes:** Defined in `docker/postgres/init.sql`

**Additional indexes for scale:**

```sql
-- Speed up common queries
CREATE INDEX idx_jobs_session_status ON generation_jobs(session_id, status);
CREATE INDEX idx_clips_job_status ON clips(job_id, status);
CREATE INDEX idx_compositions_created ON compositions(created_at DESC);

-- Partial indexes for active jobs
CREATE INDEX idx_active_jobs ON generation_jobs(created_at)
  WHERE status IN ('pending', 'planning', 'generating', 'composing');

-- Index for JSON fields (PostgreSQL 17)
CREATE INDEX idx_jobs_planned_scenes ON generation_jobs USING gin(planned_scenes);

-- Covering indexes (include columns)
CREATE INDEX idx_jobs_list_covering ON generation_jobs(created_at DESC)
  INCLUDE (id, job_type, status, prompt, duration_seconds);
```

### Query Optimization

**Identify slow queries:**

```sql
-- Enable pg_stat_statements
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slowest queries
SELECT
  query,
  calls,
  total_exec_time / 1000 AS total_seconds,
  mean_exec_time / 1000 AS mean_seconds,
  max_exec_time / 1000 AS max_seconds
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;
```

**Optimize common patterns:**

```python
# BAD: N+1 query problem
jobs = db.query(GenerationJob).all()
for job in jobs:
    clips = db.query(Clip).filter(Clip.job_id == job.id).all()  # N queries!

# GOOD: Use eager loading
jobs = db.query(GenerationJob).options(
    joinedload(GenerationJob.clips)
).all()  # 1 query!

# GOOD: Use select_in loading for many-to-many
jobs = db.query(GenerationJob).options(
    selectinload(GenerationJob.clips)
).all()
```

### Connection Pooling

**Current:** SQLAlchemy connection pool (10 connections)

**Scaled configuration:**

```python
# backend/app/db.py
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,           # Base connections
    max_overflow=40,        # Additional connections
    pool_timeout=30,        # Wait timeout
    pool_recycle=3600,      # Recycle connections every hour
    pool_pre_ping=True,     # Test connections before use
    echo_pool=True          # Log pool events (debug)
)
```

**Consider PgBouncer for very high connection counts:**

```yaml
# docker-compose.yml (for local testing)
pgbouncer:
  image: pgbouncer/pgbouncer:latest
  environment:
    DATABASES_HOST: postgres
    DATABASES_PORT: 5432
    DATABASES_USER: ai_video_user
    DATABASES_PASSWORD: password
    DATABASES_DBNAME: ai_video_pipeline
    POOL_MODE: transaction
    MAX_CLIENT_CONN: 1000
    DEFAULT_POOL_SIZE: 25
  ports:
    - "6432:6432"

# Application connects to PgBouncer instead of PostgreSQL directly
# DATABASE_URL=postgresql://user:pass@pgbouncer:6432/ai_video_pipeline
```

**Benefits:**
- Supports 1000s of client connections with only 25 database connections
- Connection pooling at infrastructure level
- Reduced database load

**Costs:**
- Run PgBouncer on separate ECS task: ~$15-30/month

### Database Maintenance

```sql
-- Regular VACUUM to reclaim space
VACUUM ANALYZE generation_jobs;
VACUUM ANALYZE clips;
VACUUM ANALYZE compositions;

-- Auto-vacuum settings (postgresql.conf or RDS parameter group)
-- autovacuum = on
-- autovacuum_naptime = 1min
-- autovacuum_vacuum_scale_factor = 0.1

-- Reindex periodically (monthly)
REINDEX TABLE generation_jobs;
REINDEX TABLE clips;

-- Update statistics
ANALYZE generation_jobs;
ANALYZE clips;
```

---

## Caching Strategies

### Current Caching

**Redis cache for:**
- User sessions
- Job queue (Celery)
- Basic key-value caching

### Enhanced Caching Strategies

#### 1. API Response Caching

```python
# backend/app/services/cache.py
from functools import wraps
import hashlib
import json

def cache_response(ttl=3600):
    """Cache API responses in Redis"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"response:{func.__name__}:{hash(args)}:{hash(frozenset(kwargs.items()))}"

            # Check cache
            cached = await redis.get(cache_key)
            if cached:
                return json.loads(cached)

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await redis.setex(cache_key, ttl, json.dumps(result))

            return result
        return wrapper
    return decorator

# Usage:
@router.get("/api/v1/generations/{job_id}")
@cache_response(ttl=300)  # Cache for 5 minutes
async def get_generation(job_id: str):
    return db.query(GenerationJob).filter_by(id=job_id).first()
```

#### 2. Prompt Similarity Caching

```python
# backend/app/services/prompt_cache.py
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class PromptCache:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.threshold = 0.85  # 85% similarity

    async def find_similar_clip(self, prompt: str) -> Optional[str]:
        """Find cached clip for similar prompt"""
        # Encode new prompt
        new_embedding = self.model.encode([prompt])[0]

        # Get recent prompts from Redis
        cached_prompts = await redis.smembers("prompt_cache:recent")

        for cached in cached_prompts:
            data = json.loads(cached)
            cached_embedding = np.array(data['embedding'])

            # Calculate similarity
            similarity = cosine_similarity(
                [new_embedding],
                [cached_embedding]
            )[0][0]

            if similarity >= self.threshold:
                return data['clip_url']  # Reuse this clip!

        return None

    async def cache_clip(self, prompt: str, clip_url: str):
        """Cache clip with prompt embedding"""
        embedding = self.model.encode([prompt])[0]

        data = {
            'prompt': prompt,
            'embedding': embedding.tolist(),
            'clip_url': clip_url
        }

        # Add to cache (expire after 30 days)
        await redis.sadd("prompt_cache:recent", json.dumps(data))
        await redis.expire("prompt_cache:recent", 30 * 24 * 3600)
```

**Expected savings:** 20-40% reduction in Replicate API costs.

#### 3. Database Query Caching

```python
# Cache expensive database queries
@cache_response(ttl=3600)
async def get_user_video_history(user_id: str):
    return db.query(GenerationJob).filter_by(
        session_id=user_id
    ).order_by(
        GenerationJob.created_at.desc()
    ).limit(50).all()
```

#### 4. S3 URL Caching

```python
# Cache presigned S3 URLs (reuse instead of regenerating)
async def get_download_url(composition_id: str):
    cache_key = f"s3_url:{composition_id}"

    cached_url = await redis.get(cache_key)
    if cached_url:
        return cached_url

    # Generate new presigned URL (expires in 1 hour)
    url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': key},
        ExpiresIn=3600
    )

    # Cache for 45 minutes (less than expiry)
    await redis.setex(cache_key, 2700, url)

    return url
```

### Redis Cluster Mode (High Availability)

For production-grade caching:

```hcl
# terraform/modules/elasticache/cluster.tf
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "ai-video-redis-cluster"
  replication_group_description = "Redis cluster for AI Video Pipeline"

  node_type            = "cache.t4g.small"
  number_cache_clusters = 3  # 1 primary + 2 replicas

  port                 = 6379
  parameter_group_name = "default.redis7"
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [var.security_group_id]

  automatic_failover_enabled = true  # Auto-failover to replica
  multi_az_enabled          = true   # Multi-AZ for HA

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  snapshot_retention_limit = 5
  snapshot_window         = "03:00-05:00"
}
```

**Benefits:**
- High availability (automatic failover)
- Read replicas for read-heavy workloads
- Multi-AZ deployment

**Costs:**
- 3 nodes × $23.36 = ~$70/month (cache.t4g.small)

---

## Traffic Projections

### Current Capacity (MVP)

| Metric | Current |
|--------|---------|
| Concurrent users | 5-10 |
| Videos/month | 100 |
| API requests/min | ~100 |
| Database QPS | ~500 |
| Cache OPS | ~1000 |

### Target Capacity (Post-MVP)

| Metric | Target | Required Scaling |
|--------|--------|-----------------|
| Concurrent users | 50-100 | 10x |
| Videos/month | 1000-5000 | 10-50x |
| API requests/min | 1000-5000 | 10-50x |
| Database QPS | 5000-10000 | 10-20x |
| Cache OPS | 10000-50000 | 10-50x |

### Capacity Planning by User Count

#### 100 Users
**Infrastructure:**
- ECS: 2-3 tasks (1 vCPU, 2GB each)
- RDS: db.t4g.small
- ElastiCache: cache.t4g.small
- ALB: Required

**Monthly costs:** ~$100-150
**Videos/month:** ~500-1000

#### 500 Users
**Infrastructure:**
- ECS: 5-10 tasks (2 vCPU, 4GB each) with auto-scaling
- RDS: db.t4g.medium + 1 read replica
- ElastiCache: 3-node cluster (cache.t4g.small)
- ALB: Required
- CloudFront: Recommended

**Monthly costs:** ~$400-600
**Videos/month:** ~2500-5000

#### 1000+ Users
**Infrastructure:**
- ECS: 10-20 tasks (2-4 vCPU, 4-8GB each)
- RDS: db.m6g.large + 2 read replicas
- ElastiCache: 3-node cluster (cache.m6g.large)
- ALB: Required
- CloudFront: Required
- WAF: Recommended

**Monthly costs:** ~$1000-2000
**Videos/month:** ~5000-10000

### Bottleneck Analysis

**At each scale:**

| Users | Primary Bottleneck | Solution |
|-------|-------------------|----------|
| 10-50 | Replicate API rate limits | Upgrade Replicate plan |
| 50-100 | Single ECS task | Add ALB + auto-scaling |
| 100-500 | Database connections | Upgrade RDS, add read replicas |
| 500-1000 | FFmpeg CPU | Increase ECS task CPU, more tasks |
| 1000+ | All of the above | Full multi-tier scaling |

---

## When to Scale

### Monitoring Thresholds

Set up CloudWatch alarms for these metrics:

#### ECS Task Metrics
```bash
# CPU Utilization
# Scale up: >70% for 5 minutes
# Scale down: <30% for 10 minutes

# Memory Utilization
# Scale up: >70% for 5 minutes
# Scale down: <30% for 10 minutes

# Running Task Count
# Alert if <1 (no redundancy)
# Alert if >max_count (scaling limit hit)
```

#### Database Metrics
```bash
# DatabaseConnections
# Alert: >80% of max_connections
# Upgrade: Consistently >80%

# CPUUtilization
# Alert: >70% for 10 minutes
# Upgrade: Consistently >70%

# FreeableMemory
# Alert: <20% free
# Upgrade: <20% free for >1 hour

# ReadLatency / WriteLatency
# Alert: >100ms
# Optimize: >50ms average
```

#### ElastiCache Metrics
```bash
# CPUUtilization
# Alert: >70%
# Upgrade: Consistently >70%

# Evictions
# Alert: >100/minute
# Upgrade: Consistently evicting

# CurrConnections
# Alert: >80% of max
# Upgrade: Near max connections
```

#### Application Metrics
```bash
# Video Generation Queue Depth
# Alert: >10 pending jobs
# Scale: >20 pending jobs

# Average Generation Time
# Alert: >5 minutes
# Optimize: >3 minutes average

# Error Rate
# Alert: >5% errors
# Investigate: >1% errors
```

### Scaling Decision Matrix

| Metric | Current | Action Threshold | Action |
|--------|---------|-----------------|--------|
| **CPU >70%** | Single task | Sustained >5 min | Add ECS tasks (horizontal) |
| **Memory >70%** | 2GB | Sustained >5 min | Increase task memory (vertical) |
| **Latency >1s** | ~300ms | 90th percentile | Optimize queries, add caching |
| **Queue depth >10** | <5 | Sustained | Add ECS tasks, increase concurrency |
| **DB connections >80%** | ~20/80 | Any spike | Upgrade RDS instance |
| **Cache evictions >100/min** | Low | Sustained | Upgrade ElastiCache |
| **Error rate >5%** | <1% | Any spike | Investigate and fix |

### Scaling Checklist

#### Before Scaling
- [ ] Identify bottleneck (CPU, memory, database, cache)
- [ ] Review CloudWatch metrics (past 7-14 days)
- [ ] Check error logs for patterns
- [ ] Estimate cost impact of scaling
- [ ] Plan scaling during low-traffic window
- [ ] Backup database before infrastructure changes
- [ ] Notify team of planned scaling

#### During Scaling
- [ ] Monitor CloudWatch metrics in real-time
- [ ] Watch application logs for errors
- [ ] Test critical endpoints after changes
- [ ] Verify auto-scaling policies trigger correctly
- [ ] Check database connection pool settings

#### After Scaling
- [ ] Verify performance improvements
- [ ] Monitor for 24-48 hours
- [ ] Adjust auto-scaling thresholds if needed
- [ ] Update documentation with new configuration
- [ ] Review and optimize costs

---

## Scaling Roadmap

### Phase 1: MVP Foundation (Month 1-2)
**Goal:** Stable foundation for 10-50 users

**Actions:**
- [x] Deploy single ECS task
- [x] RDS db.t4g.micro
- [x] ElastiCache cache.t4g.micro
- [x] Basic monitoring and alerting
- [ ] Optimize slow queries
- [ ] Implement basic caching
- [ ] Set up budget alerts

**Costs:** $42-50/month

### Phase 2: Early Growth (Month 3-6)
**Goal:** Support 50-100 users reliably

**Actions:**
- [ ] Add Application Load Balancer
- [ ] Scale to 2-3 ECS tasks
- [ ] Enable ECS auto-scaling
- [ ] Upgrade RDS to db.t4g.small
- [ ] Implement prompt similarity caching
- [ ] Add read replica (if needed)
- [ ] Set up CloudFront CDN

**Costs:** $100-200/month

### Phase 3: Scaling Up (Month 6-12)
**Goal:** Handle 100-500 users

**Actions:**
- [ ] Increase to 5-10 ECS tasks (auto-scaled)
- [ ] Upgrade to 2 vCPU, 4GB tasks
- [ ] Upgrade RDS to db.t4g.medium
- [ ] Add 1-2 read replicas
- [ ] Upgrade to 3-node Redis cluster
- [ ] Implement PgBouncer for connection pooling
- [ ] Aggressive response caching
- [ ] Consider Aurora PostgreSQL

**Costs:** $400-700/month

### Phase 4: Production Scale (Year 2+)
**Goal:** Support 1000+ users

**Actions:**
- [ ] Multi-region deployment for redundancy
- [ ] Database sharding (if needed)
- [ ] Dedicated video processing queue
- [ ] Kubernetes migration (consider EKS)
- [ ] Microservices architecture
- [ ] Separate frontend CDN
- [ ] Real-time analytics dashboard

**Costs:** $1000-3000/month

---

## Advanced Scaling Techniques

### Multi-Region Deployment

For global reach and disaster recovery:

```
Primary Region (us-east-2):
- ECS Fargate cluster
- RDS primary database
- ElastiCache Redis
- S3 bucket (primary)

Secondary Region (us-west-2):
- ECS Fargate cluster (standby or active-active)
- RDS read replica (cross-region)
- ElastiCache Redis (separate cluster)
- S3 bucket (cross-region replication)

Route 53:
- Latency-based routing
- Health checks on both regions
- Automatic failover
```

**Benefits:**
- Lower latency for global users
- Disaster recovery
- High availability

**Costs:**
- ~2x infrastructure costs
- Data transfer between regions
- Cross-region replication

### Database Sharding

For very high database load (1M+ videos):

```sql
-- Shard by user_id hash
Shard 1: user_id % 4 == 0
Shard 2: user_id % 4 == 1
Shard 3: user_id % 4 == 2
Shard 4: user_id % 4 == 3

-- Each shard is a separate RDS instance
-- Application router determines which shard to query
```

**When to implement:** Database load >10,000 QPS

### Serverless Options

**AWS Lambda for video processing:**
- Replace ECS with Lambda functions
- Pay only for execution time
- Auto-scales to thousands of concurrent executions

**Trade-offs:**
- 15-minute Lambda timeout (may not be enough)
- Cold start latency
- More complex architecture

### Kubernetes (EKS) Migration

For very large scale (10,000+ users):

**Benefits:**
- Better resource utilization
- More flexible scaling
- Broader ecosystem (Helm, Istio, etc.)
- Multi-cloud portability

**Costs:**
- EKS control plane: $73/month
- Worker nodes: Similar to ECS Fargate
- Additional complexity

---

## Cost Impact of Scaling

| Phase | Users | ECS | RDS | Cache | ALB | CloudFront | Total/Month |
|-------|-------|-----|-----|-------|-----|-----------|-------------|
| **MVP** | 10-50 | $15-36 | $12 | $12 | - | - | **$42-50** |
| **Early Growth** | 50-100 | $60-120 | $25 | $24 | $16 | $0-10 | **$125-195** |
| **Scaling Up** | 100-500 | $200-400 | $100 | $70 | $20 | $20-50 | **$410-640** |
| **Production** | 1000+ | $500-1000 | $300 | $150 | $30 | $50-100 | **$1030-1580** |

**Note:** Add Replicate API costs (variable based on usage).

---

## References

- [Deployment Guide](./deployment-guide.md)
- [Architecture Guide](./architecture.md)
- [Troubleshooting Guide](./troubleshooting.md)
- [Cost Tracking Guide](./cost-tracking.md)
- [AWS Auto Scaling](https://aws.amazon.com/autoscaling/)
- [RDS Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html)
- [ElastiCache Best Practices](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/BestPractices.html)

---

**Scaling Guide Version:** 1.0.0
**Last Updated:** 2025-11-15
**Maintained by:** DevOps Team
