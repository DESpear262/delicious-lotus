# Video Processing Setup Guide

## Quick Start

This system automatically saves AI-generated videos from Replicate to permanent S3 storage with metadata extraction and thumbnail generation.

## 🚀 What's Been Implemented

### ✅ Complete Video Processing Pipeline

1. **Replicate Webhook** → Automatically captures video generation completions
2. **Background Job Queue** → Asynchronous processing with Redis Queue (RQ)
3. **Video Processor** → FFmpeg/FFprobe for metadata extraction and thumbnails
4. **S3 Storage** → Permanent storage with presigned URLs
5. **Database** → MediaAsset records with full metadata

### ✅ Key Features

- **First frame thumbnail**: 320px width, maintains aspect ratio
- **Video metadata**: Duration, dimensions, codec, bitrate, frame rate
- **Async processing**: Non-blocking, returns immediately
- **Error handling**: Failed jobs tracked with error messages
- **Auto-tagging**: AI-generated content automatically tagged

## 📦 Files Created/Modified

### New Files

1. **`src/workers/video_processor.py`** - FFmpeg/FFprobe utilities
2. **`src/workers/video_import_job.py`** - Background job for video/image import
3. **`src/workers/job_queue.py`** - RQ job queue manager
4. **`src/workers/run_worker.py`** - Worker startup script
5. **`VIDEO_PROCESSING.md`** - Complete documentation

### Modified Files

1. **`src/app/api/v1/replicate.py`** - Webhook now enqueues import jobs
2. **`src/app/api/v1/media.py`** - Import endpoint uses async processing for videos
3. **`docker-compose.yml`** - Worker service configured with correct queues

### Already Present (No Changes Needed)

1. **`Dockerfile`** - FFmpeg already installed ✅
2. **`requirements.txt`** - RQ (Redis Queue) already installed ✅

## 🔧 Setup Instructions

### 1. Start Services

```bash
cd ffmpeg-backend

# Start all services (API + Worker + DB + Redis)
docker-compose up -d

# Check services are running
docker-compose ps

# Watch worker logs
docker-compose logs -f worker
```

### 2. Verify FFmpeg Installation

```bash
# Check FFmpeg is available in worker
docker-compose exec worker ffmpeg -version
docker-compose exec worker ffprobe -version
```

### 3. Test Video Import

#### Option A: Via Replicate Webhook (Automatic)

When you generate a video using the Replicate endpoints:

```bash
# Generate video (existing endpoint)
curl -X POST http://localhost:8000/api/v1/replicate/wan-video-t2v \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "beautiful sunset over mountains",
    "size": "720p",
    "duration": "5s"
  }'

# Response includes job_id
# {"job_id": "abc123...", "status": "starting", ...}

# When video generation completes, webhook automatically:
# 1. Receives completion notification from Replicate
# 2. Enqueues background job to save to S3
# 3. Worker downloads, processes, and uploads
# 4. MediaAsset created with thumbnail and metadata
```

#### Option B: Manual Import (Test URL)

```bash
# Import a test video directly
curl -X POST http://localhost:8000/api/v1/media/import-from-url \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    "name": "test_video.mp4",
    "type": "video",
    "metadata": {"test": true}
  }'

# Response includes asset_id and import_job_id
# Processing happens in background
```

### 4. Monitor Processing

```bash
# Watch worker logs to see processing
docker-compose logs -f worker

# You should see logs like:
# INFO - Starting video import job
# INFO - Downloaded video: 158008374 bytes
# INFO - Processing video: extracting metadata and generating thumbnail
# INFO - Video processing complete
# INFO - Uploading video to S3
# INFO - Uploading thumbnail to S3
# INFO - Video import job completed successfully
```

### 5. Verify in Database

```bash
# Check MediaAsset was created
docker-compose exec db psql -U ffmpeg -d ffmpeg_backend -c \
  "SELECT id, name, status, file_metadata->>'duration' as duration,
   file_metadata->>'width' as width, file_metadata->>'height' as height,
   thumbnail_s3_key
   FROM media_assets
   WHERE file_type = 'video'
   ORDER BY created_at DESC
   LIMIT 1;"
```

Expected output:
```
                  id                  |      name       | status | duration | width | height |        thumbnail_s3_key
--------------------------------------+-----------------+--------+----------+-------+--------+--------------------------------
 550e8400-e29b-41d4-a716-446655440000 | test_video.mp4  | ready  | 596.0    | 1280  | 720    | media/{user_id}/{asset_id}/thumbnail.jpg
```

### 6. Access Media

```bash
# List all media assets with URLs
curl http://localhost:8000/api/v1/media/

# Response includes presigned URLs for both video and thumbnail
# {
#   "assets": [{
#     "id": "...",
#     "url": "https://s3.../video.mp4?signature=...",
#     "thumbnail_url": "https://s3.../thumbnail.jpg?signature=...",
#     "metadata": {
#       "duration": 596.0,
#       "width": 1280,
#       "height": 720,
#       ...
#     }
#   }]
# }
```

## 🎯 How It Works

### Complete Flow

```
1. Replicate AI generates video → Temporary URL (expires in 1 hour)
2. Webhook receives completion → Enqueues import job
3. Worker downloads video → Calculates SHA256 checksum
4. FFprobe extracts metadata → Duration, dimensions, codec, etc.
5. FFmpeg generates thumbnail → First frame at 320px width
6. Upload to S3 → Video + thumbnail (permanent storage)
7. Update database → MediaAsset with metadata
8. Frontend polls → Gets asset_id and accesses via presigned URLs
```

