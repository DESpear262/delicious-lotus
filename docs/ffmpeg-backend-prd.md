# Track 3: FFmpeg Backend (Python) – Feature PRD v2.0
*Complete Implementation Specification with Technical Decisions*

---

## 1. Executive Summary

Track 3 is the **Video Composition & Post-Processing Service** for the AI Video Generation Pipeline, providing FFmpeg-based video processing with real-time progress tracking via WebSockets.

**Key Decisions:**
- **Queue System**: RQ (Redis Queue) with AWS ElastiCache
- **Storage**: AWS S3 for assets
- **Database**: PostgreSQL 17
- **Container**: Docker with static FFmpeg binary
- **API Framework**: FastAPI with built-in Swagger/ReDoc

---

## 2. Scope

### 2.1 In Scope (MVP)

- Composition API (`/api/v1/compositions`)
- Internal clip-processing API (`/internal/v1/process-clips`)
- FFmpeg-based processing:
  - Multi-clip composition with timeline support
  - Native transitions (fade, crossfade, cut)
  - Text overlays (drawtext filter)
  - Audio mixing (music + optional voiceover)
  - Simple color-correction presets
  - CRF-based H.264 encoding
  - 720p output (1280x720)
- Real-time progress tracking via WebSocket
- S3-hosted final video downloads
- ffprobe-based validation (configurable)
- Built-in API documentation:
  - Swagger UI (`/docs`)
  - ReDoc (`/redoc`)
- Automatic temp file cleanup with debug override

### 2.2 Out of Scope (MVP)

- Beat detection (Track 2 responsibility for MVP)
- LUT-based color grading
- GPU acceleration
- Custom/complex transitions
- Long-form content (>3 minutes)
- 1080p/4K output
- Frame interpolation/stabilization
- Multi-tenant isolation

---

## 3. Technology Stack

| Component | Technology | Details |
|-----------|-----------|---------|
| **API Framework** | FastAPI | v0.115+ with async support |
| **Queue System** | RQ (Redis Queue) | Simple, Python-native job queue |
| **Redis** | Redis 7.x | For queues and pub/sub |
| **Database** | PostgreSQL 17 | With connection pooling |
| **Storage** | AWS S3 | For source assets & final outputs |
| **Video Processing** | FFmpeg 6.x | Static binary via Docker |
| **Container** | Docker | Python 3.13-slim base |
| **Logging** | Python logging + pythonjsonlogger | JSON structured logs |
| **Language** | Python 3.13 | With type hints |

---

## 4. Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend UI   │────▶│   FastAPI App   │────▶│   RQ Workers    │
│    (Track 1)    │     │   (Public API)   │     │  (FFmpeg Jobs)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                          │
                               ▼                          ▼
                        ┌─────────────┐           ┌─────────────┐
                        │ PostgreSQL  │           │   AWS S3    │
                        │     17      │           │  (Storage)  │
                        └─────────────┘           └─────────────┘
                               │                          │
                               ▼                          ▼
                        ┌─────────────────────────────────┐
                        │            Redis 7.x            │
                        │   (Queue + Progress Tracking)   │
                        └─────────────────────────────────┘
