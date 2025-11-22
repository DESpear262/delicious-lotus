# API Reference

Complete API reference for the FFmpeg Backend Service.

## Base URL

```
Production: https://api.delicious-lotus.com
Staging: https://staging-api.delicious-lotus.com
Development: http://localhost:8000
```

## Authentication

### Public API (v1)

Public API endpoints use rate limiting based on IP address:
- **Rate Limit**: 60 requests per minute per IP
- **Headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

### Internal API

Internal API endpoints require API key authentication:

```bash
# Header-based authentication
X-API-Key: your-api-key-here
```

**Rate Limit**: 1000 requests per minute per API key

## Response Format

### Success Response

```json
{
  "composition_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Error Response

```json
{
  "detail": {
    "error_code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "fields": {
      "clips": ["At least one clip is required"]
    },
    "request_id": "req_123456",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## Endpoints

### Health & Status

#### GET /api/v1/health

Check service health status.

**Response** `200 OK`:
```json
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

#### GET /api/v1/health/detailed

Get detailed health information including resource metrics.

**Response** `200 OK`:
```json
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
  },
  "system": {
    "cpu_percent": 45.2,
    "memory_percent": 62.8,
    "disk_usage_percent": 34.1
  }
}
```

### Compositions

#### POST /api/v1/compositions

Create a new video composition.

**Request Body**:
```json
{
  "title": "My Video",
  "clips": [
    {
      "video_url": "https://example.com/clip1.mp4",
      "start_time": 0.0,
      "end_time": 10.0,
      "trim_start": 0.0,
      "trim_end": null
    }
  ],
  "audio": {
    "music_url": "https://example.com/music.mp3",
    "voiceover_url": null,
    "music_volume": 0.3,
    "voiceover_volume": 0.7,
    "original_audio_volume": 0.5
  },
  "overlays": [
    {
      "text": "Hello World",
      "position": "center",
      "start_time": 0.0,
      "end_time": 3.0,
      "font_size": 48,
      "font_color": "#FFFFFF"
    }
  ],
  "output": {
    "resolution": "1080p",
    "format": "mp4",
    "fps": 30,
    "quality": "high"
  }
}
```

**Field Specifications**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Composition title (max 200 chars) |
| `clips` | array | Yes | Array of video clips (min 1, max 50) |
| `clips[].video_url` | string (URL) | Yes | URL to video file |
| `clips[].start_time` | float | Yes | Start time in final video (seconds) |
| `clips[].end_time` | float | Yes | End time in final video (seconds) |
| `clips[].trim_start` | float | No | Trim from clip start (seconds) |
| `clips[].trim_end` | float | No | Trim from clip end (seconds) |
| `audio` | object | Yes | Audio configuration |
| `audio.music_url` | string (URL) | No | Background music URL |
| `audio.voiceover_url` | string (URL) | No | Voiceover audio URL |
| `audio.music_volume` | float | Yes | Music volume (0.0-1.0) |
| `audio.voiceover_volume` | float | Yes | Voiceover volume (0.0-1.0) |
| `audio.original_audio_volume` | float | Yes | Original clip audio volume (0.0-1.0) |
| `overlays` | array | No | Text overlays (max 10) |
| `overlays[].text` | string | Yes | Overlay text (max 500 chars) |
| `overlays[].position` | string | Yes | Position: `top-left`, `top-center`, `top-right`, `center`, `bottom-left`, `bottom-center`, `bottom-right` |
| `overlays[].start_time` | float | Yes | Start time (seconds) |
| `overlays[].end_time` | float | Yes | End time (seconds) |
| `overlays[].font_size` | integer | Yes | Font size (12-144) |
| `overlays[].font_color` | string | Yes | Hex color code (e.g., `#FFFFFF`) |
| `output` | object | Yes | Output configuration |
| `output.resolution` | string | Yes | Resolution: `720p`, `1080p`, `4k` |
| `output.format` | string | Yes | Format: `mp4`, `mov`, `webm` |
| `output.fps` | integer | Yes | Frame rate: 24, 30, 60 |
| `output.quality` | string | Yes | Quality: `low`, `medium`, `high` |

**Response** `202 Accepted`:
```json
{
  "composition_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "title": "My Video",
  "created_at": "2024-01-15T10:30:00Z",
  "job_id": "rq:job:123e4567-e89b-12d3-a456-426614174000"
}
```

**Error Responses**:
- `400 Bad Request`: Validation error
- `422 Unprocessable Entity`: Invalid field values
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

#### GET /api/v1/compositions

List compositions with optional filtering.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | all | Filter by status: `pending`, `queued`, `processing`, `completed`, `failed` |
| `limit` | integer | 50 | Results per page (max 100) |
| `offset` | integer | 0 | Pagination offset |
| `sort` | string | created_at | Sort field: `created_at`, `updated_at`, `title` |
| `order` | string | desc | Sort order: `asc`, `desc` |

**Example**:
```bash
GET /api/v1/compositions?status=completed&limit=20&offset=0&sort=created_at&order=desc
```