### Processing Details

- **Video Download**: Streaming with progress tracking
- **Thumbnail**: First frame (0.0s), 320px width, JPEG format
- **Metadata**: Duration, dimensions, frame rate, codec, bitrate
- **Storage**: S3 keys follow pattern `media/{user_id}/{asset_id}/`
- **URLs**: Presigned (1 hour expiration) generated on-demand

## ⚙️ Configuration

### Environment Variables

Add to `.env` file:

```bash
# Redis (already configured)
REDIS_URL=redis://redis:6379/0

# S3 Storage (should already be configured)
S3_BUCKET_NAME=your-bucket
S3_ACCESS_KEY_ID=your-key
S3_SECRET_ACCESS_KEY=your-secret
S3_REGION=us-east-1

# Worker Settings (optional)
WORKER_QUEUES=media_import,default  # Queues to process
WORKER_NAME=worker-1                # Worker identifier
```

### Scaling Workers

For high-volume processing, run multiple workers:

```bash
# Scale to 3 workers
docker-compose up -d --scale worker=3

# Or manually for specific queues
WORKER_NAME=worker-videos WORKER_QUEUES=media_import python -m workers.run_worker &
WORKER_NAME=worker-general WORKER_QUEUES=default python -m workers.run_worker &
```

## 🐛 Troubleshooting

### Worker Not Processing

```bash
# Check worker is running
docker-compose ps worker

# Check worker logs for errors
docker-compose logs worker

# Restart worker
docker-compose restart worker
```

### FFmpeg Errors

```bash
# Verify FFmpeg installation
docker-compose exec worker ffmpeg -version

# Test thumbnail generation manually
docker-compose exec worker ffmpeg -ss 0 -i /path/to/video.mp4 -vframes 1 -q:v 2 test.jpg
```

### Jobs Stuck in Queue

```bash
# Check Redis queue length
docker-compose exec redis redis-cli LLEN media_import

# View failed jobs
docker-compose exec redis redis-cli KEYS "rq:job:*"

# Clear queue (use with caution!)
docker-compose exec redis redis-cli DEL media_import
```

### Database Connection Issues

```bash
# Test database connection
docker-compose exec worker python -c "from db.session import SessionLocal; db = SessionLocal(); db.execute('SELECT 1'); print('✅ DB Connected')"

# Check DATABASE_URL
docker-compose exec worker env | grep DATABASE_URL
```

## 📊 Monitoring

### Redis Queue Status

```bash
# Queue lengths
docker-compose exec redis redis-cli LLEN media_import
docker-compose exec redis redis-cli LLEN default

# View with RedisInsight (GUI)
open http://localhost:5540
```

### Worker Performance

```bash
# Resource usage
docker stats ffmpeg-backend-worker

# Job processing rate
docker-compose logs worker | grep "Video import job completed"
```

### Database Stats

```sql
-- Asset status distribution
SELECT status, COUNT(*) FROM media_assets GROUP BY status;

-- Recent imports
SELECT name, status, created_at FROM media_assets
WHERE file_type = 'video'
ORDER BY created_at DESC LIMIT 10;

-- Failed imports
SELECT id, name, file_metadata->>'error' FROM media_assets
WHERE status = 'failed';
```

## 🎨 Frontend Integration

The frontend should poll the `/api/v1/media/{asset_id}` endpoint to check when video processing completes:

```typescript
// After receiving asset_id from import response
const pollAssetStatus = async (assetId: string) => {
  const response = await fetch(`/api/v1/media/${assetId}`);
  const asset = await response.json();

  if (asset.status === 'ready') {
    // Video is ready! Show it
    console.log('Video URL:', asset.url);
    console.log('Thumbnail URL:', asset.thumbnail_url);
    console.log('Duration:', asset.metadata.duration);
    console.log('Dimensions:', `${asset.metadata.width}x${asset.metadata.height}`);
  } else if (asset.status === 'uploading') {
    // Still processing, poll again in 2 seconds
    setTimeout(() => pollAssetStatus(assetId), 2000);
  } else if (asset.status === 'failed') {
    // Processing failed
    console.error('Import failed:', asset.metadata.error);
  }
};
```

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] Services started: `docker-compose ps` shows all services running
- [ ] Worker running: `docker-compose logs worker` shows "Worker started"
- [ ] FFmpeg available: `docker-compose exec worker ffmpeg -version` succeeds
- [ ] Redis connected: Worker logs show no Redis errors
- [ ] Test import succeeds: Import test video completes successfully
- [ ] Thumbnail generated: `thumbnail_s3_key` populated in database
- [ ] Metadata extracted: `duration`, `width`, `height` present
- [ ] S3 URLs work: Can access video and thumbnail via presigned URLs

## 📚 Additional Documentation

- **`VIDEO_PROCESSING.md`** - Complete technical documentation
- **`src/workers/video_processor.py`** - FFmpeg utilities with docstrings
- **`src/workers/video_import_job.py`** - Background job implementation
- **`src/workers/job_queue.py`** - Queue management API

## 🚀 Next Steps

1. **Test with real Replicate video**: Generate video via AI endpoint
2. **Monitor first import**: Watch logs as video is processed
3. **Verify frontend**: Update UI to show processing status
4. **Scale if needed**: Add more workers for high volume

---

**Need help?** Check logs and refer to VIDEO_PROCESSING.md for detailed troubleshooting!
