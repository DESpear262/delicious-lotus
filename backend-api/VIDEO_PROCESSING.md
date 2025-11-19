# Video Processing System Documentation

## Overview

The video processing system automatically downloads AI-generated videos from temporary URLs (e.g., Replicate CDN), uploads them to permanent S3 storage, extracts video metadata, and generates thumbnails. All processing happens asynchronously in background workers to avoid blocking API requests.

## Architecture

```
┌─────────────────┐
│   Replicate     │
│  Video Generation│
└────────┬────────┘
         │ Webhook
         ▼
┌─────────────────┐
│  FastAPI App    │
│  /webhook       │───┐
└─────────────────┘   │
                      │ Enqueue Job
                      ▼
              ┌──────────────┐
              │  Redis Queue │
              │  (RQ)        │
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │  RQ Worker   │
              │  (Background)│
              └──────┬───────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
    Download    Extract      Generate
    from URL    Metadata    Thumbnail
         │      (FFprobe)   (FFmpeg)
         ▼           │           │
    ┌────────────────┴───────────┘
    ▼
┌─────────────────┐
│  Upload to S3   │
│  (Video + Thumb)│
└────────┬────────┘
         ▼
┌─────────────────┐
│  Update DB      │
│  MediaAsset     │
└─────────────────┘
```

## Components

### 1. Video Processor (`workers/video_processor.py`)

Utilities for video processing using FFmpeg/FFprobe:

- **`extract_video_metadata(video_path)`**: Extracts technical metadata
  - Duration, dimensions (width/height)
  - Frame rate, codec, bitrate
  - Container format

- **`generate_thumbnail(video_path, output_path, timestamp=0.0, width=320)`**: Generates thumbnail
  - Extracts frame at specified timestamp (default: first frame)
  - Resizes to specified width maintaining aspect ratio
  - Outputs high-quality JPEG

- **`process_video_file(video_path, ...)`**: Convenience function
  - Combines metadata extraction and thumbnail generation
  - Returns both results in single call

### 2. Background Jobs (`workers/video_import_job.py`)

#### `import_video_from_url_job(url, name, user_id, asset_id, metadata)`

Complete video import pipeline:

1. **Download**: Downloads video from external URL with checksum calculation
2. **Process**: Extracts metadata and generates thumbnail (first frame at 320px)
3. **Upload**: Uploads both video and thumbnail to S3
4. **Database**: Updates MediaAsset record with all metadata
5. **Cleanup**: Removes temporary files

**Error Handling:**
- Sets MediaAsset status to FAILED on error
- Stores error message in metadata
- Cleans up temp files in all cases

#### `import_image_from_url_job(url, name, user_id, asset_id, metadata)`

Simplified image import (no processing needed):
- Downloads image
- Uploads to S3
- Updates database

### 3. Job Queue Manager (`workers/job_queue.py`)

Redis Queue (RQ) wrapper for job management:

- **`enqueue_video_import(...)`**: Enqueues video import job
  - Queue: `media_import`
  - Timeout: 30 minutes
  - Returns: Job ID for tracking

- **`enqueue_image_import(...)`**: Enqueues image import job
  - Queue: `media_import`
  - Timeout: 10 minutes
  - Returns: Job ID for tracking

- **`get_job_status(job_id)`**: Gets job status
  - Returns: `{status, result, error, progress}`
  - Status: "queued", "started", "finished", "failed", "canceled", "not_found"

- **`cancel_job(job_id)`**: Cancels a job

### 4. Replicate Webhook Handler (`api/v1/replicate.py`)

Receives webhooks when AI generation completes:

1. **Parse webhook**: Extracts result URL and status
2. **Publish to Redis**: Notifies WebSocket clients
3. **Enqueue import**: Automatically enqueues video/image import job
4. **Update metadata**: Stores asset_id and import_job_id in Redis

**Flow:**
```
Replicate webhook → Extract URL → Enqueue import job → Return 200 OK
                                    (async processing)
```

### 5. Import Endpoint (`api/v1/media.py`)

**POST `/api/v1/media/import-from-url`**

Import media from external URL:

- **For Videos**:
  - Creates placeholder MediaAsset (status: UPLOADING)
  - Enqueues background job
  - Returns immediately with job_id
  - Processing happens asynchronously

- **For Images**:
  - Synchronous processing (no video processing needed)
  - Returns complete MediaAsset immediately

