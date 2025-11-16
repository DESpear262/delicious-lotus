# API Specification
## AI Video Generation Pipeline - Inter-Service Communication

### Overview

This document defines all API contracts between the four development tracks to enable parallel development without blocking dependencies. All teams must adhere to these specifications to ensure seamless integration.

### Architecture Overview

```
┌─────────────────┐
│   Web Frontend  │
│   (React/Vite)  │
└────────┬────────┘
         │ REST + WebSocket
         ▼
┌─────────────────────────────────────┐
│         API Gateway Layer           │
│         (FastAPI Router)            │
└──────┬──────────────────┬───────────┘
       │                  │
       ▼                  ▼
┌──────────────┐   ┌──────────────┐
│  AI Backend  │   │FFmpeg Backend│
│  (Replicate) │◄─►│   (Video)    │
└──────────────┘   └──────────────┘
       │                  │
       └──────┬───────────┘
              ▼
       ┌──────────────┐
       │  PostgreSQL  │
       │    Redis     │
       └──────────────┘
```

### Base Configuration

#### API Version
All endpoints are versioned under `/api/v1/` for public APIs and `/internal/v1/` for inter-service communication.

#### Common Headers
```
Content-Type: application/json
X-Request-ID: <uuid>
X-Client-Version: <version>
```

#### Authentication
MVP uses session-based authentication with secure cookies. No JWT in Phase 1.

