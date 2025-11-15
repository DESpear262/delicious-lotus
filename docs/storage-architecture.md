# Storage Architecture
## AI Video Generation Pipeline - S3 and File Management

### Overview

This document defines the storage architecture for the AI Video Generation Pipeline, covering both local development (filesystem) and production (AWS S3) scenarios. The architecture supports the ad creative and music video pipelines with appropriate lifecycle policies, security configurations, and cost optimization strategies.

**Deployment Model:** Option B (FastAPI serves static files in single container)

**Storage Strategy:**
- **Local Development:** Filesystem storage with Docker volume mounting
- **Production:** AWS S3 with appropriate bucket organization and lifecycle policies

---

## S3 Bucket Structure

### Primary Bucket Organization

The production environment uses a single S3 bucket with a clear folder hierarchy aligned with the API specification (see `docs/api-specification-edited.md`, lines 651-675):

```
s3://ai-video-pipeline-production/
├── uploads/
│   └── {user_id}/
│       └── {upload_id}/
│           ├── original.{ext}        # User-uploaded brand assets, logos, audio
│           └── metadata.json         # Upload metadata (timestamp, size, type)
│
├── generations/
│   └── {generation_id}/
│       ├── clips/
│       │   ├── clip_001.mp4         # Individual generated video clips
│       │   ├── clip_002.mp4
│       │   └── clip_NNN.mp4
│       ├── audio/
│       │   └── background.mp3       # Generated or processed audio
│       ├── thumbnails/
│       │   ├── clip_001.jpg         # Thumbnails for preview
│       │   └── clip_002.jpg
│       └── metadata.json             # Generation parameters and results
│
├── compositions/
│   └── {composition_id}/
│       ├── final.mp4                 # Rendered final video
│       ├── thumbnail.jpg             # Video thumbnail for preview
│       ├── timeline.json             # Timeline configuration used
│       └── metadata.json             # Composition metadata
│
└── temp/
    └── {job_id}/
        └── processing/
            ├── intermediate_*.mp4    # Temporary processing files
            ├── render_pass_*.mp4     # Multi-pass encoding artifacts
            └── *.tmp                 # Various temporary files
```

### Bucket Naming Conventions

**Development:**
- `ai-video-dev-{developer-name}` (individual developer buckets)
- Example: `ai-video-dev-alice`

**Staging:**
- `ai-video-staging`

**Production:**
- `ai-video-pipeline-production`

### File Naming Conventions

**Generation IDs:** `gen_{timestamp}_{random}`
- Example: `gen_20251114_abc123xyz`

**Composition IDs:** `comp_{timestamp}_{random}`
- Example: `comp_20251114_xyz789abc`

**Clip IDs:** `clip_{sequence}`
- Example: `clip_001`, `clip_002`, etc.

**Upload IDs:** `upload_{timestamp}_{random}`
- Example: `upload_20251114_def456uvw`

---

## Lifecycle Policies

### Automatic Cleanup Rules

S3 lifecycle policies ensure cost-efficient storage management by automatically deleting temporary and outdated files.

#### Policy 1: Temporary Files (7-Day Auto-Delete)

**Target:** `temp/` folder
**Action:** Delete objects after 7 days
**Reason:** Processing artifacts no longer needed after job completion

```json
{
  "Rules": [
    {
      "Id": "delete-temp-files",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "temp/"
      },
      "Expiration": {
        "Days": 7
      }
    }
  ]
}
```

#### Policy 2: Generation Artifacts (30-Day Auto-Delete)

**Target:** `generations/` folder
**Action:** Delete objects after 30 days
**Reason:** Generated clips and intermediate assets have limited value after final composition

```json
{
  "Rules": [
    {
      "Id": "delete-generation-artifacts",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "generations/"
      },
      "Expiration": {
        "Days": 30
      }
    }
  ]
}
```

#### Policy 3: Final Compositions (90-Day Auto-Delete)

**Target:** `compositions/` folder
**Action:** Delete objects after 90 days
**Reason:** Final videos retained longer for user access and re-download

```json
{
  "Rules": [
    {
      "Id": "delete-compositions",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "compositions/"
      },
      "Expiration": {
        "Days": 90
      }
    }
  ]
}
```