**Response** `200 OK`:
```json
{
  "compositions": [
    {
      "composition_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "My Video",
      "status": "completed",
      "created_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:35:00Z",
      "duration": 300.5
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

#### GET /api/v1/compositions/{composition_id}

Get composition details and status.

**Path Parameters**:
- `composition_id` (UUID): Composition ID

**Response** `200 OK`:
```json
{
  "composition_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "My Video",
  "status": "processing",
  "progress": 45,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:32:30Z",
  "config": {
    "clips": [...],
    "audio": {...},
    "overlays": [...],
    "output": {...}
  },
  "metadata": {
    "input_files": [
      {
        "url": "https://example.com/clip1.mp4",
        "size": 15728640,
        "duration": 10.5,
        "resolution": "1920x1080"
      }
    ],
    "output_file": null,
    "estimated_duration": 20.0
  },
  "resource_usage": {
    "processing_time_seconds": 120,
    "cpu_time_seconds": 480,
    "memory_peak_mb": 1024
  }
}
```

**Error Responses**:
- `404 Not Found`: Composition not found

#### GET /api/v1/compositions/{composition_id}/download

Get download URL for completed composition.

**Response** `200 OK`:
```json
{
  "composition_id": "550e8400-e29b-41d4-a716-446655440000",
  "download_url": "https://s3.amazonaws.com/bucket/outputs/...",
  "file_size": 52428800,
  "duration": 20.5,
  "resolution": "1920x1080",
  "format": "mp4",
  "expires_at": "2024-01-15T18:30:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Composition not found
- `409 Conflict`: Composition not yet completed

#### GET /api/v1/compositions/{composition_id}/metadata

Get detailed composition metadata.

**Response** `200 OK`:
```json
{
  "composition_id": "550e8400-e29b-41d4-a716-446655440000",
  "input_files": [
    {
      "url": "https://example.com/clip1.mp4",
      "size": 15728640,
      "duration": 10.5,
      "resolution": "1920x1080",
      "codec": "h264",
      "bitrate": 12000000
    }
  ],
  "output_file": {
    "url": "https://s3.amazonaws.com/bucket/outputs/...",
    "size": 52428800,
    "duration": 20.5,
    "resolution": "1920x1080",
    "codec": "h264",
    "bitrate": 20000000,
    "fps": 30
  },
  "processing_stats": {
    "start_time": "2024-01-15T10:30:15Z",
    "end_time": "2024-01-15T10:35:45Z",
    "duration_seconds": 330,
    "ffmpeg_version": "7.0.2"
  }
}
```

#### DELETE /api/v1/compositions/{composition_id}

Delete a composition and its associated resources.

**Response** `204 No Content`

**Error Responses**:
- `404 Not Found`: Composition not found
- `409 Conflict`: Composition currently processing

### WebSocket

#### WS /api/v1/ws/compositions/{composition_id}

Subscribe to real-time composition updates.

**Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/compositions/550e8400-e29b-41d4-a716-446655440000');
```

**Message Types**:

**Progress Update**:
```json
{
  "type": "progress",
  "composition_id": "550e8400-e29b-41d4-a716-446655440000",
  "progress": 45,
  "stage": "encoding",
  "timestamp": "2024-01-15T10:32:30Z"
}
```

**Status Change**:
```json
{
  "type": "status",
  "composition_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "timestamp": "2024-01-15T10:35:00Z"
}
```

**Error Event**:
```json
{
  "type": "error",
  "composition_id": "550e8400-e29b-41d4-a716-446655440000",
  "error": "FFmpeg encoding failed",
  "error_code": "ENCODING_ERROR",
  "timestamp": "2024-01-15T10:33:00Z"
}
```

### Internal API

#### POST /internal/v1/process-clips

Process video clips with normalization and thumbnail generation.

**Authentication**: Required (`X-API-Key` header)

**Request Body**:
```json
{
  "clips": [
    {
      "clip_url": "https://example.com/clip1.mp4",
      "operations": ["normalize", "thumbnail"]
    }
  ],
  "callback_url": "https://ai-backend.example.com/callbacks/clips",
  "options": {
    "target_resolution": "1280x720",
    "target_codec": "h264",
    "thumbnail_timestamps": [1.0, 5.0, 10.0]
  }
}
```

**Response** `202 Accepted`:
```json
{
  "job_id": "internal_job_123e4567",
  "status": "queued",
  "clips": [
    {
      "clip_id": "clip_550e8400",
      "original_url": "https://example.com/clip1.mp4",
      "status": "queued"
    }
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Callback Payload** (sent to `callback_url` when complete):
```json
{
  "job_id": "internal_job_123e4567",
  "status": "completed",
  "clips": [
    {
      "clip_id": "clip_550e8400",
      "original_url": "https://example.com/clip1.mp4",
      "processed_url": "https://s3.amazonaws.com/bucket/processed/...",
      "thumbnails": [
        "https://s3.amazonaws.com/bucket/thumbnails/clip_1.0.jpg",
        "https://s3.amazonaws.com/bucket/thumbnails/clip_5.0.jpg",
        "https://s3.amazonaws.com/bucket/thumbnails/clip_10.0.jpg"
      ],
      "metadata": {
        "duration": 15.5,
        "resolution": "1280x720",
        "codec": "h264",
        "file_size": 8388608
      }
    }
  ],
  "completed_at": "2024-01-15T10:32:00Z"
}
```

## Rate Limiting

### Headers

All responses include rate limit headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705318200
```

### Rate Limit Response

When rate limit is exceeded:

**Response** `429 Too Many Requests`:
```json
{
  "detail": {
    "error_code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please retry after 60 seconds.",
    "retry_after": 60,
    "request_id": "req_123456"
  }
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |
| `ENCODING_ERROR` | 500 | FFmpeg encoding failed |
| `DOWNLOAD_ERROR` | 500 | Failed to download input file |
| `UPLOAD_ERROR` | 500 | Failed to upload output file |

## Pagination

Endpoints that return lists support pagination:

```
GET /api/v1/compositions?limit=50&offset=0
```

**Response includes pagination metadata**:
```json
{
  "compositions": [...],
  "total": 150,
  "limit": 50,
  "offset": 0,
  "has_more": true
}
```

## Versioning

API version is included in the URL path:
- **Current version**: `/api/v1/`
- **Internal API**: `/internal/v1/`

Breaking changes will result in a new version (e.g., `/api/v2/`).
