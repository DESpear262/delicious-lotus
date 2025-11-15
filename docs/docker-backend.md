# FastAPI Backend Docker Configuration

**Status:** Complete
**Created:** 2025-11-14
**Component:** Backend Docker Container (PR-D002)

---

## Overview

This document describes the Docker configuration for the FastAPI backend service, which includes:
- Python 3.13 runtime
- FFmpeg for video processing
- Static file serving for frontend (Option B deployment)
- Production-optimized multi-stage build
- Security hardening (non-root user)

**Target Image Size:** <500MB
**Base Image:** `python:3.13-slim`

---

## Quick Start

### Build the Image

```bash
# From project root
./scripts/build-backend.sh

# Or with custom tag
./scripts/build-backend.sh v1.0.0
```

### Run Tests

```bash
./scripts/test-backend.sh
```

### Run Container Standalone

```bash
docker run -p 8000:8000 ai-video-backend:latest
```

### Run with Docker Compose

```bash
# Basic backend only
cd fastapi
docker-compose -f docker-compose.test.yml up

# With full stack (postgres + redis)
docker-compose -f docker-compose.test.yml --profile full up
```

---

## Architecture

### Multi-Stage Build

The Dockerfile uses a two-stage build process:

**Stage 1: Builder**
- Installs build dependencies (gcc, g++)
- Creates Python virtual environment
- Installs all Python packages from requirements.txt
- Optimizes for clean dependency installation

**Stage 2: Runtime**
- Starts from fresh `python:3.13-slim`
- Installs FFmpeg and runtime dependencies
- Copies virtual environment from builder
- Copies application code
- Runs as non-root user (`appuser`)

### Directory Structure in Container

```
/app/                          # Application root
├── app/                       # FastAPI application code
│   ├── main.py               # Application entry point
│   ├── api/                  # API routes
│   ├── core/                 # Core functionality
│   └── models/               # Data models
├── frontend/                  # Frontend static files
│   └── dist/                 # Built frontend assets
│       ├── index.html        # SPA entry point
│       └── assets/           # JS, CSS, images
├── temp/                      # Temporary files
└── uploads/                   # User uploads
```

### Static File Serving

The backend serves frontend static files via FastAPI's `StaticFiles`:

- **Assets**: `/assets/*` → `frontend/dist/assets/*`
- **SPA Routing**: All non-API routes → `frontend/dist/index.html`
- **API Routes**: `/api/*` and `/health` take precedence

This enables single-container deployment (Option B) with unified CORS and simplified infrastructure.

---

## Building

### Build Command

```bash
docker build -t ai-video-backend:latest ./fastapi
```

### Build Arguments

Currently no build arguments are used. Future enhancements may include:
- `PYTHON_VERSION` - Override Python version
- `FFMPEG_VERSION` - Pin FFmpeg version
- `BUILD_ENV` - Build environment flag

### Build Optimization

The build is optimized for:

1. **Layer Caching**
   - Requirements installed before code copy
   - Dependency changes don't invalidate code layers

2. **Size Reduction**
   - Multi-stage build discards build tools
   - `--no-install-recommends` for apt packages
   - Cleanup of package lists after install

3. **Security**
   - Non-root user (`appuser`)
   - Minimal base image (slim variant)
   - No unnecessary packages

### Build Time

- **Cold build:** ~3-5 minutes
- **Cached build:** ~30 seconds

---

## Running

### Environment Variables

Required variables for production:

```bash
# Core Settings
APP_ENV=production
LOG_LEVEL=INFO

# API Configuration
API_TITLE="AI Video Generation Pipeline"
API_VERSION=0.1.0
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Database
DATABASE_URL=postgresql://user:pass@host:5432/videogen

# Redis
REDIS_URL=redis://host:6379/0

# Replicate API
REPLICATE_API_TOKEN=your_token_here

# AWS (if using S3)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
S3_BUCKET=your-bucket

# Feature Flags
ENABLE_STATIC_FILES=true
```

See `deploy/env.prod.template` for complete list.

### Health Checks

The container includes built-in health checks:

**Health Check Configuration:**
- **Interval:** 30 seconds
- **Timeout:** 10 seconds
- **Start Period:** 5 seconds
- **Retries:** 3

**Endpoints:**
- `/health` - Basic health check
- `/health/detailed` - Detailed system status

**Manual Health Check:**
```bash
curl http://localhost:8000/health
# {"status":"healthy","service":"ai-video-generation-pipeline"}
```

### Ports

- **8000** - HTTP API and static file serving

### Resource Requirements

**Minimum:**
- CPU: 1 core
- Memory: 512MB
- Disk: 1GB

**Recommended (with video processing):**
- CPU: 2 cores
- Memory: 2GB
- Disk: 10GB

---

## Testing

### Automated Tests

Run the complete test suite:

```bash
./scripts/test-backend.sh
```

**Tests included:**
1. ✓ Image exists
2. ✓ Container starts
3. ✓ Container becomes healthy
4. ✓ Health endpoint responds
5. ✓ FFmpeg is installed
6. ✓ Python 3.13 is present
7. ✓ Running as non-root
8. ✓ API routes respond
9. ✓ No errors in logs

### Manual Testing

**Test FFmpeg:**
```bash
docker exec backend-test ffmpeg -version
```

**Test API:**
```bash
curl http://localhost:8000/api/v1/ping
```

**View Logs:**
```bash
docker logs backend-test -f
```

**Interactive Shell:**
```bash
docker exec -it backend-test /bin/bash
```