#### Policy 4: User Uploads (No Auto-Delete)

**Target:** `uploads/` folder
**Action:** No automatic deletion
**Reason:** User-provided assets (logos, audio files) should persist until user explicitly deletes them

**Note:** Consider implementing user-initiated deletion via API endpoint.

#### Policy 5: Intelligent Tiering (Cost Optimization)

**Target:** All objects
**Action:** Move to Intelligent-Tiering after 30 days
**Reason:** Automatically transitions infrequently accessed objects to cheaper storage classes

```json
{
  "Rules": [
    {
      "Id": "intelligent-tiering",
      "Status": "Enabled",
      "Filter": {},
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "INTELLIGENT_TIERING"
        }
      ]
    }
  ]
}
```

### Implementing Lifecycle Policies

**AWS CLI Command:**
```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket ai-video-pipeline-production \
  --lifecycle-configuration file://lifecycle-policy.json
```

**Full Policy File Example:** See `deploy/s3-lifecycle-policy.json` (to be created during AWS setup)

---

## IAM Permissions (Least Privilege)

### ECS Task Role

The FastAPI backend running in ECS requires specific S3 permissions to manage video assets. Following the principle of least privilege, the task role grants only necessary permissions.

**Role Name:** `ecs-ai-video-backend-task-role`

