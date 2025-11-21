# Local Development Setup Guide
## AI Video Generation Pipeline

This guide will help you set up the local development environment for the AI Video Generation Pipeline using Docker Compose.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Testing the Environment](#testing-the-environment)
5. [Working with Services](#working-with-services)
6. [Troubleshooting](#troubleshooting)
7. [Next Steps](#next-steps)

---

## Prerequisites

Before you begin, ensure you have the following installed on your system:

### Required Software

- **Docker Desktop** (version 20.10 or higher)
  - [Download for Windows](https://docs.docker.com/desktop/install/windows-install/)
  - [Download for Mac](https://docs.docker.com/desktop/install/mac-install/)
  - [Download for Linux](https://docs.docker.com/desktop/install/linux-install/)

- **Docker Compose** (version 2.0 or higher)
  - Included with Docker Desktop
  - For Linux: [Install Docker Compose](https://docs.docker.com/compose/install/)

- **Git** (for cloning the repository)
  - [Download Git](https://git-scm.com/downloads)

### System Requirements

- **RAM:** Minimum 8GB (16GB recommended)
- **Disk Space:** At least 20GB free space
- **CPU:** Multi-core processor recommended for video processing

---

## Quick Start

If you're familiar with Docker and want to get started immediately:

```bash
# 1. Clone the repository
git clone <repository-url>
cd delicious-lotus

# 2. Copy environment file
cp .env.example .env

# 3. Edit .env and set your Replicate API token (optional for infrastructure testing)
# REPLICATE_API_TOKEN=your_token_here

# 4. Start all services
docker-compose up -d

# 5. Check service health
docker-compose ps

# 6. View logs
docker-compose logs -f
```

Your local environment is now running! PostgreSQL is available on port 5432, Redis on port 6379.

---

## Detailed Setup

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd delicious-lotus
```

### Step 2: Configure Environment Variables

1. **Copy the example environment file:**

   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file:**

   Open `.env` in your text editor and configure the following:

   #### Essential Settings (for basic functionality)

   ```env
   # Database credentials (can keep defaults for local dev)
   POSTGRES_DB=ai_video_pipeline
   POSTGRES_USER=ai_video_user
   POSTGRES_PASSWORD=dev_password_change_me

   # Redis (defaults are fine)
   REDIS_PORT=6379

   # Backend (defaults are fine)
   BACKEND_PORT=8000
   ```

   #### Optional Settings (for full functionality)

   ```env
   # Replicate API Token (required for AI video generation)
   # Get yours at: https://replicate.com/account/api-tokens
   REPLICATE_API_TOKEN=r8_your_token_here

   # AWS Credentials (optional for local dev - uses local storage fallback)
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=us-east-1
   S3_BUCKET=ai-video-dev-bucket
   ```

   **Note:** You can start with just the database settings. The backend will use local storage if AWS credentials are not provided.

### Step 3: Start the Services

#### Option A: Start all services (recommended)

```bash
docker-compose up -d
```

This starts all services in detached mode (runs in background).

#### Option B: Start with logs visible

```bash
docker-compose up
```

This keeps logs visible in your terminal. Use `Ctrl+C` to stop.

#### Option C: Start specific services

```bash
# Start only database and cache
docker-compose up -d postgres redis
```

### Step 4: Verify Services are Running

Check the status of all services:

```bash
docker-compose ps
```

You should see output similar to:

```
NAME                    STATUS              PORTS
ai-video-postgres       Up (healthy)        0.0.0.0:5432->5432/tcp
ai-video-redis          Up (healthy)        0.0.0.0:6379->6379/tcp
ai-video-backend        Up                  0.0.0.0:8000->8000/tcp
ai-video-celery-worker  Up                  -
```

**Note:** Backend and Celery services show placeholder messages until the backend team provides the FastAPI structure.

---

## Testing the Environment

### Test PostgreSQL Connection

#### Using psql (if installed locally)

```bash
psql -h localhost -p 5432 -U ai_video_user -d ai_video_pipeline
```

Password: `dev_password_change_me` (or whatever you set in `.env`)

#### Using Docker exec

```bash
docker exec -it ai-video-postgres psql -U ai_video_user -d ai_video_pipeline
```

#### Verify database schema

Once connected to psql:

```sql
-- List all tables
\dt

-- You should see:
-- generation_jobs, clips, compositions, brand_assets, user_sessions, etc.

-- Check a table structure
\d generation_jobs

-- Query default session
SELECT * FROM user_sessions;

-- Exit
\q
```

### Test Redis Connection

#### Using redis-cli (if installed locally)

```bash
redis-cli -h localhost -p 6379
```

#### Using Docker exec

```bash
docker exec -it ai-video-redis redis-cli
```

#### Verify Redis is working

```bash
# Test basic operations
PING
# Should return: PONG

# Set a test key
SET test_key "Hello from AI Video Pipeline"
GET test_key

# Check server info
INFO server

# Exit
exit
```

### Test Database Schema

Run a sample query to verify the schema is properly initialized:

```bash
docker exec -it ai-video-postgres psql -U ai_video_user -d ai_video_pipeline -c "SELECT version, description FROM schema_migrations;"
```

Expected output:
```
 version |                          description
---------+----------------------------------------------------------------
       1 | Initial schema - MVP database structure for AI Video Generation Pipeline
```

---

## Working with Services

### Viewing Logs

#### View all service logs

```bash
docker-compose logs -f
```

#### View specific service logs

```bash
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f backend
docker-compose logs -f celery-worker
```

### Stopping Services

#### Stop all services (keeps data)

```bash
docker-compose stop
```

#### Stop and remove containers (keeps data in volumes)

```bash
docker-compose down
```

#### Stop and remove everything including volumes (CAUTION: deletes all data)

```bash
docker-compose down -v
```

### Restarting Services

#### Restart all services

```bash
docker-compose restart
```

#### Restart specific service

```bash
docker-compose restart postgres
docker-compose restart redis
```

### Rebuilding Services

If you make changes to Docker configurations:

```bash
# Rebuild and restart
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build backend
```

---

## Database Management

### Accessing the Database

#### Interactive psql session

```bash
docker exec -it ai-video-postgres psql -U ai_video_user -d ai_video_pipeline
```

#### Run a single SQL command

```bash
docker exec -it ai-video-postgres psql -U ai_video_user -d ai_video_pipeline -c "SELECT COUNT(*) FROM generation_jobs;"
```

### Backing Up the Database

```bash
# Create backup
docker exec ai-video-postgres pg_dump -U ai_video_user ai_video_pipeline > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
docker exec -i ai-video-postgres psql -U ai_video_user -d ai_video_pipeline < backup_20251114_120000.sql
```

### Resetting the Database

If you need to start fresh:

```bash
# Stop services
docker-compose down

# Remove database volume
docker volume rm delicious-lotus_postgres_data

# Restart services (will reinitialize database)
docker-compose up -d postgres
```

### Database Maintenance Functions

The schema includes helper functions:

```sql
-- Clean up expired sessions
SELECT cleanup_expired_sessions();

-- Clean up old jobs (older than 7 days)
SELECT cleanup_old_jobs(7);
```

---

## Redis Management

### Accessing Redis CLI

```bash
docker exec -it ai-video-redis redis-cli
```

### Monitoring Redis

```bash
# Monitor commands in real-time
docker exec -it ai-video-redis redis-cli MONITOR

# Get statistics
docker exec -it ai-video-redis redis-cli INFO stats

# Get memory usage
docker exec -it ai-video-redis redis-cli INFO memory
```

### Clearing Redis Data

```bash
# CAUTION: This deletes all data in Redis
docker exec -it ai-video-redis redis-cli FLUSHALL
```

---

## Troubleshooting

### Services Won't Start

#### Check Docker is running

```bash
docker --version
docker-compose --version
```

#### Check port conflicts

```bash
# On Windows (PowerShell)
Get-NetTCPConnection -LocalPort 5432,6379,8000

# On macOS/Linux
lsof -i :5432
lsof -i :6379
lsof -i :8000
```

If ports are in use, either:
1. Stop the conflicting service
2. Change ports in `.env` file

#### View detailed error logs

```bash
docker-compose logs postgres
docker-compose logs redis
```

### Database Connection Errors

#### Error: "password authentication failed"

- Check `POSTGRES_PASSWORD` in `.env` matches what you're using
- Try resetting: `docker-compose down -v` then `docker-compose up -d`

#### Error: "database does not exist"

- Check `POSTGRES_DB` in `.env`
- Verify init.sql ran: `docker-compose logs postgres | grep init.sql`

### Redis Connection Errors

#### Error: "Could not connect to Redis"

- Check Redis is running: `docker-compose ps redis`
- Check logs: `docker-compose logs redis`
- Verify port: `docker exec -it ai-video-redis redis-cli PING`

### Container Health Issues

#### Check health status

```bash
docker-compose ps
```

#### Inspect unhealthy container

```bash
docker inspect ai-video-postgres | grep -A 10 Health
```

#### View health check logs

```bash
docker-compose logs postgres | grep health
```

### Performance Issues

#### Check resource usage

```bash
docker stats
```

#### Increase Docker resources

1. Open Docker Desktop
2. Settings → Resources
3. Increase Memory/CPU allocation
4. Apply & Restart

### Data Persistence Issues

#### Verify volumes exist

```bash
docker volume ls | grep delicious-lotus
```

You should see:
- `delicious-lotus_postgres_data`
- `delicious-lotus_redis_data`
- `delicious-lotus_backend_uploads`
- `delicious-lotus_backend_outputs`

#### Inspect volume

```bash
docker volume inspect delicious-lotus_postgres_data
```

---

## Environment Variables Reference

### Required Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `ai_video_pipeline` | Database name |
| `POSTGRES_USER` | `ai_video_user` | Database user |
| `POSTGRES_PASSWORD` | `dev_password_change_me` | Database password |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `REDIS_PORT` | `6379` | Redis port |
| `BACKEND_PORT` | `8000` | Backend API port |
| `REPLICATE_API_TOKEN` | - | Replicate API key for AI models |
| `AWS_ACCESS_KEY_ID` | - | AWS access key (optional) |
| `AWS_SECRET_ACCESS_KEY` | - | AWS secret key (optional) |

See `.env.example` for complete list.

---

## Next Steps

### After Setup is Complete

1. **Wait for Backend Structure**
   - Backend team is creating the FastAPI application structure
   - PR-D002 will add the actual backend Dockerfile and code

2. **Frontend Development**
   - Frontend will be built separately using Vite
   - Build output will be served by the backend in production

3. **Development Workflow**
   - Keep Docker services running while developing
   - Backend/frontend code changes will hot-reload (once implemented)
   - Database schema changes require rebuild: `docker-compose down -v && docker-compose up -d`

### Useful Commands Cheat Sheet

```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything
docker-compose down

# Restart a service
docker-compose restart postgres

# Access PostgreSQL
docker exec -it ai-video-postgres psql -U ai_video_user -d ai_video_pipeline

# Access Redis
docker exec -it ai-video-redis redis-cli

# Check service status
docker-compose ps

# View resource usage
docker stats
```

---

## Additional Resources

### Documentation

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [FastAPI Documentation](https://backend-api.tiangolo.com/)

### Project Documentation

- [Product Requirements Document](./prd.md)
- [Task List - DevOps](./task-list-devops.md)
- [Architecture Diagram](./architecture.md) (coming soon)
- [Deployment Guide](./deployment-guide.md) (coming soon)

### Getting Help

- Check [Troubleshooting](#troubleshooting) section above
- Review logs: `docker-compose logs`
- Ask the development team
- Create an issue in the repository

---

## Notes

### Current Limitations

1. **Backend Service:** Currently shows a placeholder message until backend team provides FastAPI structure (PR-D002)
2. **Celery Worker:** Placeholder until task queue implementation
3. **Local Storage:** Uses local volumes instead of S3 when AWS credentials not provided

### Security Notes for Local Development

- Default passwords are intentionally simple for local development
- **NEVER use these credentials in production**
- `.env` file is in `.gitignore` - never commit it
- For production deployment, use strong passwords and secrets management

### Performance Notes

- First startup takes longer (downloads images, initializes database)
- Subsequent startups are much faster
- Database and Redis data persist across restarts
- Volumes can grow large - clean up periodically with `docker-compose down -v`

---

**Last Updated:** 2025-11-14
**Version:** 1.0.0 (MVP)
**Maintained by:** DevOps Team
