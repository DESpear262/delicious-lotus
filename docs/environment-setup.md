# Environment Configuration Guide

## Overview

This guide explains how to configure environment variables for the AI Video Generation Pipeline across different environments (development, staging, production).

**Key Files:**
- `.env.example` - Local development template (comprehensive reference)
- `deploy/env.dev.template` - Development/staging deployment template
- `deploy/env.prod.template` - Production deployment template

## Quick Start

### Local Development

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Update essential variables:
   ```bash
   # Required for AI features:
   REPLICATE_API_TOKEN=your_token_here

   # Required for production storage (optional for local):
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   ```

3. Start the development environment:
   ```bash
   docker-compose up
   ```

### Production Deployment

1. Copy the production template:
   ```bash
   cp deploy/env.prod.template .env.production
   ```

2. **CRITICAL:** Replace all `CHANGE_ME_` placeholders with actual production values

3. Review security settings thoroughly

4. Consider using AWS Secrets Manager for sensitive values

## Environment Variable Reference

### Categories

1. [Environment Identification](#environment-identification)
2. [Database Configuration](#database-configuration)
3. [Redis Configuration](#redis-configuration)
4. [Backend API Configuration](#backend-api-configuration)
5. [CORS Configuration](#cors-configuration)
6. [AI Services (Replicate)](#ai-services-replicate)
7. [AWS Configuration](#aws-configuration)
8. [Storage Configuration](#storage-configuration)
9. [Video Processing (FFmpeg)](#video-processing-ffmpeg)
10. [Job Processing (Celery)](#job-processing-celery)
11. [Performance & Caching](#performance--caching)
12. [Rate Limiting](#rate-limiting)
13. [Security Settings](#security-settings)
14. [Monitoring & Logging](#monitoring--logging)
15. [Feature Flags](#feature-flags)
16. [Frontend Configuration](#frontend-configuration)

---

## Environment Identification

### ENVIRONMENT
- **Type:** String
- **Required:** Yes
- **Values:** `development`, `staging`, `production`
- **Default:** `development`
- **Description:** Identifies the current environment and affects logging, debugging, and feature availability

### DEBUG
- **Type:** Boolean
- **Required:** Yes
- **Values:** `true`, `false`
- **Default:** `true` (dev), `false` (prod)
- **Description:** Enables verbose logging and detailed error messages. **MUST be false in production.**

### LOG_LEVEL
- **Type:** String
- **Required:** Yes
- **Values:** `debug`, `info`, `warning`, `error`, `critical`
- **Default:** `debug` (dev), `warning` (prod)
- **Description:** Minimum log level to output

### LOG_FORMAT
- **Type:** String
- **Required:** Yes
- **Values:** `json`, `text`
- **Default:** `text` (dev), `json` (prod)
- **Description:** Log output format. Use `json` for structured logging in production.

---

## Database Configuration

### POSTGRES_DB
- **Type:** String
- **Required:** Yes
- **Example:** `ai_video_pipeline`
- **Description:** PostgreSQL database name

### POSTGRES_USER
- **Type:** String
- **Required:** Yes
- **Example:** `ai_video_user`
- **Description:** PostgreSQL username

### POSTGRES_PASSWORD
- **Type:** String (Secret)
- **Required:** Yes
- **Example:** `CHANGE_ME_secure_password_123`
- **Description:** PostgreSQL password. Use strong, randomly generated passwords in production.
- **Security:** Store in AWS Secrets Manager for production

### POSTGRES_HOST
- **Type:** String
- **Required:** Yes
- **Example (local):** `postgres`
- **Example (prod):** `your-rds-instance.xxxx.us-east-1.rds.amazonaws.com`
- **Description:** PostgreSQL server hostname or IP

### POSTGRES_PORT
- **Type:** Integer
- **Required:** Yes
- **Default:** `5432`
- **Description:** PostgreSQL server port

### DATABASE_URL
- **Type:** String (Secret)
- **Required:** Yes
- **Format:** `postgresql://user:password@host:port/database`
- **Example:** `postgresql://ai_video_user:password123@postgres:5432/ai_video_pipeline`
- **Description:** Full database connection string. Can be auto-constructed from individual variables.

### DB_POOL_SIZE
- **Type:** Integer
- **Required:** No
- **Default:** `10` (dev), `20` (prod)
- **Description:** Database connection pool size

### DB_MAX_OVERFLOW
- **Type:** Integer
- **Required:** No
- **Default:** `20` (dev), `40` (prod)
- **Description:** Maximum overflow connections beyond pool size

### DB_SSL_MODE
- **Type:** String
- **Required:** No (Required for production RDS)
- **Values:** `disable`, `allow`, `prefer`, `require`, `verify-ca`, `verify-full`
- **Default:** `disable` (dev), `require` (prod)
- **Description:** SSL mode for database connections

---

## Redis Configuration

### REDIS_HOST
- **Type:** String
- **Required:** Yes
- **Example (local):** `redis`
- **Example (prod):** `your-redis-cluster.xxxx.cache.amazonaws.com`
- **Description:** Redis server hostname

### REDIS_PORT
- **Type:** Integer
- **Required:** Yes
- **Default:** `6379`
- **Description:** Redis server port

### REDIS_DB
- **Type:** Integer
- **Required:** No
- **Default:** `0`
- **Description:** Redis database number (0-15)

### REDIS_PASSWORD
- **Type:** String (Secret)
- **Required:** No (Yes for production ElastiCache)
- **Example:** `CHANGE_ME_redis_auth_token`
- **Description:** Redis authentication token
- **Security:** Enable AUTH in production

### REDIS_URL
- **Type:** String (Secret)
- **Required:** Yes
- **Format:** `redis://[password@]host:port/db`
- **Example:** `redis://:auth_token@redis.example.com:6379/0`
- **Description:** Full Redis connection string

### REDIS_MAX_CONNECTIONS
- **Type:** Integer
- **Required:** No
- **Default:** `50` (dev), `100` (prod)
- **Description:** Maximum Redis connection pool size

---

## Backend API Configuration

### BACKEND_PORT
- **Type:** Integer
- **Required:** Yes
- **Default:** `8000`
- **Description:** Port the FastAPI backend listens on

### API_BASE_URL
- **Type:** String
- **Required:** Yes
- **Example (local):** `http://localhost:8000`
- **Example (prod):** `https://your-production-domain.com`
- **Description:** Base URL for the API, used by frontend

### SECRET_KEY
- **Type:** String (Secret)
- **Required:** Yes
- **Generate:** `openssl rand -hex 32`
- **Description:** Application secret key for sessions and JWT signing
- **Security:** Must be unique per environment, never reuse dev secrets in production

### JWT_SECRET_KEY
- **Type:** String (Secret)
- **Required:** Yes (if using JWT authentication)
- **Generate:** `openssl rand -hex 32`
- **Description:** Separate secret key for JWT token signing
- **Security:** Must be different from SECRET_KEY

### JWT_ALGORITHM
- **Type:** String
- **Required:** No
- **Default:** `HS256`
- **Description:** JWT signing algorithm

### JWT_ACCESS_TOKEN_EXPIRE_MINUTES
- **Type:** Integer
- **Required:** No
- **Default:** `60` (dev), `30` (prod)
- **Description:** JWT access token lifetime in minutes

### JWT_REFRESH_TOKEN_EXPIRE_DAYS
- **Type:** Integer
- **Required:** No
- **Default:** `7` (dev), `1` (prod)
- **Description:** JWT refresh token lifetime in days

---

## CORS Configuration

### ALLOWED_ORIGINS
- **Type:** String (comma-separated list)
- **Required:** Yes
- **Example (dev):** `http://localhost:5173,http://localhost:3000,http://localhost:8000`
- **Example (prod):** `https://your-production-domain.com`
- **Description:** Allowed origins for CORS requests
- **Note:** For Option B deployment (FastAPI serves static files), same-origin reduces CORS complexity

### CORS_ALLOW_CREDENTIALS
- **Type:** Boolean
- **Required:** No
- **Default:** `true`
- **Description:** Allow credentials (cookies, authorization headers) in CORS requests

### CORS_ALLOW_METHODS
- **Type:** String (comma-separated list)
- **Required:** No
- **Default:** `GET,POST,PUT,DELETE,PATCH,OPTIONS`
- **Description:** Allowed HTTP methods for CORS

### CORS_ALLOW_HEADERS
- **Type:** String (comma-separated list)
- **Required:** No
- **Default:** `*` (dev), `Content-Type,Authorization,X-Request-ID` (prod)
- **Description:** Allowed headers in CORS requests

---

## AI Services (Replicate)

### REPLICATE_API_TOKEN
- **Type:** String (Secret)
- **Required:** Yes
- **Get from:** https://replicate.com/account/api-tokens
- **Format:** `r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **Description:** Replicate API authentication token
- **Security:** Store securely, monitor usage for cost control

### REPLICATE_USE_CHEAP_MODELS
- **Type:** Boolean
- **Required:** No
- **Default:** `true` (dev), `false` (prod)
- **Description:** Use cheaper/faster models for development

### REPLICATE_MODEL_QUALITY_TIER
- **Type:** String
- **Required:** No
- **Values:** `economy`, `standard`, `premium`
- **Default:** `standard` (dev), `premium` (prod)
- **Description:** Model quality tier affecting output quality and cost

### REPLICATE_IMAGE_MODEL
- **Type:** String
- **Required:** No
- **Default:** `stability-ai/sdxl:latest`
- **Description:** Replicate model ID for image generation

### REPLICATE_VIDEO_MODEL
- **Type:** String
- **Required:** No
- **Default:** `deforum/deforum_stable_diffusion:latest`
- **Description:** Replicate model ID for video generation

### REPLICATE_TIMEOUT_SECONDS
- **Type:** Integer
- **Required:** No
- **Default:** `300` (dev), `600` (prod)
- **Description:** Timeout for Replicate API calls

### REPLICATE_MAX_RETRIES
- **Type:** Integer
- **Required:** No
- **Default:** `3` (dev), `5` (prod)
- **Description:** Maximum retry attempts for failed API calls

### REPLICATE_RETRY_DELAY_SECONDS
- **Type:** Integer
- **Required:** No
- **Default:** `5` (dev), `10` (prod)
- **Description:** Delay between retry attempts

---

## AWS Configuration

### AWS_ACCESS_KEY_ID
- **Type:** String (Secret)
- **Required:** No (local), Yes (production)
- **Example:** `AKIAIOSFODNN7EXAMPLE`
- **Description:** AWS access key ID
- **Security:** Prefer IAM roles for ECS tasks when possible
- **Alternative:** Use ECS task IAM roles instead of static credentials

### AWS_SECRET_ACCESS_KEY
- **Type:** String (Secret)
- **Required:** No (local), Yes (production)
- **Example:** `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`
- **Description:** AWS secret access key
- **Security:** Never commit to git, use Secrets Manager or IAM roles

### AWS_REGION
- **Type:** String
- **Required:** Yes (when using AWS services)
- **Default:** `us-east-1`
- **Description:** AWS region for all services

### S3_BUCKET
- **Type:** String
- **Required:** Yes (production)
- **Example:** `ai-video-prod-bucket-12345`
- **Description:** S3 bucket name for video and asset storage
- **Naming:** Must be globally unique, use environment suffix

### S3_UPLOADS_PREFIX
- **Type:** String
- **Required:** No
- **Default:** `uploads/`
- **Description:** S3 key prefix for uploaded assets

### S3_GENERATIONS_PREFIX
- **Type:** String
- **Required:** No
- **Default:** `generations/`
- **Description:** S3 key prefix for generated video clips

### S3_COMPOSITIONS_PREFIX
- **Type:** String
- **Required:** No
- **Default:** `compositions/`
- **Description:** S3 key prefix for final composed videos

### S3_TEMP_PREFIX
- **Type:** String
- **Required:** No
- **Default:** `temp/`
- **Description:** S3 key prefix for temporary files (auto-deleted)

### S3_PRESIGNED_URL_EXPIRY
- **Type:** Integer
- **Required:** No
- **Default:** `3600` (1 hour for dev), `1800` (30 min for prod)
- **Description:** Expiration time for presigned S3 URLs in seconds

### ECR_REPOSITORY
- **Type:** String
- **Required:** Yes (production)
- **Format:** `{account-id}.dkr.ecr.{region}.amazonaws.com/{repo-name}`
- **Example:** `123456789012.dkr.ecr.us-east-1.amazonaws.com/ai-video-backend`
- **Description:** ECR repository URL for Docker images

### ECS_CLUSTER
- **Type:** String
- **Required:** Yes (production)
- **Example:** `ai-video-prod-cluster`
- **Description:** ECS cluster name

### ECS_SERVICE
- **Type:** String
- **Required:** Yes (production)
- **Example:** `ai-video-prod-service`
- **Description:** ECS service name

### ECS_TASK_DEFINITION
- **Type:** String
- **Required:** Yes (production)
- **Example:** `ai-video-backend-prod`
- **Description:** ECS task definition family name

---

## Storage Configuration

### USE_LOCAL_STORAGE
- **Type:** Boolean
- **Required:** Yes
- **Default:** `true` (dev), `false` (prod)
- **Description:** Use local filesystem instead of S3 for development

### LOCAL_STORAGE_PATH
- **Type:** String
- **Required:** Yes (if USE_LOCAL_STORAGE=true)
- **Default:** `/app/storage`
- **Description:** Local filesystem path for video storage

### STORAGE_CLEANUP_ENABLED
- **Type:** Boolean
- **Required:** No
- **Default:** `true`
- **Description:** Enable automatic cleanup of old files

### STORAGE_CLEANUP_TEMP_FILES_DAYS
- **Type:** Integer
- **Required:** No
- **Default:** `1` (dev), `7` (prod)
- **Description:** Days before temporary files are deleted

### STORAGE_CLEANUP_GENERATIONS_DAYS
- **Type:** Integer
- **Required:** No
- **Default:** `7` (dev), `30` (prod)
- **Description:** Days before generated videos are deleted

---

## Video Processing (FFmpeg)

### FFMPEG_PATH
- **Type:** String
- **Required:** No
- **Default:** `/usr/bin/ffmpeg`
- **Description:** Path to FFmpeg binary (auto-detected if not specified)

### FFMPEG_THREADS
- **Type:** Integer
- **Required:** No
- **Default:** `4` (dev), `8` (prod)
- **Description:** Number of threads for FFmpeg processing

### FFMPEG_PRESET
- **Type:** String
- **Required:** No
- **Values:** `ultrafast`, `superfast`, `veryfast`, `faster`, `fast`, `medium`, `slow`, `slower`, `veryslow`
- **Default:** `medium` (dev), `fast` (prod)
- **Description:** FFmpeg encoding preset (speed vs quality tradeoff)

### OUTPUT_VIDEO_QUALITY
- **Type:** String
- **Required:** Yes
- **Default:** `720p`
- **Description:** Output video resolution quality

### OUTPUT_VIDEO_WIDTH
- **Type:** Integer
- **Required:** Yes
- **Default:** `1280`
- **Description:** Output video width in pixels

### OUTPUT_VIDEO_HEIGHT
- **Type:** Integer
- **Required:** Yes
- **Default:** `720`
- **Description:** Output video height in pixels

### OUTPUT_VIDEO_CODEC
- **Type:** String
- **Required:** Yes
- **Default:** `libx264`
- **Description:** Video codec for output

### OUTPUT_VIDEO_BITRATE
- **Type:** String
- **Required:** No
- **Default:** `2M` (dev), `3M` (prod)
- **Description:** Video bitrate (higher = better quality, larger file)

### OUTPUT_AUDIO_CODEC
- **Type:** String
- **Required:** Yes
- **Default:** `aac`
- **Description:** Audio codec for output

### OUTPUT_AUDIO_BITRATE
- **Type:** String
- **Required:** No
- **Default:** `128k` (dev), `192k` (prod)
- **Description:** Audio bitrate

### MAX_VIDEO_DURATION
- **Type:** Integer
- **Required:** Yes
- **Default:** `180`
- **Description:** Maximum video duration in seconds (3 minutes)

### MAX_AD_DURATION
- **Type:** Integer
- **Required:** Yes
- **Default:** `60`
- **Description:** Maximum ad video duration in seconds

### MAX_MUSIC_VIDEO_DURATION
- **Type:** Integer
- **Required:** Yes
- **Default:** `180`
- **Description:** Maximum music video duration in seconds

---

## Job Processing (Celery)

### CELERY_BROKER_URL
- **Type:** String (Secret)
- **Required:** Yes
- **Format:** Same as REDIS_URL
- **Description:** Celery message broker URL (typically Redis)

### CELERY_RESULT_BACKEND
- **Type:** String (Secret)
- **Required:** Yes
- **Format:** Same as REDIS_URL
- **Description:** Celery result backend URL (typically Redis)

### CELERY_WORKER_CONCURRENCY
- **Type:** Integer
- **Required:** No
- **Default:** `4` (dev), `8` (prod)
- **Description:** Number of concurrent worker processes

### MAX_CONCURRENT_JOBS
- **Type:** Integer
- **Required:** Yes
- **Default:** `5` (dev), `20` (prod)
- **Description:** Maximum concurrent video generation jobs

### JOB_TIMEOUT_SECONDS
- **Type:** Integer
- **Required:** Yes
- **Default:** `1200` (20 min for dev), `3600` (1 hour for prod)
- **Description:** Maximum time for a single job

### JOB_RETRY_MAX_ATTEMPTS
- **Type:** Integer
- **Required:** No
- **Default:** `3`
- **Description:** Maximum retry attempts for failed jobs

---

## Performance & Caching

### ENABLE_CACHING
- **Type:** Boolean
- **Required:** No
- **Default:** `true`
- **Description:** Enable response caching

### CACHE_TTL_SECONDS
- **Type:** Integer
- **Required:** No
- **Default:** `3600` (1 hour for dev), `7200` (2 hours for prod)
- **Description:** Cache time-to-live in seconds

### CACHE_AI_RESPONSES
- **Type:** Boolean
- **Required:** No
- **Default:** `true`
- **Description:** Cache Replicate API responses to reduce costs

### REUSE_SIMILAR_PROMPTS
- **Type:** Boolean
- **Required:** No
- **Default:** `true`
- **Description:** Reuse generated content for similar prompts

---

## Rate Limiting

### RATE_LIMIT_ENABLED
- **Type:** Boolean
- **Required:** No
- **Default:** `true`
- **Description:** Enable rate limiting to prevent abuse

### RATE_LIMIT_PER_MINUTE
- **Type:** Integer
- **Required:** No
- **Default:** `60` (dev), `30` (prod)
- **Description:** Maximum requests per minute per user

### RATE_LIMIT_PER_HOUR
- **Type:** Integer
- **Required:** No
- **Default:** `1000` (dev), `500` (prod)
- **Description:** Maximum requests per hour per user

---

## Security Settings

### MAX_UPLOAD_SIZE_MB
- **Type:** Integer
- **Required:** Yes
- **Default:** `100` (dev), `50` (prod)
- **Description:** Maximum file upload size in megabytes

### ALLOWED_UPLOAD_EXTENSIONS
- **Type:** String (comma-separated list)
- **Required:** Yes
- **Default:** `.mp3,.wav,.m4a,.jpg,.jpeg,.png,.gif,.webp`
- **Description:** Allowed file extensions for uploads

### MAX_PROMPT_LENGTH
- **Type:** Integer
- **Required:** Yes
- **Default:** `2000` (dev), `1500` (prod)
- **Description:** Maximum prompt length in characters

### SESSION_COOKIE_SECURE
- **Type:** Boolean
- **Required:** Yes
- **Default:** `false` (dev), `true` (prod)
- **Description:** Send cookies only over HTTPS (must be true in production)

### FORCE_HTTPS
- **Type:** Boolean
- **Required:** No
- **Default:** `false` (dev), `true` (prod)
- **Description:** Force HTTPS redirects for all requests

---

## Monitoring & Logging

### SENTRY_DSN
- **Type:** String (Secret)
- **Required:** No (Yes for production)
- **Example:** `https://xxx@xxx.ingest.sentry.io/xxx`
- **Description:** Sentry error tracking DSN
- **Get from:** https://sentry.io/

### SENTRY_ENVIRONMENT
- **Type:** String
- **Required:** No
- **Default:** Same as ENVIRONMENT
- **Description:** Environment tag for Sentry events

### SENTRY_ENABLED
- **Type:** Boolean
- **Required:** No
- **Default:** `false` (dev), `true` (prod)
- **Description:** Enable Sentry error tracking

### CLOUDWATCH_ENABLED
- **Type:** Boolean
- **Required:** No
- **Default:** `false` (dev), `true` (prod)
- **Description:** Enable CloudWatch logging

### CLOUDWATCH_LOG_GROUP
- **Type:** String
- **Required:** Yes (if CLOUDWATCH_ENABLED=true)
- **Example:** `/aws/ecs/ai-video-prod`
- **Description:** CloudWatch log group name

---

## Feature Flags

### ENABLE_AD_PIPELINE
- **Type:** Boolean
- **Required:** Yes
- **Default:** `true`
- **Description:** Enable Ad Creative Pipeline (15-60 seconds)

### ENABLE_MUSIC_VIDEO_PIPELINE
- **Type:** Boolean
- **Required:** Yes
- **Default:** `false` (MVP), `true` (post-MVP)
- **Description:** Enable Music Video Pipeline (1-3 minutes)

### ENABLE_TIMELINE_EDITOR
- **Type:** Boolean
- **Required:** No
- **Default:** `false`
- **Description:** Enable timeline-based editing features

### ENABLE_ADVANCED_TRANSITIONS
- **Type:** Boolean
- **Required:** No
- **Default:** `false`
- **Description:** Enable advanced transition effects

---

## Frontend Configuration

### SERVE_FRONTEND
- **Type:** Boolean
- **Required:** Yes (for Option B deployment)
- **Default:** `true`
- **Description:** FastAPI serves frontend static files (Option B deployment)

### FRONTEND_BUILD_PATH
- **Type:** String
- **Required:** Yes (if SERVE_FRONTEND=true)
- **Default:** `/app/frontend/dist`
- **Description:** Path to frontend build output directory

### FRONTEND_CDN_URL
- **Type:** String
- **Required:** No
- **Example:** `https://your-cdn.cloudfront.net`
- **Description:** CDN URL for static assets (optional, recommended for production)

---

## Secrets Management Best Practices

### Local Development
- Use `.env` file (never commit to git)
- Use moderate password strength
- OK to use same credentials across local dev instances

### Production
1. **Use AWS Secrets Manager** (recommended):
   ```bash
   # Store secrets in Secrets Manager
   aws secretsmanager create-secret \
     --name ai-video-prod \
     --secret-string file://secrets.json
   ```

2. **Reference secrets in ECS task definition**:
   ```json
   {
     "secrets": [
       {
         "name": "DATABASE_URL",
         "valueFrom": "arn:aws:secretsmanager:region:account:secret:ai-video-prod:DATABASE_URL::"
       }
     ]
   }
   ```

3. **Never use static credentials in production**:
   - Prefer IAM roles for ECS tasks
   - Use Secrets Manager for database passwords
   - Rotate secrets regularly (every 90 days minimum)

### Security Checklist
- [ ] All `CHANGE_ME_` placeholders replaced
- [ ] Strong, unique passwords generated (min 32 chars for production)
- [ ] DEBUG=false in production
- [ ] SESSION_COOKIE_SECURE=true in production
- [ ] FORCE_HTTPS=true in production
- [ ] Sentry enabled for error tracking
- [ ] CloudWatch enabled for logging
- [ ] Rate limiting enabled
- [ ] File upload size limits configured
- [ ] CORS origins restricted to production domain only

---

## Troubleshooting

### Database Connection Issues
- Check `DATABASE_URL` format
- Verify RDS security group allows ECS task IP range
- Ensure SSL mode matches RDS configuration
- Test connection: `psql $DATABASE_URL`

### Redis Connection Issues
- Check `REDIS_URL` format
- Verify ElastiCache security group configuration
- Test with: `redis-cli -u $REDIS_URL ping`

### S3 Access Issues
- Verify IAM role/credentials have S3 permissions
- Check bucket name and region match
- Ensure bucket exists: `aws s3 ls s3://$S3_BUCKET`

### Replicate API Issues
- Verify API token is valid
- Check rate limits haven't been exceeded
- Monitor costs at https://replicate.com/account

### CORS Issues (Option B)
- Should be minimal with same-origin deployment
- Verify `ALLOWED_ORIGINS` includes production domain
- Check browser console for specific CORS errors

---

## Environment Migration Checklist

### Development → Staging
- [ ] Copy `deploy/env.dev.template` to `.env.staging`
- [ ] Update database to staging RDS instance
- [ ] Update Redis to staging ElastiCache
- [ ] Update S3 bucket to staging bucket
- [ ] Update secrets with staging-specific values
- [ ] Enable basic monitoring (Sentry, CloudWatch)
- [ ] Test thoroughly before promoting to production

### Staging → Production
- [ ] Copy `deploy/env.prod.template` to `.env.production`
- [ ] Generate new, strong secrets (don't reuse staging)
- [ ] Update all AWS resources to production instances
- [ ] Enable all monitoring and alerting
- [ ] Set DEBUG=false
- [ ] Set SESSION_COOKIE_SECURE=true
- [ ] Configure auto-scaling
- [ ] Set up backup and disaster recovery
- [ ] Review all security settings
- [ ] Conduct security audit
- [ ] Test disaster recovery procedures

---

## Quick Reference: Required Variables

### Minimal Local Development
```bash
REPLICATE_API_TOKEN=your_token
DATABASE_URL=postgresql://user:pass@postgres:5432/db
REDIS_URL=redis://redis:6379/0
```

### Minimal Production Deployment
```bash
# Environment
ENVIRONMENT=production
DEBUG=false

# Database (RDS)
DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/db

# Redis (ElastiCache)
REDIS_URL=redis://elasticache-endpoint:6379/0

# Secrets
SECRET_KEY=generate_with_openssl_rand_hex_32
JWT_SECRET_KEY=different_random_string

# AI
REPLICATE_API_TOKEN=r8_production_token

# AWS
AWS_REGION=us-east-1
S3_BUCKET=ai-video-prod-bucket-unique
ECR_REPOSITORY=account.dkr.ecr.region.amazonaws.com/repo

# Monitoring
SENTRY_DSN=https://sentry-dsn
CLOUDWATCH_ENABLED=true

# Frontend
SERVE_FRONTEND=true
FRONTEND_BUILD_PATH=/app/frontend/dist
```

---

## Support

For questions or issues:
- Check troubleshooting section above
- Review template files for examples
- See `docs/deployment-guide.md` for deployment procedures
- See `docs/troubleshooting.md` for common issues
