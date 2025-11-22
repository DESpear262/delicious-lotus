# System Architecture

## Overview

The FFmpeg Backend Service is a distributed system designed for asynchronous video processing using a microservices-inspired architecture. It leverages FastAPI for the web layer, PostgreSQL for persistence, Redis for job queuing, and FFmpeg for video processing.

## High-Level Architecture

```mermaid
graph TB
    Client[Client Applications]
    LB[Load Balancer]
    API1[API Server 1]
    API2[API Server 2]
    APIn[API Server N]
    Worker1[Worker 1]
    Worker2[Worker 2]
    WorkerN[Worker N]
    DB[(PostgreSQL)]
    Redis[(Redis)]
    S3[S3 Storage]

    Client -->|HTTP/WebSocket| LB
    LB --> API1
    LB --> API2
    LB --> APIn

    API1 -->|Read/Write| DB
    API2 -->|Read/Write| DB
    APIn -->|Read/Write| DB

    API1 -->|Enqueue Jobs| Redis
    API2 -->|Enqueue Jobs| Redis
    APIn -->|Enqueue Jobs| Redis

    Redis -->|Process Jobs| Worker1
    Redis -->|Process Jobs| Worker2
    Redis -->|Process Jobs| WorkerN

    Worker1 -->|Update Status| DB
    Worker2 -->|Update Status| DB
    WorkerN -->|Update Status| DB

    Worker1 -->|Upload/Download| S3
    Worker2 -->|Upload/Download| S3
    WorkerN -->|Upload/Download| S3

    Worker1 -->|Publish Events| Redis
    Worker2 -->|Publish Events| Redis
    WorkerN -->|Publish Events| Redis

    Redis -->|Subscribe Events| API1
    Redis -->|Subscribe Events| API2
    Redis -->|Subscribe Events| APIn

    API1 -->|WebSocket Updates| Client
    API2 -->|WebSocket Updates| Client
    APIn -->|WebSocket Updates| Client
```

## Component Architecture

### API Server

```mermaid
graph LR
    Request[HTTP Request]
    Middleware[Middleware Stack]
    Router[API Router]
    Handler[Route Handler]
    Service[Service Layer]
    DB[(Database)]
    Queue[Job Queue]

    Request --> Middleware
    Middleware --> Router
    Router --> Handler
    Handler --> Service
    Service --> DB
    Service --> Queue

    Middleware -->|Request ID| Middleware
    Middleware -->|Logging| Middleware
    Middleware -->|Rate Limit| Middleware
    Middleware -->|Auth| Middleware
    Middleware -->|Metrics| Middleware
```

**Middleware Stack** (executed in order):
1. **RequestIDMiddleware**: Generates unique request ID
2. **LoggingMiddleware**: Structured logging for all requests
3. **MetricsMiddleware**: Collects request metrics
4. **InternalAuthMiddleware**: Authentication for internal endpoints
5. **RateLimitMiddleware**: Rate limiting per client
6. **CORSMiddleware**: Cross-origin resource sharing

### Worker Architecture

```mermaid
graph TB
    Queue[Redis Queue]
    Worker[RQ Worker]
    JobHandler[Job Handler]
    FFmpeg[FFmpeg Service]
    S3Service[S3 Service]
    DB[(Database)]
    Redis[(Redis PubSub)]

    Queue -->|Dequeue Job| Worker
    Worker -->|Execute| JobHandler
    JobHandler -->|Download Assets| S3Service
    JobHandler -->|Process Video| FFmpeg
    JobHandler -->|Upload Result| S3Service
    JobHandler -->|Update Status| DB
    JobHandler -->|Publish Events| Redis

    FFmpeg -->|Progress Updates| JobHandler
    JobHandler -->|Progress %| Redis
```

**Worker Process Flow**:
1. Dequeue job from Redis
2. Download video assets from S3
3. Execute FFmpeg command
4. Monitor FFmpeg progress
5. Publish progress updates to Redis
6. Upload processed video to S3
7. Update database with final status
8. Clean up temporary files