#### Error Response Format
All errors follow this structure:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {},
    "timestamp": "2025-11-14T10:00:00Z",
    "request_id": "uuid"
  }
}
```

### Section A: Frontend ↔ AI Backend APIs

#### 1. Submit Generation Request
**POST** `/api/v1/generations`

Creates a new video generation job.

**Request Body:**
```json
{
  "prompt": "Create a 30-second ad for a luxury watch...",
  "parameters": {
    "duration_seconds": 30,
    "aspect_ratio": "16:9",
    "style": "professional",
    "brand": {
      "name": "ChronoLux",
      "colors": ["#1a1a1a", "#d4af37"],
      "logo_url": "https://..."
    },
    "include_cta": true,
    "cta_text": "Shop Now",
    "music_style": "corporate"
  },
  "options": {
    "quality": "high",
    "fast_generation": false
  }
}
```

**Response (201 Created):**
```json
{
  "generation_id": "gen_abc123xyz",
  "status": "queued",
  "created_at": "2025-11-14T10:00:00Z",
  "estimated_completion": "2025-11-14T10:05:00Z",
  "websocket_url": "/ws/generations/gen_abc123xyz"
}
```

**Validation Rules:**
- `prompt`: 50-2000 characters
- `duration_seconds`: 15, 30, 45, or 60
- `aspect_ratio`: "16:9", "9:16", or "1:1"
- `style`: enum of predefined styles

#### 2. Get Generation Status
**GET** `/api/v1/generations/{generation_id}`

Retrieves current status and metadata for a generation job.

**Response (200 OK):**
```json
{
  "generation_id": "gen_abc123xyz",
  "status": "processing",
  "progress": {
    "current_step": "generating_clips",
    "steps_completed": 3,
    "total_steps": 8,
    "percentage": 37.5,
    "current_clip": 2,
    "total_clips": 5
  },
  "metadata": {
    "prompt": "...",
    "parameters": {},
    "created_at": "2025-11-14T10:00:00Z",
    "updated_at": "2025-11-14T10:02:30Z"
  },
  "clips_generated": [
    {
      "clip_id": "clip_001",
      "thumbnail_url": "https://...",
      "duration": 6.0,
      "status": "completed"
    }
  ]
}
```

**Status Enum:**
- `queued`: Job created, waiting to start
- `processing`: Actively generating
- `composing`: Clips done, creating final video
- `completed`: Success, video ready
- `failed`: Generation failed
- `cancelled`: User cancelled

#### 3. List User Generations
**GET** `/api/v1/generations`

Returns paginated list of user's generation jobs.

**Query Parameters:**
- `page`: integer (default: 1)
- `limit`: integer (default: 20, max: 100)
- `status`: filter by status
- `sort`: "created_at" | "-created_at"

**Response (200 OK):**
```json
{
  "generations": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "pages": 3
  }
}
```

#### 4. Cancel Generation
**POST** `/api/v1/generations/{generation_id}/cancel`

Cancels an in-progress generation.

**Response (200 OK):**
```json
{
  "generation_id": "gen_abc123xyz",
  "status": "cancelled",
  "message": "Generation cancelled successfully"
}
```

#### 5. Get Generated Assets
**GET** `/api/v1/generations/{generation_id}/assets`

Retrieves URLs for all generated clips and metadata.

**Response (200 OK):**
```json
{
  "generation_id": "gen_abc123xyz",
  "assets": {
    "clips": [
      {
        "clip_id": "clip_001",
        "url": "https://...",
        "duration": 6.0,
        "format": "mp4",
        "resolution": "1920x1080",
        "thumbnail": "https://..."
      }
    ],
    "audio": {
      "url": "https://...",
      "duration": 30.0,
      "format": "mp3"
    },
    "metadata": {
      "scene_descriptions": [...],
      "style_parameters": {...}
    }
  }
}
```

### Section B: Frontend ↔ FFmpeg Backend APIs

#### 1. Request Video Composition
**POST** `/api/v1/compositions`

Initiates final video composition from generated clips.

**Request Body:**
```json
{
  "generation_id": "gen_abc123xyz",
  "clips": [
    {
      "clip_id": "clip_001",
      "url": "https://...",
      "start_time": 0,
      "end_time": 6,
      "transition_in": "fade",
      "transition_out": "cut"
    }
  ],
  "audio": {
    "url": "https://...",
    "volume": 0.8,
    "fade_in": 1.0,
    "fade_out": 2.0
  },
  "overlays": [
    {
      "type": "text",
      "content": "Shop Now",
      "position": {"x": 0.5, "y": 0.8},
      "start_time": 25,
      "duration": 5,
      "style": {
        "font": "Arial",
        "size": 48,
        "color": "#ffffff"
      }
    }
  ],
  "output": {
    "format": "mp4",
    "resolution": "1920x1080",
    "fps": 30,
    "codec": "h264",
    "quality": "high"
  }
}
```

**Response (201 Created):**
```json
{
  "composition_id": "comp_xyz789",
  "status": "queued",
  "estimated_duration": 120,
  "websocket_url": "/ws/compositions/comp_xyz789"
}
```

#### 2. Get Composition Status
**GET** `/api/v1/compositions/{composition_id}`

**Response (200 OK):**
```json
{
  "composition_id": "comp_xyz789",
  "status": "encoding",
  "progress": {
    "percentage": 75,
    "frames_processed": 675,
    "total_frames": 900,
    "current_pass": 1,
    "total_passes": 1
  },
  "output": {
    "url": null,
    "size_bytes": null,
    "duration": 30.0
  }
}
```

#### 3. Download Final Video
**GET** `/api/v1/compositions/{composition_id}/download`

Returns the final composed video file.

**Response (200 OK):**
- Binary video file with appropriate headers
- `Content-Type: video/mp4`
- `Content-Disposition: attachment; filename="video_comp_xyz789.mp4"`

#### 4. Get Composition Metadata
**GET** `/api/v1/compositions/{composition_id}/metadata`

**Response (200 OK):**
```json
{
  "composition_id": "comp_xyz789",
  "file_info": {
    "size_bytes": 15728640,
    "duration_seconds": 30.0,
    "resolution": "1920x1080",
    "fps": 30,
    "codec": "h264",
    "bitrate": "4Mbps"
  },
  "timeline": [...],
  "processing_stats": {
    "start_time": "2025-11-14T10:05:00Z",
    "end_time": "2025-11-14T10:07:00Z",
    "total_seconds": 120
  }
}
```

### Section C: AI Backend ↔ FFmpeg Backend APIs

#### 1. Submit Clips for Processing
**POST** `/internal/v1/process-clips`

Internal API for AI backend to send generated clips to FFmpeg backend.

**Request Body:**
```json
{
  "job_id": "gen_abc123xyz",
  "clips": [
    {
      "clip_id": "clip_001",
      "source_url": "s3://bucket/clips/clip_001.mp4",
      "duration": 6.0,
      "metadata": {
        "scene_number": 1,
        "prompt": "Opening shot of luxury watch",
        "style_vector": [0.8, 0.2, 0.5]
      }
    }
  ],
  "instructions": {
    "target_duration": 30,
    "transitions": ["fade", "cut", "dissolve"],
    "color_correction": true,
    "stabilization": false
  },
  "callback_url": "http://ai-backend:8001/internal/v1/processing-complete"
}
```

**Response (202 Accepted):**
```json
{
  "processing_id": "proc_123",
  "status": "accepted",
  "estimated_completion": 60
}
```

#### 2. Get Processing Status
**GET** `/internal/v1/process-clips/{processing_id}`

**Response (200 OK):**
```json
{
  "processing_id": "proc_123",
  "status": "processing",
  "clips_processed": 3,
  "total_clips": 5,
  "current_operation": "color_matching"
}
```

#### 3. Processing Complete Callback
**POST** `/internal/v1/processing-complete`

FFmpeg backend calls this when processing is complete.

**Request Body:**
```json
{
  "job_id": "gen_abc123xyz",
  "processing_id": "proc_123",
  "status": "completed",
  "output": {
    "video_url": "s3://bucket/processed/gen_abc123xyz.mp4",
    "thumbnail_url": "s3://bucket/thumbnails/gen_abc123xyz.jpg",
    "metadata": {...}
  }
}
```

### Section D: WebSocket APIs

#### 1. Generation Progress WebSocket
**WebSocket** `/ws/generations/{generation_id}`

Real-time updates for generation progress.

**Client → Server:**
```json
{
  "type": "subscribe",
  "generation_id": "gen_abc123xyz"
}
```

**Server → Client Messages:**
```json
{
  "type": "progress",
  "data": {
    "step": "generating_clip",
    "clip_number": 2,
    "total_clips": 5,
    "percentage": 40,
    "message": "Generating scene 2: Product close-up"
  }
}
```

```json
{
  "type": "clip_completed",
  "data": {
    "clip_id": "clip_002",
    "thumbnail_url": "https://...",
    "duration": 6.0
  }
}
```

```json
{
  "type": "status_change",
  "data": {
    "old_status": "processing",
    "new_status": "composing",
    "message": "All clips generated, starting composition"
  }
}
```

```json
{
  "type": "completed",
  "data": {
    "video_url": "https://...",
    "thumbnail_url": "https://...",
    "duration": 30.0
  }
}
```

```json
{
  "type": "error",
  "data": {
    "code": "GENERATION_FAILED",
    "message": "Failed to generate clip 3",
    "recoverable": true
  }
}
```

#### 2. Composition Progress WebSocket
**WebSocket** `/ws/compositions/{composition_id}`

Real-time updates for video composition.

**Server → Client Messages:**
```json
{
  "type": "encoding_progress",
  "data": {
    "percentage": 45,
    "frames_processed": 405,
    "total_frames": 900,
    "estimated_remaining": 55
  }
}
```

### Section E: Shared Data Models

#### PostgreSQL Schema

```sql
-- Generation jobs table
CREATE TABLE generations (
    id VARCHAR(32) PRIMARY KEY,
    user_id VARCHAR(32),
    prompt TEXT NOT NULL,
    parameters JSONB NOT NULL,
    status VARCHAR(20) NOT NULL,
    progress JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    error_message TEXT,
    cost_cents INTEGER
);