### Integration Testing

Test with full stack (PR-D001):

```bash
# From project root
docker-compose up

# Backend should be accessible at:
# http://localhost:8000
```

---

## Troubleshooting

### Container Won't Start

**Symptom:** Container exits immediately

**Solutions:**
1. Check logs: `docker logs <container-name>`
2. Verify environment variables are set
3. Check port 8000 isn't already in use: `lsof -i :8000`
4. Verify image built successfully: `docker images ai-video-backend`

### Health Check Failing

**Symptom:** Container marked as unhealthy

**Solutions:**
1. Check if app is running: `docker exec <container> ps aux`
2. Test health endpoint manually: `curl http://localhost:8000/health`
3. Check logs for startup errors
4. Verify Python dependencies installed: `docker exec <container> pip list`

### FFmpeg Not Working

**Symptom:** Video processing fails

**Solutions:**
1. Verify FFmpeg installed: `docker exec <container> ffmpeg -version`
2. Check FFmpeg has required codecs: `docker exec <container> ffmpeg -codecs`
3. Verify file permissions in /app/temp directory
4. Check available disk space

### Static Files Not Serving

**Symptom:** Frontend returns 404

**Solutions:**
1. Verify `ENABLE_STATIC_FILES=true` is set
2. Check frontend/dist exists: `docker exec <container> ls -la /app/frontend/dist`
3. Verify build included frontend files
4. Check CORS settings if accessing from different domain

### Memory Issues

**Symptom:** Container OOM (Out of Memory)

**Solutions:**
1. Increase container memory limit
2. Check for memory leaks in logs
3. Reduce concurrent video processing jobs
4. Monitor with: `docker stats <container>`

### Build Failures

**Symptom:** Docker build fails

**Common Causes:**
1. **Network issues:** Retry build, check internet connection
2. **Dependency conflicts:** Update requirements.txt
3. **Python version:** Verify Python 3.13 compatibility
4. **Disk space:** Clean old images: `docker system prune`

---

## Production Deployment

### ECS Task Definition

Example for AWS ECS (Fargate):

```json
{
  "family": "ai-video-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-video-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "APP_ENV", "value": "production"},
        {"name": "LOG_LEVEL", "value": "INFO"}
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:..."
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ai-video-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### CI/CD Integration

See `docs/deployment-guide.md` for complete CI/CD setup.

**Quick CI/CD Steps:**
1. Build image: `docker build -t ai-video-backend:${GIT_SHA} .`
2. Tag image: `docker tag ai-video-backend:${GIT_SHA} ${ECR_URL}:${GIT_SHA}`
3. Push to ECR: `docker push ${ECR_URL}:${GIT_SHA}`
4. Update ECS task: `aws ecs update-service ...`

---

## Security Considerations

### Non-Root User

The container runs as `appuser` (non-root) for security:
- UID/GID created during build
- Home directory: `/app`
- No shell access: `/sbin/nologin`

### Secret Management

**Never include secrets in:**
- Dockerfile
- Image layers
- Environment variables in docker-compose.yml (for production)

**Use instead:**
- AWS Secrets Manager
- Environment files (`.env`) excluded from git
- Docker secrets
- ECS task definition secrets

### Image Scanning

Recommended tools:
- `docker scan ai-video-backend:latest`
- AWS ECR image scanning
- Trivy: `trivy image ai-video-backend:latest`

---

## Maintenance

### Updating Dependencies

1. Update `requirements.txt`
2. Rebuild image: `./scripts/build-backend.sh`
3. Run tests: `./scripts/test-backend.sh`
4. Deploy new version

### Monitoring Image Size

```bash
# Check image size
docker images ai-video-backend --format "{{.Size}}"

# Compare sizes between tags
docker images ai-video-backend --format "table {{.Tag}}\t{{.Size}}"

# Analyze layer sizes
docker history ai-video-backend:latest
```

### Cleanup

```bash
# Remove old images
docker image prune -a

# Remove test containers
docker rm -f $(docker ps -a -q --filter "name=backend-test")

# Full cleanup (careful!)
docker system prune -a --volumes
```

---

## Performance Tuning

### Build Performance

```bash
# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1
docker build -t ai-video-backend:latest ./fastapi
```

### Runtime Performance

1. **Increase workers:**
   ```bash
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
   ```

2. **Enable Gunicorn:**
   ```bash
   CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
   ```

3. **Adjust memory limits:**
   ```bash
   docker run -m 2g --memory-swap 2g ai-video-backend:latest
   ```

---

## Files Reference

### Created Files

- `fastapi/Dockerfile` - Multi-stage production build
- `fastapi/.dockerignore` - Build exclusions
- `fastapi/docker-compose.test.yml` - Local testing
- `scripts/build-backend.sh` - Build automation
- `scripts/test-backend.sh` - Testing automation
- `docs/docker-backend.md` - This document

### Related Files

- `docker-compose.yml` - Full stack (PR-D001)
- `deploy/env.prod.template` - Production environment template (PR-D005)
- `.github/workflows/deploy-backend.yml` - CI/CD pipeline (PR-D004, future)

---

## Next Steps

After completing PR-D002:
1. **PR-D004:** CI/CD Pipeline - Automated build and deployment
2. **PR-D006:** Monitoring - CloudWatch integration
3. **Integration:** Connect with AI backend team for video generation

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [AWS ECS Task Definitions](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definitions.html)

---

**Last Updated:** 2025-11-14
**Maintained By:** DevOps Team