```

---

## 5. API Specification

### 5.1 Public Composition APIs
Base path: `/api/v1`

#### POST `/api/v1/compositions`
Create new composition job.

**Request:**
```json
{
  "clips": [
    {
      "url": "s3://bucket/clip1.mp4",
      "start_time": 0,
      "end_time": 3.5,
      "trim_start": 0,
      "trim_end": 3.5,
      "transition_in": "fade",
      "transition_duration": 0.5
    }
  ],
  "audio": {
    "music_url": "s3://bucket/music.mp3",
    "voiceover_url": "s3://bucket/vo.mp3",
    "music_volume": 0.8,
    "voiceover_volume": 1.0
    },
  "overlays": [
    {
      "type": "text",
      "content": "Summer Sale!",
      "position": {"x": "center", "y": 100},
      "start_time": 0,
      "duration": 5,
      "style": {
        "font": "Arial",
        "size": 48,
        "color": "#FFFFFF",
        "shadow": true
      }
    }
  ],
  "output": {
    "resolution": "720p",
    "fps": 30,
    "crf": 21,
    "format": "mp4"
  }
}
```

**Response:**
```json
{
  "composition_id": "comp_abc123",
  "status": "queued",
  "created_at": "2025-11-14T10:00:00Z",
  "estimated_duration": 45,
  "websocket_url": "wss://api.example.com/ws/compositions/comp_abc123"
}
```

#### GET `/api/v1/compositions/{composition_id}`
Get composition status.

**Response:**
```json
{
  "composition_id": "comp_abc123",
  "status": "processing",
  "progress": {
    "stage": "encoding",
    "percentage": 65,
    "message": "Encoding final video"
  },
  "created_at": "2025-11-14T10:00:00Z",
  "updated_at": "2025-11-14T10:00:45Z",
  "output_url": null
}
```

#### GET `/api/v1/compositions/{composition_id}/download`
Returns redirect to S3 presigned URL when ready.

#### GET `/api/v1/compositions/{composition_id}/metadata`
Get detailed processing metadata.

### 5.2 Internal Service APIs
Base path: `/internal/v1`

#### POST `/internal/v1/process-clips`
Process clips from AI Backend.

**Request:**
```json
{
  "processing_id": "proc_xyz789",
  "clips": ["s3://bucket/raw1.mp4", "s3://bucket/raw2.mp4"],
  "operations": ["normalize", "color_correct", "thumbnail"],
  "callback_url": "http://ai-backend/internal/v1/processing-complete"
}
```

#### POST `/internal/v1/beat-detection` (Post-MVP)
Analyze audio for beat alignment.

### 5.3 Health & Monitoring

#### GET `/health`
Basic health check.

#### GET `/health/detailed`
Comprehensive health status:
```json
{
  "status": "healthy",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "s3": "healthy",
    "ffmpeg": "healthy"
  },
  "version": "1.0.0",
  "timestamp": "2025-11-14T10:00:00Z"
}
```

### 5.4 WebSocket Endpoints

#### WS `/ws/compositions/{composition_id}`
Real-time composition progress.

**Message Format:**
```json
{
  "type": "progress",
  "data": {
    "stage": "encoding",
    "percentage": 65,
    "message": "Encoding video",
    "timestamp": "2025-11-14T10:00:45Z"
  }
}
```

### 5.5 Developer APIs
Base path: `/dev` (enabled via `ENABLE_DEV_API=true`)

#### POST `/dev/test-generation`
Create mock generation for testing.

#### POST `/dev/reset-user`
Reset test user data.

---

## 6. Error Handling

### Standard Error Format
All errors follow this structure:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {},
    "timestamp": "2025-11-14T10:00:00Z",
    "request_id": "req_uuid"
  }
}
```

### Error Codes
| Code | HTTP Status | Description |
|------|------------|-------------|
| `COMPOSITION_NOT_FOUND` | 404 | Composition ID doesn't exist |
| `INVALID_CLIP_FORMAT` | 400 | Unsupported video format |
| `PROCESSING_FAILED` | 500 | FFmpeg processing error |
| `STORAGE_ERROR` | 503 | S3 unavailable |
| `QUEUE_FULL` | 503 | Too many pending jobs |
| `INVALID_TIMELINE` | 400 | Timeline validation failed |

---

## 7. FFmpeg Processing Pipeline

### 7.1 Installation (Docker)
```dockerfile
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Download static FFmpeg binary
RUN wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
    tar xvf ffmpeg-release-amd64-static.tar.xz && \
    mv ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ && \
    mv ffmpeg-*-amd64-static/ffprobe /usr/local/bin/ && \
    rm -rf ffmpeg-*

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.2 Composition Pipeline Steps

1. **Job Initialization**
   - Load configuration from PostgreSQL
   - Create temp directory: `/tmp/videogen/{job_id}`
   - Update status to "downloading"

2. **Asset Download**
   - Download clips from S3 to temp directory
   - Download audio files
   - Validate with ffprobe
   - Update progress (0-20%)

3. **Normalization**
   - Convert all clips to same resolution/fps
   - Ensure consistent codec (H.264)
   - Update progress (20-30%)

4. **Timeline Assembly**
   - Apply trim points to clips
   - Create concat demuxer file
   - Update progress (30-40%)

5. **Transition Processing**
   - Build filter complex for transitions
   - Apply fade/crossfade effects
   - Update progress (40-50%)

6. **Overlay Application**
   - Add text overlays with drawtext
   - Apply positioning and timing
   - Update progress (50-60%)

7. **Audio Processing**
   - Mix music and voiceover tracks
   - Apply volume adjustments
   - Add fade in/out
   - Update progress (60-70%)

8. **Final Encoding**
   - Encode with H.264, CRF 21
   - Target resolution 1280x720
   - Update progress (70-90%)

9. **Upload & Cleanup**
   - Upload to S3
   - Generate thumbnail
   - Clean temp files (unless `KEEP_TEMP_FILES=true`)
   - Update progress (90-100%)

### 7.3 FFmpeg Command Examples

**Basic composition with transitions:**
```bash
ffmpeg -i clip1.mp4 -i clip2.mp4 -i music.mp3 \
  -filter_complex "
    [0:v]fade=out:st=3:d=0.5[v0];
    [1:v]fade=in:st=0:d=0.5[v1];
    [v0][v1]concat=n=2:v=1:a=0[outv];
    [outv]scale=1280:720,
    drawtext=text='Summer Sale':x=(w-text_w)/2:y=100:
    fontsize=48:fontcolor=white:shadowx=2:shadowy=2[finalv]
  " \
  -map "[finalv]" -map 2:a \
  -c:v libx264 -crf 21 -preset medium \
  -c:a aac -b:a 192k \
  output.mp4