### Data Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant DB
    participant Queue
    participant Worker
    participant FFmpeg
    participant S3

    Client->>API: POST /compositions
    API->>DB: Create composition record
    DB-->>API: Composition ID
    API->>Queue: Enqueue job
    Queue-->>API: Job ID
    API-->>Client: 202 Accepted (composition_id)

    Queue->>Worker: Dequeue job
    Worker->>DB: Update status: processing
    Worker->>S3: Download video clips
    S3-->>Worker: Video files

    Worker->>FFmpeg: Execute composition
    loop Processing
        FFmpeg-->>Worker: Progress update
        Worker->>Queue: Publish progress event
        Queue->>API: Subscribe to events
        API->>Client: WebSocket progress update
    end

    FFmpeg-->>Worker: Completed video
    Worker->>S3: Upload result
    S3-->>Worker: Upload URL
    Worker->>DB: Update status: completed
    Worker->>Queue: Publish completion event
    Queue->>API: Completion event
    API->>Client: WebSocket completion

    Client->>API: GET /compositions/{id}/download
    API->>DB: Get composition
    DB-->>API: Composition data
    API->>S3: Generate presigned URL
    S3-->>API: Presigned URL
    API-->>Client: Download URL
```

## Database Schema

```mermaid
erDiagram
    COMPOSITION ||--o{ JOB : "has"
    COMPOSITION {
        uuid id PK
        string title
        jsonb config
        string status
        timestamp created_at
        timestamp updated_at
        timestamp completed_at
        string error_message
        string output_url
    }

    JOB {
        uuid id PK
        uuid composition_id FK
        string job_id
        string status
        integer progress
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }
```

**Composition States**:
- `pending`: Composition created, waiting for processing
- `queued`: Job enqueued in Redis
- `processing`: Worker actively processing
- `completed`: Successfully processed
- `failed`: Processing failed with error

## Storage Architecture

### S3 Bucket Structure

```
s3://bucket-name/
├── inputs/
│   ├── {composition_id}/
│   │   ├── clip_0.mp4
│   │   ├── clip_1.mp4
│   │   ├── audio.mp3
│   │   └── overlay.png
├── outputs/
│   ├── {composition_id}/
│   │   ├── final.mp4
│   │   └── thumbnail.jpg
└── temp/
    └── {job_id}/
        └── intermediate_files/
```

### Temporary File Management

```mermaid
graph LR
    Download[Download Assets]
    Process[Process Video]
    Upload[Upload Result]
    Cleanup[Cleanup]

    Download -->|/tmp/job_id/inputs| Process
    Process -->|/tmp/job_id/output| Upload
    Upload --> Cleanup
    Cleanup -->|Delete /tmp/job_id| End[End]
```

## Redis Architecture

### Job Queues

```
Queue Priorities:
├── high (priority: 10)
│   └── urgent compositions
├── default (priority: 5)
│   └── normal compositions
└── low (priority: 1)
    └── background tasks
```

### PubSub Channels

```
Channels:
├── composition:{composition_id}:progress
│   └── Progress updates (0-100%)
├── composition:{composition_id}:status
│   └── Status changes
└── composition:{composition_id}:error
    └── Error events
```

## Scaling Considerations

### Horizontal Scaling

**API Servers**:
- Stateless design allows unlimited horizontal scaling
- Load balancer distributes requests
- WebSocket connections use Redis PubSub for cross-instance communication

**Workers**:
- Add workers to increase concurrent job processing
- Each worker can process multiple jobs (based on CPU cores)
- Workers can be specialized by queue (high, default, low)

### Vertical Scaling

**API Servers**:
- Increase CPU for higher request throughput
- Increase memory for larger request payloads

**Workers**:
- Increase CPU cores for FFmpeg parallel processing
- Increase memory for processing large video files
- Increase disk I/O for faster temporary file operations

### Database Optimization

**Connection Pooling**:
```python
# SQLAlchemy async pool configuration
pool_size = 20  # Maximum connections
max_overflow = 10  # Additional connections under load
pool_timeout = 30  # Connection timeout
pool_recycle = 3600  # Recycle connections after 1 hour
```

**Indexes**:
```sql
CREATE INDEX idx_composition_status ON compositions(status);
CREATE INDEX idx_composition_created ON compositions(created_at DESC);
CREATE INDEX idx_job_composition_id ON jobs(composition_id);
CREATE INDEX idx_job_status ON jobs(status);
```

## Performance Characteristics

### Expected Throughput

| Metric | Value | Notes |
|--------|-------|-------|
| API Request Latency | < 100ms | P95 for GET requests |
| Composition Creation | < 200ms | Including DB write and job enqueue |
| Worker Processing | 1-5 min | Depends on video length and complexity |
| Concurrent Jobs | 5-10 | Per worker instance |
| API Requests/sec | 1000+ | With proper horizontal scaling |

### Resource Requirements

**API Server** (per instance):
- CPU: 2-4 cores
- Memory: 2-4 GB
- Disk: 10 GB
- Network: 1 Gbps

**Worker** (per instance):
- CPU: 4-8 cores (FFmpeg is CPU-intensive)
- Memory: 4-8 GB
- Disk: 50-100 GB (for temporary files)
- Network: 1 Gbps (for S3 uploads/downloads)

**Database**:
- CPU: 4-8 cores
- Memory: 8-16 GB
- Disk: 100+ GB SSD
- IOPS: 3000+ for production

**Redis**:
- CPU: 2-4 cores
- Memory: 4-8 GB
- Disk: 20 GB
- Persistence: AOF or RDB

## Security Architecture

```mermaid
graph TB
    Internet[Internet]
    WAF[Web Application Firewall]
    LB[Load Balancer/TLS Termination]
    API[API Servers]
    Internal[Internal API]
    Worker[Workers]

    Internet -->|HTTPS| WAF
    WAF -->|Rate Limit| LB
    LB -->|HTTP| API
    API -->|API Key Auth| Internal
    Internal -->|Callback| External[External Services]

    API -.->|IAM Roles| S3[(S3)]
    Worker -.->|IAM Roles| S3
    API -.->|Credentials| DB[(Database)]
    Worker -.->|Credentials| DB
```

**Security Layers**:
1. **Network**: WAF, DDoS protection, TLS 1.3
2. **Application**: Rate limiting, input validation, SQL injection prevention
3. **Authentication**: API keys for internal endpoints, JWT for user authentication
4. **Authorization**: Role-based access control (RBAC)
5. **Data**: Encryption at rest (S3, DB), encryption in transit (TLS)
6. **Secrets**: Environment variables, AWS Secrets Manager, HashiCorp Vault

## Monitoring and Observability

### Metrics

```mermaid
graph LR
    App[Application]
    Metrics[Metrics Middleware]
    Prometheus[Prometheus]
    Grafana[Grafana]

    App -->|Collect| Metrics
    Metrics -->|Expose /metrics| Prometheus
    Prometheus -->|Query| Grafana
```

**Key Metrics**:
- Request rate (requests/sec)
- Request latency (P50, P95, P99)
- Error rate (4xx, 5xx)
- Active connections
- Queue depth
- Worker utilization
- Job completion time
- FFmpeg processing time

### Logging

**Structured Logging Format**:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "ffmpeg-backend",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "composition_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Composition processing started",
  "duration_ms": 150,
  "status_code": 200
}
```

### Distributed Tracing

```mermaid
graph LR
    Request[HTTP Request]
    API[API Handler]
    Queue[Job Queue]
    Worker[Worker]
    FFmpeg[FFmpeg]

    Request -->|Trace ID| API
    API -->|Trace ID| Queue
    Queue -->|Trace ID| Worker
    Worker -->|Trace ID| FFmpeg

    API -.->|Span| Jaeger[Jaeger/OpenTelemetry]
    Worker -.->|Span| Jaeger
```

## Disaster Recovery

### Backup Strategy

**Database**:
- Daily automated backups
- Point-in-time recovery
- Cross-region replication
- Retention: 30 days

**S3**:
- Versioning enabled
- Cross-region replication
- Lifecycle policies for old files
- Retention: 90 days for outputs

**Redis**:
- AOF persistence
- RDB snapshots every 6 hours
- Replica for high availability

### Recovery Procedures

1. **API Server Failure**: Auto-scaling group replaces failed instances
2. **Worker Failure**: Jobs automatically retry from queue
3. **Database Failure**: Failover to replica (< 30s downtime)
4. **Redis Failure**: Restart from persistence, re-enqueue jobs
5. **S3 Outage**: Retry with exponential backoff