**Request:**
```json
{
  "url": "https://replicate.delivery/pbxt/abc123.mp4",
  "name": "AI_Video_12345.mp4",
  "type": "video",
  "metadata": {
    "aiGenerated": true,
    "prompt": "beautiful sunset",
    "model": "wan-video/wan-2.5-t2v"
  }
}
```

**Response (Video):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "AI_Video_12345.mp4",
  "type": "video",
  "url": "",  // Empty until processing completes
  "thumbnail_url": null,
  "size": 0,
  "created_at": "2025-11-17T10:30:00Z",
  "metadata": {
    "import_job_id": "abc123-def456",
    "status": "processing"
  }
}
```

## Database Schema

### MediaAsset Model

```python
class MediaAsset:
    id: UUID                           # Primary key
    user_id: UUID                      # Owner
    name: str                          # Filename
    file_size: int                     # Size in bytes
    file_type: MediaAssetType          # IMAGE/VIDEO/AUDIO
    s3_key: str                        # S3 object key
    thumbnail_s3_key: str | None       # Thumbnail S3 key
    status: MediaAssetStatus           # UPLOADING/READY/FAILED
    checksum: str                      # SHA256 checksum
    file_metadata: dict                # JSONB: duration, dimensions, codec, etc.
    folder_id: UUID | None             # Optional folder
    tags: list[str]                    # Array of tags
    is_deleted: bool                   # Soft delete flag
    created_at: datetime
    updated_at: datetime
```

### Status Lifecycle

```
PENDING_UPLOAD → UPLOADING → READY
                     ↓
                   FAILED
```

For videos:
1. **UPLOADING**: Background job downloading/processing
2. **READY**: Upload complete, metadata extracted, thumbnail generated
3. **FAILED**: Error during processing (error stored in metadata)

## Video Metadata Fields

Stored in `MediaAsset.file_metadata` (JSONB):

```json
{
  "duration": 5.0,              // Duration in seconds
  "width": 1280,                 // Video width
  "height": 720,                 // Video height
  "frame_rate": 30.0,            // FPS
  "codec": "h264",               // Video codec
  "bitrate": 5000000,            // Bitrate in bps
  "format": "mp4",               // Container format
  "aiGenerated": true,           // AI-generated flag
  "prompt": "...",               // Generation prompt
  "model": "wan-video/wan-2.5",  // Model used
  "source": "ai_generation",     // Source type
  "source_url": "https://...",   // Original URL
  "imported_at": "2025-11-17..." // Import timestamp
}
```

## Thumbnail Generation

### Specifications

- **Timestamp**: First frame (0.0 seconds)
- **Width**: 320 pixels
- **Height**: Auto (maintains aspect ratio)
- **Format**: JPEG
- **Quality**: High (q:v 2)

### FFmpeg Command

```bash
ffmpeg -y -ss 0.0 -i video.mp4 \
  -vf scale=320:-1 \
  -vframes 1 \
  -q:v 2 \
  thumbnail.jpg
```

### Storage

- **S3 Key**: `media/{user_id}/{asset_id}/thumbnail.jpg`
- **Content-Type**: `image/jpeg`
- **Access**: Presigned URLs (1 hour expiration)

## Running the Worker

### Development (Docker Compose)

The worker is automatically started with docker-compose:

```bash
cd ffmpeg-backend
docker-compose up -d
```

This starts:
- API server (port 8000)
- RQ worker (1 instance)
- PostgreSQL database
- Redis

Check worker logs:
```bash
docker-compose logs -f worker
```

### Production (Standalone)

Run worker manually:

```bash
cd ffmpeg-backend
export REDIS_URL=redis://localhost:6379/0
export DATABASE_URL=postgresql://user:pass@localhost/db
export WORKER_QUEUES=media_import,default

python -m workers.run_worker
```

### Environment Variables

- `REDIS_URL`: Redis connection URL (default: redis://localhost:6379/0)
- `WORKER_QUEUES`: Comma-separated queue names (default: media_import,default)
- `WORKER_NAME`: Worker identifier (default: auto-generated)
- `DATABASE_URL`: PostgreSQL connection string
- `S3_*`: S3 credentials and configuration

### Scaling Workers

Run multiple workers for parallel processing:

```bash
# Worker 1
WORKER_NAME=worker-1 python -m workers.run_worker &

# Worker 2
WORKER_NAME=worker-2 python -m workers.run_worker &

# Worker 3
WORKER_NAME=worker-3 python -m workers.run_worker &
```

Or use docker-compose scaling:

```bash
docker-compose up -d --scale worker=3
```

## Monitoring

### Job Status

Check job status via API or directly in Python:

```python
from workers.job_queue import get_job_status