```

---

## 8. RQ Worker Implementation

### 8.1 Worker Configuration
```python
# worker.py
import os
from rq import Worker, Queue, Connection
import redis
from handlers import composition_handler, clip_processor

# Redis connection
redis_conn = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

# Queue definitions
queues = [
    Queue('high', connection=redis_conn),    # Urgent jobs
    Queue('default', connection=redis_conn),  # Normal compositions
    Queue('low', connection=redis_conn)       # Background tasks
]

if __name__ == '__main__':
    with Connection(redis_conn):
        worker = Worker(queues)
        worker.work(with_scheduler=True)
```

### 8.2 Job Handler
```python
# handlers/composition_handler.py
import subprocess
import json
from pathlib import Path
import boto3
import redis

redis_client = redis.from_url(os.getenv('REDIS_URL'))
s3_client = boto3.client('s3')

def process_composition(composition_id: str, config: dict):
    """Main composition processing function"""
    
    def update_progress(stage: str, percentage: int, message: str):
        """Update progress in Redis and publish to WebSocket channel"""
        progress_data = {
            "stage": stage,
            "percentage": percentage,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store current state
        redis_client.hset(
            f"composition:{composition_id}",
            mapping={
                "status": "processing",
                "progress": json.dumps(progress_data)
            }
        )
        
        # Publish for WebSocket subscribers
        redis_client.publish(
            f"composition:{composition_id}",
            json.dumps({
                "type": "progress",
                "data": progress_data
            })
        )
    
    try:
        # Processing pipeline
        update_progress("initializing", 0, "Starting composition")
        
        # Create temp directory
        temp_dir = Path(f"/tmp/videogen/{composition_id}")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Download assets
        update_progress("downloading", 10, "Downloading clips")
        # ... download logic ...
        
        # Build FFmpeg command
        update_progress("processing", 30, "Processing video")
        ffmpeg_cmd = build_ffmpeg_command(config, temp_dir)
        
        # Execute FFmpeg with progress parsing
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Parse FFmpeg progress output
        for line in process.stderr:
            if "time=" in line:
                # Extract time and calculate percentage
                current_time = parse_ffmpeg_time(line)
                total_duration = config.get('duration', 30)
                percentage = min(int((current_time / total_duration) * 60) + 40, 90)
                update_progress("encoding", percentage, f"Encoding video")
        
        # Upload to S3
        update_progress("uploading", 95, "Uploading to storage")
        output_url = upload_to_s3(temp_dir / "output.mp4", composition_id)
        
        # Success
        update_progress("completed", 100, "Composition complete")
        redis_client.hset(
            f"composition:{composition_id}",
            mapping={
                "status": "completed",
                "output_url": output_url
            }
        )
        
    except Exception as e:
        # Error handling
        logger.error(f"Composition failed: {str(e)}", extra={
            "composition_id": composition_id,
            "error": str(e)
        })
        
        redis_client.hset(
            f"composition:{composition_id}",
            "status", "failed",
            "error", str(e)
        )
        
        redis_client.publish(
            f"composition:{composition_id}",
            json.dumps({
                "type": "error",
                "data": {
                    "message": "Composition failed",
                    "error": str(e)
                }
            })
        )
        raise
    
    finally:
        # Cleanup
        if not os.getenv('KEEP_TEMP_FILES', 'false').lower() == 'true':
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
```

---

## 9. WebSocket Implementation

```python
# websocket_manager.py
import asyncio
import json
import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        
    async def connect(self, websocket: WebSocket, composition_id: str):
        """Accept WebSocket connection and subscribe to Redis channel"""
        await websocket.accept()
        
        # Add to active connections
        if composition_id not in self.active_connections:
            self.active_connections[composition_id] = []
        self.active_connections[composition_id].append(websocket)
        
        # Create Redis connection for this WebSocket
        redis_client = await redis.from_url(self.redis_url)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"composition:{composition_id}")
        
        try:
            # Send current status immediately
            current_status = await redis_client.hgetall(f"composition:{composition_id}")
            if current_status:
                await websocket.send_json({
                    "type": "status",
                    "data": {
                        "status": current_status.get(b"status", b"unknown").decode(),
                        "progress": json.loads(current_status.get(b"progress", b"{}").decode())
                    }
                })
            
            # Listen for updates
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    data = message['data']
                    if isinstance(data, bytes):
                        data = data.decode('utf-8')
                    await websocket.send_text(data)
                    
        except WebSocketDisconnect:
            self.disconnect(websocket, composition_id)
        finally:
            await pubsub.unsubscribe(f"composition:{composition_id}")
            await redis_client.close()
    
    def disconnect(self, websocket: WebSocket, composition_id: str):
        """Remove WebSocket from active connections"""
        if composition_id in self.active_connections:
            self.active_connections[composition_id].remove(websocket)
            if not self.active_connections[composition_id]:
                del self.active_connections[composition_id]

