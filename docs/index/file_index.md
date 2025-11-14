# File Index - AI Backend & Gateway

This index tracks all files created during the AI Backend development process.

## FastAPI Backend Files

### Core Application Files
- `fastapi/app/main.py` - Main FastAPI application with lifespan management and middleware
- `fastapi/app/core/config.py` - Application configuration settings
- `fastapi/app/core/logging.py` - Logging configuration with request ID tracking
- `fastapi/app/core/errors.py` - Global exception handlers and error responses

### API Routes
- `fastapi/app/api/routes/v1.py` - Public API v1 endpoints for video generation
- `fastapi/app/api/routes/internal_v1.py` - Internal API v1 endpoints for FFmpeg integration (PR #004)

### Data Models
- `fastapi/app/models/schemas.py` - Pydantic models and schemas for all API endpoints

### Tests
- `fastapi/tests/test_basic.py` - Basic application tests
- `fastapi/tests/test_v1_routes.py` - Tests for public API v1 endpoints
- `fastapi/tests/test_internal_routes.py` - Tests for internal API v1 endpoints (PR #004)

## Documentation Files

### Project Requirements
- `docs/prd.md` - Product Requirements Document
- `docs/prd-edited.md` - Edited version of PRD with updates
- `docs/ai-backend-prd.md` - AI Backend specific requirements
- `docs/ffmpeg-backend-prd.md` - FFmpeg Backend requirements
- `docs/api-specification.md` - API specification document
- `docs/api-specification-edited.md` - Edited API specification

### Task Management
- `docs/ai-backend-tasks-list.md` - Detailed task breakdown for AI backend
- `docs/task-list-devops.md` - DevOps task list
- `docs/task-list-frontend.md` - Frontend task list

### Memory Bank
- `docs/memory/projectbrief.md` - Project brief and foundation (pending)
- `docs/memory/productContext.md` - Product context and goals (pending)
- `docs/memory/activeContext.md` - Current work status and focus
- `docs/memory/systemPatterns.md` - System architecture decisions
- `docs/memory/techContext.md` - Technology stack and constraints
- `docs/memory/progress.md` - Implementation progress and status

### Setup and Deployment
- `docs/local-setup.md` - Local development environment setup

## Infrastructure Files

### Docker
- `docker/docker-compose.yml` - Local development environment
- `docker/postgres/init.sql` - Database initialization
- `docker/redis/redis.conf` - Redis configuration

### FastAPI Backend
- `fastapi/requirements.txt` - Python dependencies
- `fastapi/README.md` - Backend documentation
- `backend/Dockerfile.dev` - Development Docker configuration

## Frontend Files

### React Application
- `frontend/package.json` - Node.js dependencies
- `frontend/vite.config.ts` - Vite build configuration
- `frontend/tsconfig.json` - TypeScript configuration
- `frontend/eslint.config.js` - ESLint configuration

## Agent Coordination

### Identity Management
- `.claude/agent-identity.lock` - Agent identity tracking

### Commits
- `commits/Orange/` - Orange agent commit records
- `fastapi/commits/Orange/` - Backend-specific Orange commits
- `commits/Blonde/` - Blonde agent commit records (PR #004)

## Root Files

- `LICENSE` - Project license
- `README.md` - Project overview (pending)