status = get_job_status("job-id-here")
print(status)
# {
#   "status": "finished",
#   "result": {...},
#   "error": None,
#   "progress": None
# }
```

### Redis Queues

Monitor queue status:

```bash
# Using redis-cli
redis-cli
> LLEN media_import
> LLEN default

# Using RedisInsight (docker-compose)
# Open http://localhost:5540
```

### Worker Logs

Monitor worker activity:

```bash
# Docker
docker-compose logs -f worker

# Standalone
# Worker logs to stdout
```

### Database

Check MediaAsset status:

```sql
-- Count assets by status
SELECT status, COUNT(*)
FROM media_assets
GROUP BY status;

-- Find failed imports
SELECT id, name, file_metadata->>'error' as error
FROM media_assets
WHERE status = 'failed';

-- Recent video imports
SELECT id, name, status, created_at
FROM media_assets
WHERE file_type = 'video'
ORDER BY created_at DESC
LIMIT 10;
```

## Error Handling

### Common Errors

1. **Download Timeout**: URL not responding (300s timeout)
   - Check if Replicate URL is expired (1 hour expiration)
   - Solution: Regenerate video or use fresh URL

2. **FFmpeg Processing Failed**: Invalid video file
   - Check video codec compatibility
   - Solution: Video may be corrupted, regenerate

3. **S3 Upload Failed**: Network or credentials issue
   - Verify S3 credentials and permissions
   - Check S3 bucket exists and is accessible

4. **Database Connection Lost**: Worker can't update DB
   - Check DATABASE_URL is correct
   - Verify database is running and accessible

### Error Recovery

Failed jobs are stored in Redis with error details:

```python
from workers.job_queue import get_job_status

status = get_job_status(job_id)
if status["status"] == "failed":
    print(f"Error: {status['error']}")

    # Retry by enqueuing new job
    from workers.job_queue import enqueue_video_import
    new_job_id = enqueue_video_import(url, name, user_id, asset_id, metadata)
```

## Testing

### Manual Test

```bash
# Start services
cd ffmpeg-backend
docker-compose up -d

# Import a test video
curl -X POST http://localhost:8000/api/v1/media/import-from-url \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    "name": "test_video.mp4",
    "type": "video",
    "metadata": {"test": true}
  }'

# Check job status in worker logs
docker-compose logs -f worker

# Verify in database
docker-compose exec db psql -U ffmpeg -d ffmpeg_backend \
  -c "SELECT id, name, status, file_metadata FROM media_assets ORDER BY created_at DESC LIMIT 1;"
```

### Integration Test

See `tests/test_video_import.py` for automated tests.

## Troubleshooting

### Worker Not Processing Jobs

1. Check worker is running:
   ```bash
   docker-compose ps worker
   ```

2. Check Redis connection:
   ```bash
   docker-compose exec worker python -c "from workers.redis_pool import get_redis_connection; get_redis_connection().ping()"
   ```

3. Check queue has jobs:
   ```bash
   docker-compose exec redis redis-cli LLEN media_import
   ```

### FFmpeg Not Found

1. Verify FFmpeg is installed:
   ```bash
   docker-compose exec worker ffmpeg -version
   ```

2. Check PATH includes `/usr/local/bin`:
   ```bash
   docker-compose exec worker echo $PATH
   ```

### Video Processing Slow

- Increase worker count (see Scaling Workers)
- Check CPU/memory resources
- Monitor with `docker stats`

## Performance

### Typical Processing Times

- **Download** (100MB video): 10-30 seconds
- **Metadata extraction**: 1-2 seconds
- **Thumbnail generation**: 2-5 seconds
- **S3 upload**: 10-30 seconds

**Total**: ~30-60 seconds for 100MB video

### Resource Usage

Per worker:
- **CPU**: 1-2 cores during FFmpeg processing
- **Memory**: ~500MB baseline + video size
- **Disk**: Temporary files (deleted after processing)

Recommendation: 2 workers per 2 CPU cores

## Future Enhancements

- [ ] Multiple thumbnail timestamps (beginning, middle, end)
- [ ] Video transcoding (convert to web-optimized format)
- [ ] Automatic quality adjustment based on resolution
- [ ] Progress updates during processing (via WebSocket)
- [ ] Batch processing for multiple videos
- [ ] Video preview generation (animated GIF or short clip)
- [ ] Audio waveform visualization for audio files