# Usage in FastAPI
manager = ConnectionManager()

@app.websocket("/ws/compositions/{composition_id}")
async def websocket_endpoint(websocket: WebSocket, composition_id: str):
    await manager.connect(websocket, composition_id)
```

---

## 10. Configuration Management

### 10.1 Environment Variables
```bash
# Core Settings
ENVIRONMENT=development|staging|production
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR

# AWS Configuration (S3 Only)
AWS_REGION=us-west-2
AWS_S3_BUCKET=videogen-assets
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# PostgreSQL Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/videogen
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# FFmpeg Settings
FFMPEG_BIN=/usr/local/bin/ffmpeg
FFPROBE_BIN=/usr/local/bin/ffprobe
DEFAULT_CRF=21
MAX_CONCURRENT_JOBS=5

# Processing Configuration
TMP_DIR=/tmp/videogen
KEEP_TEMP_FILES=false
RUN_FFPROBE_VALIDATION=true

# Feature Flags
ENABLE_DEV_API=false
ENABLE_BEAT_DETECTION=false
ENABLE_GPU_ENCODING=false
ENABLE_4K_OUTPUT=false

# Worker Configuration
RQ_WORKER_COUNT=3
RQ_JOB_TIMEOUT=300
RQ_RESULT_TTL=86400
```

### 10.2 Feature Flags Implementation
```python
# feature_flags.py
import os
from functools import wraps