CREATE INDEX idx_generations_user_id ON generations(user_id);
CREATE INDEX idx_generations_status ON generations(status);
CREATE INDEX idx_generations_created_at ON generations(created_at DESC);

-- Generated clips table
CREATE TABLE clips (
    id VARCHAR(32) PRIMARY KEY,
    generation_id VARCHAR(32) REFERENCES generations(id),
    clip_number INTEGER NOT NULL,
    url TEXT NOT NULL,
    thumbnail_url TEXT,
    duration DECIMAL(5,2),
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(generation_id, clip_number)
);

CREATE INDEX idx_clips_generation_id ON clips(generation_id);

-- Compositions table
CREATE TABLE compositions (
    id VARCHAR(32) PRIMARY KEY,
    generation_id VARCHAR(32) REFERENCES generations(id),
    status VARCHAR(20) NOT NULL,
    input_config JSONB NOT NULL,
    output_url TEXT,
    output_metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX idx_compositions_generation_id ON compositions(generation_id);

-- Status enum type
CREATE TYPE generation_status AS ENUM (
    'queued', 'processing', 'composing',
    'completed', 'failed', 'cancelled'
);

CREATE TYPE composition_status AS ENUM (
    'queued', 'encoding', 'completed', 'failed'
);

-- Aspect ratio enum
CREATE TYPE aspect_ratio AS ENUM ('16:9', '9:16', '1:1');
```

#### Redis Queue Structures

```python
# Job Queue Keys
generation_queue = "queue:generation:pending"      # List of generation IDs
composition_queue = "queue:composition:pending"    # List of composition IDs
priority_queue = "queue:generation:priority"       # Priority generations

# Status Keys (with TTL)
generation_status = "status:generation:{id}"       # Hash of current status
composition_status = "status:composition:{id}"     # Hash of current status

# Progress Keys (with TTL)
generation_progress = "progress:generation:{id}"   # Current progress JSON

# Lock Keys (for distributed processing)
generation_lock = "lock:generation:{id}"           # Processing lock
composition_lock = "lock:composition:{id}"         # Processing lock

# Cache Keys
model_cache = "cache:model:{model_id}"            # Cached model responses
style_cache = "cache:style:{style_hash}"          # Style consistency cache
```

#### File Storage Conventions

```
/storage/
├── uploads/
│   └── {user_id}/
│       └── {upload_id}/
│           └── original.{ext}
├── generations/
│   └── {generation_id}/
│       ├── clips/
│       │   ├── clip_001.mp4
│       │   └── clip_002.mp4
│       ├── audio/
│       │   └── background.mp3
│       └── metadata.json
├── compositions/
│   └── {composition_id}/
│       ├── final.mp4
│       ├── thumbnail.jpg
│       └── timeline.json
└── temp/
    └── {job_id}/
        └── processing/
```

### Section F: Error Codes

#### Client Errors (4xx)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| INVALID_PROMPT | 400 | Prompt validation failed |
| INVALID_PARAMETERS | 400 | Invalid generation parameters |
| GENERATION_NOT_FOUND | 404 | Generation ID doesn't exist |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| INSUFFICIENT_CREDITS | 402 | User has no credits (future) |

#### Server Errors (5xx)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| REPLICATE_API_ERROR | 502 | Replicate API failure |
| PROCESSING_FAILED | 500 | Video processing error |
| DATABASE_ERROR | 500 | Database operation failed |
| STORAGE_ERROR | 500 | S3/storage failure |
| QUEUE_ERROR | 500 | Redis queue error |

### Section G: Rate Limiting

#### Limits (MVP)
- Generation requests: 10 per hour per user
- Status queries: 60 per minute per user
- WebSocket connections: 5 concurrent per user
- File uploads: 5 per hour per user

#### Response Headers
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1731579600
```

### Section H: Health Check Endpoints

#### Service Health
**GET** `/health`

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-14T10:00:00Z"
}
```

#### Detailed Health
**GET** `/health/detailed`

**Response (200 OK):**
```json
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "redis": "connected",
    "replicate": "available",
    "storage": "accessible"
  },
  "metrics": {
    "active_generations": 3,
    "queue_depth": 12,
    "average_generation_time": 245
  }
}
```

### Section I: Development & Testing

#### Local Development Endpoints

**POST** `/dev/test-generation`
- Bypasses Replicate, uses mock data
- Instant response for UI development

**GET** `/dev/reset-user`
- Clears user data for testing
- Development environment only

#### Environment Variables

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1

# Service URLs
AI_BACKEND_URL=http://ai-backend:8001
FFMPEG_BACKEND_URL=http://ffmpeg-backend:8002

# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/videogen
REDIS_URL=redis://redis:6379/0

# External APIs
REPLICATE_API_TOKEN=r8_xxx
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=xxx

# Feature Flags
ENABLE_MOCK_MODE=false
ENABLE_DEBUG_ENDPOINTS=false
MAX_CONCURRENT_JOBS=5
```

### Section J: Integration Guidelines

#### 1. Request ID Tracking
All requests must include `X-Request-ID` header for tracing across services.

#### 2. Timeout Configuration
- REST API calls: 30 second timeout
- WebSocket idle: 5 minute timeout
- Long polling fallback: 60 second timeout

#### 3. Retry Strategy
- Use exponential backoff: 1s, 2s, 4s, 8s
- Max 3 retries for transient failures
- Circuit breaker after 5 consecutive failures

#### 4. Content Negotiation
- Default: `application/json`
- Video: `video/mp4`
- Images: `image/jpeg`, `image/png`

#### 5. CORS Configuration
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, X-Request-ID
```

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-14 | Initial specification |

### Contact

For API questions or clarifications during development:
- Create an issue in the GitHub repository
- Tag with `api-spec` label
- Include the endpoint and use case