**Policy Document:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowGenerationOperations",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::ai-video-pipeline-production/generations/*",
        "arn:aws:s3:::ai-video-pipeline-production/compositions/*",
        "arn:aws:s3:::ai-video-pipeline-production/temp/*"
      ]
    },
    {
      "Sid": "AllowUploadOperations",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::ai-video-pipeline-production/uploads/*"
      ]
    },
    {
      "Sid": "AllowListBucket",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::ai-video-pipeline-production"
      ],
      "Condition": {
        "StringLike": {
          "s3:prefix": [
            "generations/*",
            "compositions/*",
            "uploads/*",
            "temp/*"
          ]
        }
      }
    }
  ]
}
```

**Key Restrictions:**
- No `s3:DeleteBucket` permission (prevents accidental bucket deletion)
- No wildcard `s3:*` permissions
- Scoped to specific prefixes within the bucket
- No permissions to modify bucket policies or lifecycle rules

### User Role (for Direct Uploads - if implemented)

If implementing direct browser-to-S3 uploads (post-MVP), create a separate role with temporary credentials:

**Role Name:** `ai-video-user-upload-role`

**Permissions:**
- `s3:PutObject` only on `uploads/{user_id}/*`
- Time-limited STS credentials (15-minute expiry)

---

## Presigned URL Generation

### Overview

Presigned URLs provide secure, temporary access to S3 objects without exposing AWS credentials or making objects publicly accessible. The backend generates these URLs for both uploads and downloads.

### Download URLs (for Compositions and Clips)

**Use Case:** Allow users to download generated videos without S3 authentication

**Implementation:**

```python
# backend/app/services/storage.py
import boto3
from botocore.config import Config
from datetime import timedelta

class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            config=Config(signature_version='s3v4')
        )
        self.bucket = os.getenv('S3_BUCKET', 'ai-video-pipeline-production')

    def generate_download_url(
        self,
        object_key: str,
        expiration: int = 3600
    ) -> str:
        """
        Generate presigned URL for downloading files.

        Args:
            object_key: S3 object key (e.g., "compositions/comp_123/final.mp4")
            expiration: URL expiration in seconds (default: 1 hour)

        Returns:
            Presigned URL string
        """
        url = self.s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.bucket,
                'Key': object_key
            },
            ExpiresIn=expiration
        )
        return url
```

**API Endpoint:**

```python
# backend/app/api/v1/compositions.py
@router.get("/compositions/{composition_id}/download")
async def download_composition(composition_id: str):
    """
    Returns presigned URL for final video download.
    """
    object_key = f"compositions/{composition_id}/final.mp4"

    # Generate 1-hour expiring URL
    download_url = storage_service.generate_download_url(
        object_key,
        expiration=3600
    )

    return {
        "url": download_url,
        "expires_in": 3600,
        "filename": f"video_{composition_id}.mp4"
    }
```

### Upload URLs (for User Assets)

**Use Case:** Allow users to upload brand assets (logos, audio files) directly to S3

**Implementation:**

```python
def generate_upload_url(
    self,
    object_key: str,
    content_type: str,
    expiration: int = 900
) -> dict:
    """
    Generate presigned URL for uploading files.

    Args:
        object_key: S3 object key (e.g., "uploads/{user_id}/{upload_id}/logo.png")
        content_type: MIME type (e.g., "image/png")
        expiration: URL expiration in seconds (default: 15 minutes)

    Returns:
        Dictionary with presigned URL and required headers
    """
    url = self.s3_client.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': self.bucket,
            'Key': object_key,
            'ContentType': content_type
        },
        ExpiresIn=expiration
    )

    return {
        "upload_url": url,
        "expires_in": expiration,
        "method": "PUT",
        "headers": {
            "Content-Type": content_type
        }
    }
```

**Security Considerations:**
- Short expiration times (15 minutes for uploads, 1 hour for downloads)
- Content-Type validation to prevent malicious file uploads
- File size limits enforced at API level before URL generation
- Rate limiting on URL generation endpoints

### Expiration Times by Use Case

| Use Case | Expiration | Reason |
|----------|------------|--------|
| User uploads | 15 minutes | Short window reduces risk of URL sharing |
| Clip previews | 1 hour | Allows time for user review in browser |
| Final downloads | 6 hours | Permits slow downloads, re-downloads |
| Internal processing | 30 minutes | Service-to-service transfers |

---

## CORS Configuration

### When CORS is Needed

CORS (Cross-Origin Resource Sharing) configuration is required for:
1. **Direct browser uploads to S3** (if implemented)
2. **Client-side video playback** from S3 URLs

### S3 Bucket CORS Rules

For the chosen deployment model (Option B - single domain), CORS is minimal since the frontend is served from the same origin as the API. However, presigned S3 URLs require CORS configuration.

**CORS Configuration JSON:**

```json
[
  {
    "AllowedOrigins": [
      "https://your-production-domain.com",
      "http://localhost:5173",
      "http://localhost:8000"
    ],
    "AllowedMethods": [
      "GET",
      "PUT",
      "POST"
    ],
    "AllowedHeaders": [
      "Content-Type",
      "Content-Length",
      "Authorization",
      "X-Amz-Date",
      "X-Amz-Security-Token"
    ],
    "ExposeHeaders": [
      "ETag"
    ],
    "MaxAgeSeconds": 3600
  }
]
```

**Apply CORS Configuration:**

```bash
aws s3api put-bucket-cors \
  --bucket ai-video-pipeline-production \
  --cors-configuration file://s3-cors-config.json
```

### FastAPI CORS Configuration

The backend also needs CORS middleware configured (already in `.env.example` as `ALLOWED_ORIGINS`):

```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production Note:** Replace wildcard origins with specific production domain once deployed.

---

## Cost Optimization Strategies

### 1. Lifecycle Management (Automated)

**Savings:** ~60% reduction in storage costs
**Implementation:** Lifecycle policies (see above)
- Temp files deleted after 7 days
- Generations deleted after 30 days
- Compositions deleted after 90 days
- Intelligent-Tiering for infrequently accessed objects

**Estimated Impact:**
- Average video generation: 500MB (clips + intermediate files)
- Without lifecycle: 500MB × 100 generations = 50GB persistent
- With lifecycle: ~5GB average (90% reduction)

### 2. Multipart Upload for Large Files

**Savings:** Reduced failed upload costs, faster uploads
**Implementation:** Use S3 multipart upload for files >100MB

```python
def upload_large_file(self, file_path: str, object_key: str):
    """
    Upload large files using multipart upload.
    Automatically used for files >100MB.
    """
    self.s3_client.upload_file(
        file_path,
        self.bucket,
        object_key,
        Config=boto3.s3.transfer.TransferConfig(
            multipart_threshold=100 * 1024 * 1024,  # 100MB
            max_concurrency=10,
            multipart_chunksize=10 * 1024 * 1024     # 10MB chunks
        )
    )
```

### 3. Compression Before Upload

**Savings:** ~30% storage reduction
**Implementation:** Compress final videos to optimal bitrate

```bash
# FFmpeg compression settings in backend/app/services/video.py
ffmpeg -i input.mp4 \
  -c:v libx264 \
  -preset medium \
  -crf 23 \
  -c:a aac \
  -b:a 128k \
  output_compressed.mp4
```

**Quality vs. Size Trade-offs:**
- CRF 18: High quality, larger files (~8MB/minute)
- CRF 23: Good quality, optimal size (~4MB/minute) - **RECOMMENDED**
- CRF 28: Lower quality, small files (~2MB/minute)

### 4. Smart Caching (Avoid Re-Generation)

**Savings:** Reduced Replicate API costs, faster responses
**Implementation:** Cache similar prompts and reuse clips

```python
# backend/app/services/cache.py
async def check_similar_generation(prompt: str, parameters: dict) -> Optional[str]:
    """
    Check if similar generation exists to reuse clips.
    Uses prompt embedding similarity (cosine > 0.95).
    """
    # Hash normalized parameters
    param_hash = hash_parameters(parameters)

    # Check Redis cache for similar prompts
    cache_key = f"cache:similar:{param_hash}:{hash(prompt)}"
    cached = await redis.get(cache_key)

    if cached:
        return cached  # Return existing generation_id

    return None
```

### 5. Regional Optimization

**Savings:** Reduced data transfer costs
**Implementation:** Use same AWS region for all resources

**Recommended Region:** `us-east-1`
- Lowest S3 pricing
- Best Replicate API latency
- Most ECS/RDS availability

**Cost Comparison:**
- us-east-1: $0.023/GB storage
- us-west-2: $0.023/GB storage
- eu-west-1: $0.024/GB storage

### 6. Request Optimization

**Savings:** Reduced S3 API request costs
**Implementation:**
- Batch operations where possible
- Use S3 Select for metadata queries (instead of downloading full files)
- Minimize HEAD requests by caching object metadata

```python
# Use S3 Select for metadata extraction (avoids downloading entire file)
response = s3_client.select_object_content(
    Bucket=bucket,
    Key='generations/gen_123/metadata.json',
    Expression="SELECT * FROM S3Object[*] s WHERE s.status = 'completed'",
    ExpressionType='SQL',
    InputSerialization={'JSON': {'Type': 'DOCUMENT'}},
    OutputSerialization={'JSON': {}}
)
```

### 7. CloudFront CDN (Post-MVP)

**Savings:** Reduced S3 data transfer costs for popular videos
**Implementation:** Add CloudFront distribution in front of S3 bucket

**When to Implement:**
- If users frequently re-download videos
- If demo videos are shared publicly
- Post-MVP optimization phase

**Expected Savings:**
- S3 transfer: $0.09/GB
- CloudFront transfer: $0.085/GB + caching benefits

### Cost Tracking

**Monitor These Metrics:**
- S3 storage size per folder (`aws s3 ls --summarize --recursive`)
- Number of objects by prefix
- Request counts (PUT, GET, DELETE)
- Data transfer out
- Lifecycle transition counts

**CloudWatch Metrics to Track:**
- `BucketSizeBytes`
- `NumberOfObjects`

**Monthly Cost Estimate (MVP):**
- 100 generations/month × 500MB = 50GB storage
- With lifecycle policies: ~5GB average storage
- Estimated monthly cost: ~$1-2 (storage + requests + transfer)

---

## Local Development Storage

### Filesystem Structure

For local development, the backend uses filesystem storage instead of S3, mounted via Docker volumes.

**Docker Volume Configuration:**

```yaml
# docker-compose.yml (from PR-D001)
services:
  backend:
    volumes:
      - ./storage:/app/storage  # Local storage mount
```

**Local Storage Structure:**

```
./storage/
├── uploads/
├── generations/
├── compositions/
└── temp/
```

### Environment-Aware Storage Service

The backend automatically switches between S3 and local filesystem based on environment:

```python
# backend/app/services/storage.py
class StorageService:
    def __init__(self):
        self.use_local = os.getenv('USE_LOCAL_STORAGE', 'true').lower() == 'true'

        if self.use_local:
            self.storage_path = os.getenv('LOCAL_STORAGE_PATH', '/app/storage')
            os.makedirs(self.storage_path, exist_ok=True)
        else:
            self.s3_client = boto3.client('s3')
            self.bucket = os.getenv('S3_BUCKET')

    def save_file(self, file_path: str, object_key: str):
        """Save file to S3 or local filesystem based on environment."""
        if self.use_local:
            dest_path = os.path.join(self.storage_path, object_key)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy(file_path, dest_path)
        else:
            self.s3_client.upload_file(file_path, self.bucket, object_key)

    def get_file_url(self, object_key: str) -> str:
        """Get file URL (presigned S3 or local path)."""
        if self.use_local:
            return f"http://localhost:8000/storage/{object_key}"
        else:
            return self.generate_download_url(object_key)
```

### Serving Local Files in Development

FastAPI serves local storage files via static file mounting:

```python
# backend/app/main.py
from fastapi.staticfiles import StaticFiles

if os.getenv('USE_LOCAL_STORAGE', 'true').lower() == 'true':
    app.mount(
        "/storage",
        StaticFiles(directory="/app/storage"),
        name="storage"
    )
```

---

## Environment Variables

All storage-related environment variables are already defined in `.env.example` (lines 50-63). Here's the reference with additional context:

### S3 Configuration

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=                    # Leave empty for local dev
AWS_SECRET_ACCESS_KEY=                # Leave empty for local dev
AWS_REGION=us-east-1                  # Default region for S3 bucket

# S3 Bucket
S3_BUCKET=ai-video-dev-bucket         # Bucket name (change for production)

# Local Storage Fallback
USE_LOCAL_STORAGE=true                # true for local dev, false for production
LOCAL_STORAGE_PATH=/app/storage       # Container path for local storage
```

### Production Environment Variables

For production deployment (ECS), set these in the task definition:

```bash
# Production S3 Settings
USE_LOCAL_STORAGE=false
S3_BUCKET=ai-video-pipeline-production
AWS_REGION=us-east-1
# AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY not needed if using IAM roles
```

**Note:** ECS tasks should use IAM roles instead of hardcoded credentials. The `ecs-ai-video-backend-task-role` automatically provides S3 access without explicit credentials.

---

## Security Best Practices

### 1. Never Make Buckets Public

**Rule:** All S3 buckets must have "Block all public access" enabled.

**Why:** Presigned URLs provide controlled access without public bucket policies.

**Verification:**
```bash
aws s3api get-public-access-block --bucket ai-video-pipeline-production
```

### 2. Enable Versioning (Optional for Production)

**When:** If you need to recover deleted files or track changes

**Trade-off:** Increased storage costs vs. data recovery capability

```bash
aws s3api put-bucket-versioning \
  --bucket ai-video-pipeline-production \
  --versioning-configuration Status=Enabled
```

### 3. Enable Encryption at Rest

**Default:** S3 Server-Side Encryption (SSE-S3) - no cost

**Implementation:**
```bash
aws s3api put-bucket-encryption \
  --bucket ai-video-pipeline-production \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

### 4. Enable Access Logging (Optional)

**When:** If you need to audit S3 access for compliance or debugging

**Cost:** Additional storage for logs

```bash
aws s3api put-bucket-logging \
  --bucket ai-video-pipeline-production \
  --bucket-logging-status file://logging-config.json
```

### 5. Validate File Types on Upload

**Implementation:** Check MIME types and file extensions before generating upload URLs

```python
ALLOWED_UPLOAD_TYPES = {
    'image/png': '.png',
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/gif': '.gif',
    'audio/mpeg': '.mp3',
    'audio/wav': '.wav'
}

def validate_upload_type(content_type: str, filename: str) -> bool:
    """Ensure uploaded file type is allowed."""
    if content_type not in ALLOWED_UPLOAD_TYPES:
        return False

    allowed_exts = ALLOWED_UPLOAD_TYPES[content_type]
    if isinstance(allowed_exts, str):
        allowed_exts = [allowed_exts]

    return any(filename.lower().endswith(ext) for ext in allowed_exts)
```

---

## Monitoring and Troubleshooting

### CloudWatch Metrics to Monitor

1. **Storage Metrics:**
   - `BucketSizeBytes` (total storage used)
   - `NumberOfObjects` (object count by prefix)

2. **Request Metrics:**
   - `AllRequests` (total S3 API requests)
   - `GetRequests`, `PutRequests`, `DeleteRequests`
   - `4xxErrors`, `5xxErrors`

3. **Cost Metrics:**
   - Data transfer out
   - Lifecycle transitions

### Common Issues and Solutions

#### Issue 1: "Access Denied" when accessing S3

**Cause:** IAM role missing permissions or incorrect bucket name

**Solution:**
1. Verify bucket name in environment variable: `echo $S3_BUCKET`
2. Check ECS task role has correct permissions
3. Verify object key exists: `aws s3 ls s3://bucket/path/`

#### Issue 2: Presigned URLs returning 403

**Cause:** URL expired or wrong signature version

**Solution:**
1. Check URL expiration timestamp
2. Ensure `signature_version='s3v4'` in boto3 config
3. Verify system clock is synchronized (presigned URLs use timestamps)

#### Issue 3: CORS errors in browser

**Cause:** S3 CORS configuration missing or incorrect

**Solution:**
1. Verify CORS policy includes your domain
2. Check allowed methods include GET/PUT
3. Ensure `AllowedHeaders` includes required S3 headers

#### Issue 4: High S3 costs

**Cause:** Lifecycle policies not running or too many requests

**Solution:**
1. Verify lifecycle policy status: `aws s3api get-bucket-lifecycle-configuration`
2. Check request counts in CloudWatch
3. Implement request batching and caching

#### Issue 5: Local storage not accessible in Docker

**Cause:** Volume mount missing or incorrect permissions

**Solution:**
1. Verify volume in docker-compose.yml: `./storage:/app/storage`
2. Check directory permissions: `chmod -R 755 ./storage`
3. Ensure directory exists before starting container

---

## Deployment Checklist

### Pre-Production Setup

- [ ] Create S3 bucket with appropriate name
- [ ] Enable "Block all public access"
- [ ] Configure lifecycle policies (7-day temp, 30-day generations, 90-day compositions)
- [ ] Enable S3 Server-Side Encryption (SSE-S3)
- [ ] Apply CORS configuration
- [ ] Create IAM role for ECS tasks with least privilege S3 permissions
- [ ] Attach IAM role to ECS task definition
- [ ] Set environment variables in ECS task definition (`USE_LOCAL_STORAGE=false`, `S3_BUCKET=...`)
- [ ] Test presigned URL generation
- [ ] Verify lifecycle policies are active
- [ ] Set up CloudWatch monitoring for bucket metrics
- [ ] Document bucket name and region in deployment notes

### Post-Deployment Verification

- [ ] Upload test file via API
- [ ] Generate presigned download URL
- [ ] Verify CORS headers in browser
- [ ] Check lifecycle policy execution (after 7 days)
- [ ] Monitor S3 costs in AWS Cost Explorer
- [ ] Test file deletion via API
- [ ] Verify IAM permissions work correctly
- [ ] Test both local dev and production storage paths

---

## Future Enhancements (Post-MVP)

### 1. CloudFront CDN
- Add CloudFront distribution for video delivery
- Reduce S3 data transfer costs
- Improve global download speeds

### 2. S3 Transfer Acceleration
- Enable for faster uploads from distant regions
- Useful for international users
- Additional cost: $0.04-$0.08/GB

### 3. Multi-Region Replication
- Replicate bucket to secondary region
- Disaster recovery and reduced latency
- Doubles storage costs

### 4. Advanced Lifecycle Policies
- Transition to Glacier for long-term archival
- Further cost reduction for rarely accessed videos

### 5. S3 Batch Operations
- Bulk processing of existing objects
- Apply tags, copy, or delete operations at scale

---

## References

- **API Specification:** `docs/api-specification-edited.md` (lines 651-675)
- **Environment Variables:** `.env.example` (lines 50-63)
- **Local Setup:** `docs/local-setup.md`
- **Deployment Decision:** `docs/task-list-devops.md` (line 11)
- **AWS S3 Pricing:** https://aws.amazon.com/s3/pricing/
- **S3 Lifecycle Policies:** https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html
- **IAM Best Practices:** https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