class FeatureFlags:
    def __init__(self):
        self.flags = {
            'dev_api': os.getenv('ENABLE_DEV_API', 'false').lower() == 'true',
            'beat_detection': os.getenv('ENABLE_BEAT_DETECTION', 'false').lower() == 'true',
            'gpu_encoding': os.getenv('ENABLE_GPU_ENCODING', 'false').lower() == 'true',
            '4k_output': os.getenv('ENABLE_4K_OUTPUT', 'false').lower() == 'true'
        }
    
    def is_enabled(self, feature: str) -> bool:
        return self.flags.get(feature, False)
    
    def require_feature(self, feature: str):
        """Decorator to check feature flag"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.is_enabled(feature):
                    raise HTTPException(
                        status_code=404,
                        detail=f"Feature '{feature}' is not enabled"
                    )
                return await func(*args, **kwargs)
            return wrapper
        return decorator

features = FeatureFlags()

# Usage
@app.post("/dev/test-generation")
@features.require_feature('dev_api')
async def test_generation():
    return {"status": "test"}
```

---

## 11. Logging Configuration

```python
# logging_config.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging(log_level: str = "INFO"):
    """Configure structured JSON logging"""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove default handlers
    logger.handlers = []
    
    # Create JSON formatter
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={
            "asctime": "timestamp",
            "levelname": "level",
            "name": "logger"
        }
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler for production
    if os.getenv('ENVIRONMENT') == 'production':
        file_handler = logging.handlers.RotatingFileHandler(
            '/var/log/videogen/app.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add request ID to all logs
    import contextvars
    request_id_var = contextvars.ContextVar('request_id', default=None)
    
    class RequestIdFilter(logging.Filter):
        def filter(self, record):
            record.request_id = request_id_var.get()
            return True
    
    logger.addFilter(RequestIdFilter())
    
    return logger

# Initialize on startup
logger = setup_logging(os.getenv('LOG_LEVEL', 'INFO'))

# Usage examples
logger.info("Starting composition", extra={
    "composition_id": "comp_123",
    "clip_count": 5,
    "duration": 30
})

logger.error("FFmpeg failed", extra={
    "composition_id": "comp_123",
    "error": "Invalid codec",
    "command": ffmpeg_cmd
}, exc_info=True)
```

---

## 12. Database Schema

```sql
-- PostgreSQL 17 Schema

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Compositions table
CREATE TABLE compositions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    composition_id VARCHAR(50) UNIQUE NOT NULL,
    user_id VARCHAR(100),
    config JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    progress JSONB,
    output_url TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX idx_compositions_status ON compositions(status);
CREATE INDEX idx_compositions_user_id ON compositions(user_id);
CREATE INDEX idx_compositions_created_at ON compositions(created_at DESC);
CREATE INDEX idx_compositions_config ON compositions USING GIN(config);

-- Processing jobs table (internal)
CREATE TABLE processing_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    processing_id VARCHAR(50) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,
    source_service VARCHAR(100),
    config JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    callback_url TEXT,
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Job metrics table
CREATE TABLE job_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(50) NOT NULL,
    job_type VARCHAR(50) NOT NULL,
    duration_seconds FLOAT,
    cpu_time FLOAT,
    memory_peak_mb INTEGER,
    ffmpeg_stats JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_compositions_updated_at
    BEFORE UPDATE ON compositions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_processing_jobs_updated_at
    BEFORE UPDATE ON processing_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
```

---

## 13. Testing Strategy

### 13.1 Unit Tests
```python
# tests/test_ffmpeg_builder.py
import pytest
from services.ffmpeg_builder import FFmpegCommandBuilder

def test_basic_composition():
    builder = FFmpegCommandBuilder()
    cmd = builder.add_input("clip1.mp4").add_input("clip2.mp4").concat().build()
    assert "-i clip1.mp4" in cmd
    assert "-i clip2.mp4" in cmd
    assert "concat" in cmd

def test_text_overlay():
    builder = FFmpegCommandBuilder()
    cmd = builder.add_text_overlay("Test", x="center", y=100).build()
    assert "drawtext" in cmd
    assert "text='Test'" in cmd
```

### 13.2 Integration Tests
```python
# tests/integration/test_composition_flow.py
import asyncio
import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_full_composition_flow(client: TestClient, mock_s3):
    # Create composition
    response = client.post("/api/v1/compositions", json={
        "clips": [{"url": "s3://test/clip1.mp4"}],
        "output": {"resolution": "720p"}
    })
    assert response.status_code == 202
    comp_id = response.json()["composition_id"]
    
    # Check status
    response = client.get(f"/api/v1/compositions/{comp_id}")
    assert response.json()["status"] in ["queued", "processing"]
    
    # Wait for completion (with timeout)
    for _ in range(30):
        response = client.get(f"/api/v1/compositions/{comp_id}")
        if response.json()["status"] == "completed":
            break
        await asyncio.sleep(1)
    
    assert response.json()["status"] == "completed"
    assert response.json()["output_url"].startswith("https://")
```

### 13.3 Load Tests
```python
# tests/load/test_concurrent_jobs.py
import concurrent.futures
import requests

def create_composition(index):
    response = requests.post(
        "http://localhost:8000/api/v1/compositions",
        json={"clips": [...], "output": {...}}
    )
    return response.json()

def test_concurrent_load():
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_composition, i) for i in range(10)]
        results = [f.result() for f in futures]
        
    assert all(r.get("composition_id") for r in results)
```

---

## 14. Project File Structure

```
track3-ffmpeg-backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app initialization
│   ├── config.py                    # Configuration management
│   ├── dependencies.py              # Dependency injection
│   └── exceptions.py                # Custom exception classes
│
├── api/
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── compositions.py     # Composition endpoints
│   │   │   ├── health.py           # Health check endpoints
│   │   │   └── websocket.py        # WebSocket endpoints
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── composition.py      # Pydantic models for compositions
│   │   │   ├── common.py           # Shared schemas
│   │   │   └── errors.py           # Error response schemas
│   │   └── validators/
│   │       ├── __init__.py
│   │       ├── timeline.py         # Timeline validation
│   │       └── media.py            # Media file validation
│   │
│   ├── internal/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   └── processing.py   # Internal processing endpoints
│   │   │   └── schemas/
│   │   │       ├── __init__.py
│   │   │       └── processing.py   # Internal API schemas
│   │
│   └── dev/
│       ├── __init__.py
│       └── routers/
│           ├── __init__.py
│           └── test.py              # Development/test endpoints
│
├── core/
│   ├── __init__.py
│   ├── logging.py                  # Logging configuration
│   ├── metrics.py                  # Metrics collection
│   ├── feature_flags.py            # Feature flag management
│   └── security.py                 # Security utilities
│
├── services/
│   ├── __init__.py
│   ├── ffmpeg/
│   │   ├── __init__.py
│   │   ├── builder.py              # FFmpeg command builder
│   │   ├── executor.py             # FFmpeg process execution
│   │   ├── filters.py              # Filter complex builders
│   │   ├── transitions.py          # Transition effects
│   │   ├── overlays.py             # Text/image overlays
│   │   └── audio.py                # Audio processing
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── s3.py                   # S3 operations
│   │   ├── temp.py                 # Temp file management
│   │   └── cleanup.py              # File cleanup service
│   │
│   ├── queue/
│   │   ├── __init__.py
│   │   ├── redis_client.py         # Redis connection management
│   │   ├── publisher.py            # Progress publishing
│   │   └── subscriber.py           # WebSocket subscription
│   │
│   └── validation/
│       ├── __init__.py
│       ├── ffprobe.py              # FFprobe validation
│       └── media.py                # Media file validation
│
├── workers/
│   ├── __init__.py
│   ├── main.py                     # RQ worker entry point
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── composition.py          # Composition job handler
│   │   ├── processing.py           # Clip processing handler
│   │   └── cleanup.py              # Cleanup job handler
│   │
│   └── tasks/
│       ├── __init__.py
│       ├── download.py             # Asset download tasks
│       ├── encode.py               # Encoding tasks
│       ├── upload.py               # Upload tasks
│       └── notify.py               # Notification tasks
│
├── models/
│   ├── __init__.py
│   ├── base.py                     # Base SQLAlchemy model
│   ├── composition.py              # Composition model
│   ├── job.py                      # Job model
│   └── metrics.py                  # Metrics model
│
├── db/
│   ├── __init__.py
│   ├── session.py                  # Database session management
│   ├── migrations/
│   │   ├── alembic.ini
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   │
│   └── seeds/
│       ├── __init__.py
│       └── development.py          # Development seed data
│
├── utils/
│   ├── __init__.py
│   ├── time.py                     # Time utilities
│   ├── files.py                    # File utilities
│   ├── subprocess.py               # Subprocess utilities
│   └── progress.py                 # Progress calculation
│
├── middleware/
│   ├── __init__.py
│   ├── request_id.py               # Request ID middleware
│   ├── error_handler.py            # Global error handler
│   └── rate_limit.py               # Rate limiting
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest configuration
│   ├── fixtures/
│   │   ├── __init__.py
│   │   ├── media/                  # Test media files
│   │   │   ├── clip1.mp4
│   │   │   ├── clip2.mp4
│   │   │   └── music.mp3
│   │   └── data.py                 # Test data fixtures
│   │
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_ffmpeg_builder.py
│   │   ├── test_validators.py
│   │   ├── test_transitions.py
│   │   └── test_overlays.py
│   │
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_composition_flow.py
│   │   ├── test_websocket.py
│   │   └── test_worker_jobs.py
│   │
│   └── e2e/
│       ├── __init__.py
│       └── test_full_pipeline.py
│
├── scripts/
│   ├── start_api.sh                # Start API server
│   ├── start_worker.sh             # Start RQ workers
│   ├── run_migrations.sh           # Run database migrations
│   ├── seed_db.sh                  # Seed development data
│   └── cleanup_temp.sh             # Manual temp cleanup
│
├── docker/
│   ├── Dockerfile                  # Production Dockerfile
│   ├── Dockerfile.dev              # Development Dockerfile
│   ├── docker-compose.yml          # Local development setup
│   └── docker-compose.test.yml     # Test environment
│
├── configs/
│   ├── development.env             # Development environment
│   ├── test.env                    # Test environment
│   └── production.env.example      # Production env template
│
├── docs/
│   ├── API.md                      # API documentation
│   ├── SETUP.md                    # Setup instructions
│   ├── DEVELOPMENT.md              # Development guide
│   ├── FFMPEG_RECIPES.md           # FFmpeg command recipes
│   └── TROUBLESHOOTING.md          # Common issues
│
├── .github/
│   └── workflows/
│       ├── test.yml                # CI test workflow
│       └── lint.yml                # Linting workflow
│
├── requirements/
│   ├── base.txt                    # Base requirements
│   ├── development.txt             # Dev requirements
│   └── production.txt              # Production requirements
│
├── .env.example                    # Environment variable template
├── .gitignore
├── .dockerignore
├── .pre-commit-config.yaml         # Pre-commit hooks
├── pyproject.toml                  # Python project config
├── pytest.ini                      # Pytest configuration
├── Makefile                        # Common commands
└── README.md                       # Project documentation
```

### Key Files Explained

#### `app/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.routers import compositions, health, websocket
from api.internal.v1.routers import processing
from api.dev.routers import test
from core.logging import setup_logging
from core.feature_flags import features
from middleware.request_id import RequestIDMiddleware
from middleware.error_handler import ErrorHandlerMiddleware

app = FastAPI(
    title="Track 3 - FFmpeg Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup
setup_logging()

# Middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(compositions.router, prefix="/api/v1/compositions", tags=["compositions"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
app.include_router(processing.router, prefix="/internal/v1", tags=["internal"])

if features.is_enabled('dev_api'):
    app.include_router(test.router, prefix="/dev", tags=["development"])
```

#### `docker-compose.yml`
```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://postgres:password@db:5432/videogen
    depends_on:
      - redis
      - db
    volumes:
      - ./:/app
      - /tmp/videogen:/tmp/videogen
    command: uvicorn app.main:app --host 0.0.0.0 --reload

  worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.dev
    environment:
      - ENVIRONMENT=development
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://postgres:password@db:5432/videogen
    depends_on:
      - redis
      - db
    volumes:
      - ./:/app
      - /tmp/videogen:/tmp/videogen
    command: python -m workers.main

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  db:
    image: postgres:17-alpine
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=videogen
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

#### `Makefile`
```makefile
.PHONY: help dev test lint clean

help:
	@echo "Available commands:"
	@echo "  make dev       - Start development environment"
	@echo "  make test      - Run tests"
	@echo "  make lint      - Run linting"
	@echo "  make clean     - Clean temporary files"
	@echo "  make migrate   - Run database migrations"
	@echo "  make worker    - Start worker only"

dev:
	docker-compose -f docker/docker-compose.yml up

test:
	docker-compose -f docker/docker-compose.test.yml run --rm api pytest

lint:
	black . --check
	flake8 .
	mypy .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf /tmp/videogen/*

migrate:
	docker-compose -f docker/docker-compose.yml run --rm api alembic upgrade head

worker:
	python -m workers.main
```

---

## 15. Local Development Setup

### 15.1 Quick Start
```bash
# Clone repository
git clone <repository-url>
cd track3-ffmpeg-backend

# Copy environment variables
cp .env.example .env

# Start services
make dev

# Run migrations
make migrate

# Access API documentation
open http://localhost:8000/docs
```

### 15.2 Development Workflow
```bash
# Run tests
make test

# Start worker only (for debugging)
make worker

# Clean temporary files
make clean

# Format code
black .

# Type checking
mypy .
```

---

## 16. Security Considerations

### 16.1 Input Validation
- Sanitize all text overlay content
- Validate S3 URLs against whitelist
- Limit composition duration (max 3 minutes for MVP)
- Validate video codecs and formats
- Rate limiting per user/IP

### 16.2 Infrastructure Security
- Environment-based configuration
- S3 presigned URLs with expiration (1 hour)
- Secrets in environment variables (use secrets manager in production)
- Database connections with SSL
- Network isolation where possible

### 16.3 FFmpeg Security
- Use static binary (no system dependencies)
- Disable network protocols in FFmpeg
- Resource limits (CPU, memory, time)
- Input file size limits
- Sandboxed execution environment

---

## 17. Performance Optimization

### 17.1 MVP Targets
- 5 concurrent compositions
- 45-second average processing time for 30-second video
- 720p output at 30fps
- CRF 21 for quality/size balance

### 17.2 Optimization Strategies
- Reuse normalized clips when possible
- Parallel download of assets
- Stream processing where feasible
- Efficient temp file management
- Redis connection pooling

### 17.3 Post-MVP Enhancements
- GPU acceleration with NVENC
- Distributed encoding
- CDN for popular assets
- Predictive scaling
- Advanced caching strategies

---

## 18. Acceptance Criteria

### 18.1 Functional Requirements
✓ All API endpoints operational and documented in Swagger  
✓ End-to-end composition workflow functional  
✓ WebSocket real-time updates working  
✓ Error handling with proper status codes  
✓ S3 integration for storage  
✓ RQ worker processing  
✓ PostgreSQL persistence  

### 18.2 Performance Requirements
✓ Handle 5 concurrent jobs  
✓ < 2x real-time processing for 720p  
✓ < 5 second API response times  
✓ 99% uptime for health endpoints  

### 18.3 Quality Requirements
✓ Unit test coverage > 80%  
✓ Integration tests passing  
✓ No memory leaks in workers  
✓ Proper cleanup of temp files  
✓ Structured JSON logging  
✓ Metrics reporting  

---

## 19. Appendix

### A. Sample FFmpeg Commands

**Crossfade between clips:**
```bash
ffmpeg -i clip1.mp4 -i clip2.mp4 \
  -filter_complex \
  "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=3[outv]" \
  -map "[outv]" output.mp4
```

**Text overlay with animation:**
```bash
ffmpeg -i input.mp4 \
  -vf "drawtext=text='Summer Sale':x='if(lt(t,2),w-t*w/2,(w-text_w)/2)':y=h-50:fontsize=40:fontcolor=white@0.8:shadowx=2:shadowy=2" \
  output.mp4
```

**Audio mixing with ducking:**
```bash
ffmpeg -i video.mp4 -i music.mp3 -i voiceover.mp3 \
  -filter_complex \
  "[1:a]volume=0.3[music];[2:a]volume=1.0[vo];[music][vo]amix=inputs=2:duration=shortest[aout]" \
  -map 0:v -map "[aout]" \
  -c:v copy -c:a aac -b:a 192k \
  output.mp4
```

### B. Sample Implementation Files

**services/ffmpeg/builder.py**
```python
class FFmpegCommandBuilder:
    def __init__(self):
        self.inputs = []
        self.filters = []
        self.outputs = []
        self.global_options = []
        
    def add_input(self, filepath: str, options: dict = None):
        if options:
            for key, value in options.items():
                self.inputs.append(f"-{key} {value}")
        self.inputs.append(f"-i {filepath}")
        return self
    
    def add_filter(self, filter_string: str):
        self.filters.append(filter_string)
        return self
    
    def add_text_overlay(self, text: str, x: str = "center", y: int = 50):
        if x == "center":
            x = "(w-text_w)/2"
        filter_str = f"drawtext=text='{text}':x={x}:y={y}:fontsize=40:fontcolor=white"
        self.filters.append(filter_str)
        return self
    
    def build(self) -> list:
        cmd = ["ffmpeg"]
        cmd.extend(self.global_options)
        cmd.extend(self.inputs)
        if self.filters:
            cmd.extend(["-filter_complex", ";".join(self.filters)])
        cmd.extend(self.outputs)
        return cmd
```

### C. Useful Resources
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [RQ Documentation](https://python-rq.org/)
- [Redis Pub/Sub Guide](https://redis.io/docs/manual/pubsub/)

---

## Document Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 2.1 | 2024-11-14 | Removed AWS deployment/monitoring, added comprehensive file structure | Team |
| 2.0 | 2024-11-14 | Complete technical specification with all decisions finalized | Team |
| 1.0 | 2024-11-01 | Initial PRD | Team |

---

# End of Document