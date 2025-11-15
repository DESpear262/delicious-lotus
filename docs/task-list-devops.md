# Task List - DevOps Track
## AI Video Generation Pipeline

### Overview
This task list covers infrastructure, deployment, and operational concerns for the video generation pipeline. Team 1 (DevOps + Frontend) is responsible for these tasks.

**MVP Focus:** Ad Creative Pipeline (15-60 seconds) only
**Post-MVP:** Add Music Video Pipeline (1-3 minutes) support
**Timeline:** 48 hours to MVP, 8 days total

**DEPLOYMENT DECISION (Task 2.5):** Option B - FastAPI serves static frontend files (single container deployment)

---

## PR Status Summary

**Completed:** 5/10 ✅
**Unblocked (Ready to Start):** 5 🎯
**Blocked (Dependencies Not Met):** 0
**Total Remaining:** 5 PRs (~12-13 hours)

---

## Currently Unblocked PRs

**READY TO START (5 PRs):**
1. **PR-D009: Deployment Documentation** (2h) - Create deployment guide, architecture docs, troubleshooting, cost tracking, and scaling docs
2. **PR-D004: CI/CD Pipeline** (2-3h) - GitHub Actions workflows for automated deployment, testing, and security scanning
3. **PR-D006: Monitoring & Observability** (2h) - CloudWatch dashboards, alarms, logging configuration, and application instrumentation
4. **PR-D007: Load Testing & Performance** (3h) - Locust load tests, performance benchmarks, and optimization tuning
5. **PR-D008: Security Hardening** (3h) - Security audit, vulnerability scanning, secrets management, and compliance documentation

**See detailed plans for each PR below** ↓

---

### PR-D001: Local Development Environment (Task 1)
**Status:** Complete ✅ | **Est:** 2 hours | **Completed by:** Orange
- Docker Compose for local dev (PostgreSQL 16, Redis 7, placeholder services)
- Production-ready database schema (9 tables, views, triggers, helper functions)
- Comprehensive environment variables (60+ documented)
- Files: `docker-compose.yml`, `.env.example`, `docs/local-setup.md`, `docker/postgres/init.sql`, `docker/redis/redis.conf`, `backend/Dockerfile.dev`, `backend/README.md`
- Commit: b020358

### PR-D003: Storage Architecture Documentation (Task 6 - doc only)
**Status:** Complete ✅ | **Est:** 1 hour | **Completed by:** White
**Dependencies:** None
**Description:** Document S3 bucket structure, lifecycle policies, and IAM permissions. Actual AWS resource creation will be done by user when credentials available.

**Files Created:**
- `docs/storage-architecture.md` - Comprehensive S3 architecture, lifecycle policies, IAM permissions, presigned URLs, CORS config, cost optimization, local dev setup

**Acceptance Criteria:**
- [x] S3 bucket structure documented (uploads/, generations/, compositions/, temp/)
- [x] Lifecycle policies specified (7-day auto-delete for temp files, 30-day for generations, 90-day for compositions)
- [x] IAM permissions documented (least privilege for ECS tasks)
- [x] Presigned URL generation approach documented (with code examples)
- [x] CORS configuration for direct uploads (with JSON config)
- [x] Cost optimization strategies documented (7 strategies with estimates)
- [x] Environment variables defined in .env.example (already comprehensive, no additions needed)

**Implementation Notes:**
- Focus on documentation only - no actual AWS resources
- Coordinate with backend team on file paths and naming conventions
- Consider both local development (filesystem) and production (S3) scenarios

### PR-D005: Environment Configuration Templates (Task 8)
**Status:** Complete ✅ | **Est:** 2 hours | **Completed by:** Orange
**Dependencies:** None
**Description:** Create comprehensive environment configuration templates for dev and production environments with all required secrets and settings.

**Files Created/Modified:**
- ✅ `deploy/env.dev.template` - Development environment template
- ✅ `deploy/env.prod.template` - Production environment template
- ✅ `docs/environment-setup.md` - Configuration guide and variable reference
- ✅ `backend/app/config/settings.py` - Settings management structure
- ✅ `backend/app/config/__init__.py` - Config module initialization
- ✅ `backend/app/__init__.py` - App initialization
- ✅ `.gitignore` - Fixed to exclude actual .env files

**Commit:** 1215253

**Acceptance Criteria (All Met):**
- ✅ All environment variables documented with descriptions
- ✅ Templates for Replicate API keys (placeholder format)
- ✅ Templates for database connection strings (dev/prod)
- ✅ Templates for Redis configuration (dev/prod)
- ✅ CORS settings for Option B single-domain deployment
- ✅ AWS credentials templates (S3, ECR, ECS)
- ✅ Security settings (secrets, JWT keys, etc.)
- ✅ Feature flags for MVP vs post-MVP features
- ✅ Secrets management approach documented
- ✅ Clear instructions on how to populate actual values

### PR-D009: Deployment Documentation (Task 13)
**Status:** Unblocked | **Est:** 2 hours | **Agent:** Available
**Dependencies:** None (can document in parallel with implementation)
**Description:** Create comprehensive deployment, architecture, and troubleshooting documentation for the entire system.

**Files to Create:**
- `docs/deployment-guide.md` - Step-by-step deployment procedures
- `docs/architecture.md` - System architecture diagram and explanation
- `docs/troubleshooting.md` - Common issues and solutions
- `docs/cost-tracking.md` - AWS cost tracking and optimization
- `docs/scaling.md` - Post-MVP scaling recommendations

**Detailed Acceptance Criteria:**

**1. deployment-guide.md** - Complete deployment runbook
- [ ] Prerequisites checklist (AWS CLI, Docker, Terraform, credentials)
- [ ] First-time deployment walkthrough:
  - [ ] AWS account setup
  - [ ] Terraform initialization (`terraform init`)
  - [ ] Variable configuration (`terraform.tfvars`)
  - [ ] Infrastructure deployment (`terraform apply`)
  - [ ] Database initialization (`./scripts/migrate-db.sh init`)
- [ ] Update/redeployment procedures:
  - [ ] Code changes deployment (`./scripts/deploy.sh apply`)
  - [ ] Database migrations (`./scripts/migrate-db.sh migrate`)
  - [ ] Configuration updates (environment variables)
- [ ] Rollback procedures:
  - [ ] ECS task rollback (previous task definition)
  - [ ] Database rollback (migration down)
  - [ ] Terraform state management
- [ ] Health check verification steps
- [ ] Post-deployment validation checklist

**2. architecture.md** - System design documentation
- [ ] High-level architecture diagram (ASCII art or Mermaid)
  - [ ] Frontend (React/Vite served by FastAPI)
  - [ ] Backend (FastAPI on ECS Fargate)
  - [ ] AI Services (Replicate API integration)
  - [ ] FFmpeg Backend (video composition)
  - [ ] Data stores (PostgreSQL RDS, Redis ElastiCache, S3)
- [ ] Component interaction flowcharts:
  - [ ] Video generation flow (request → AI → clips → composition)
  - [ ] WebSocket real-time updates
  - [ ] Asset upload and storage
- [ ] Network architecture:
  - [ ] VPC configuration (public/private subnets)
  - [ ] Security groups and firewall rules
  - [ ] Service communication patterns
- [ ] Data flow diagrams:
  - [ ] Request lifecycle
  - [ ] Database schema relationships (reference init.sql)
  - [ ] S3 storage structure (reference storage-architecture.md)
- [ ] Technology stack breakdown by component
- [ ] Deployment model (Option B: single container, static files)

**3. troubleshooting.md** - Operational playbook
- [ ] Container startup failures:
  - [ ] ECS task won't start → Check logs in CloudWatch
  - [ ] Health check failing → Verify /health endpoint
  - [ ] Out of memory → Increase task memory allocation
- [ ] Database connection issues:
  - [ ] Connection refused → Security group rules
  - [ ] Timeout → VPC/subnet configuration
  - [ ] Too many connections → Connection pool tuning
- [ ] S3 access problems:
  - [ ] Access denied → IAM role permissions
  - [ ] Slow uploads → Network/NAT gateway issues
  - [ ] Lifecycle policy not working → Policy syntax/timing
- [ ] Frontend not loading:
  - [ ] Static files 404 → Build output directory mismatch
  - [ ] CORS errors → Should not occur with Option B
  - [ ] Blank page → Check browser console, API endpoints
- [ ] API errors:
  - [ ] 500 errors → Check CloudWatch logs
  - [ ] 503 errors → Service not running or unhealthy
  - [ ] Timeout → Long-running generation jobs (expected)
- [ ] Common commands:
  - [ ] View ECS task logs
  - [ ] Connect to RDS (via migration task)
  - [ ] Invalidate caches
  - [ ] Restart services

**4. cost-tracking.md** - Financial management
- [ ] Monthly cost breakdown (from PR-D010 infrastructure):
  - [ ] RDS PostgreSQL: ~$12/month (db.t4g.micro)
  - [ ] ElastiCache Redis: ~$11/month (cache.t4g.micro)
  - [ ] ECS Fargate: ~$15/month (1 task, 1 vCPU, 2GB RAM)
  - [ ] S3 Storage: ~$1-5/month (with lifecycle policies)
  - [ ] ECR: ~$1/month (image storage)
  - [ ] CloudWatch: ~$0-5/month (basic logging)
  - [ ] **Total: $40-50/month**
- [ ] Cost tracking spreadsheet template:
  - [ ] Daily cost tracking
  - [ ] Per-service breakdown
  - [ ] Budget vs. actual
  - [ ] Replicate API costs (separate tracking)
- [ ] Cost optimization strategies:
  - [ ] S3 lifecycle policies (already implemented: 7/30/90 day auto-delete)
  - [ ] RDS/ElastiCache instance sizing (start small, scale up)
  - [ ] ECS task count optimization (1 task for MVP)
  - [ ] Smart caching to reduce AI API calls
  - [ ] Spot instances for non-critical workloads (future)
- [ ] Budget alerts setup instructions (AWS Budgets)
- [ ] Cost anomaly detection setup

**5. scaling.md** - Growth strategy
- [ ] Post-MVP scaling recommendations:
  - [ ] Horizontal scaling:
    - [ ] ECS service auto-scaling (CPU/memory targets)
    - [ ] Multi-task deployment (3-5 tasks)
    - [ ] Application Load Balancer (ALB) addition
  - [ ] Vertical scaling:
    - [ ] RDS instance upgrade path (t4g.micro → t4g.small → t4g.medium)
    - [ ] ElastiCache cluster mode
    - [ ] ECS task CPU/memory increases
  - [ ] Database optimization:
    - [ ] Read replicas for heavy read workloads
    - [ ] Connection pooling tuning (PgBouncer)
    - [ ] Query optimization and indexing
  - [ ] Caching strategies:
    - [ ] Redis caching for repeated prompts
    - [ ] S3 + CloudFront CDN for video delivery
    - [ ] API response caching
- [ ] Traffic projections and capacity planning:
  - [ ] Current capacity: 5 concurrent users
  - [ ] Target capacity: 50+ concurrent users
  - [ ] Bottleneck analysis (likely: AI API rate limits)
- [ ] Multi-region deployment considerations (future)
- [ ] Database sharding strategy (if needed for high volume)
- [ ] When to scale checklist (CPU >70%, latency >1s, queue depth >10)

**Implementation Notes:**
- Reference existing documentation (local-setup.md, storage-architecture.md, environment-setup.md)
- Include links to AWS documentation for specific services
- Add placeholder sections for Music Video Pipeline (post-MVP feature)
- Keep language clear and operational (targeted at DevOps/SRE teams)
- Include real examples from deployed infrastructure

### PR-D010: AWS Infrastructure Deployment (Tasks 2, 4, 5)
**Status:** Complete ✅ | **Est:** 6 hours | **Completed by:** White
**Dependencies:** None
**Description:** Complete AWS infrastructure deployment using Terraform, including all core services, database initialization, and deployment automation scripts.

**Files Created:**
- ✅ `terraform/` - Complete Terraform infrastructure as code
  - `main.tf` - Main orchestration with 8 modules
  - `variables.tf` - All configurable parameters
  - `outputs.tf` - Resource endpoints and connection strings
  - `terraform.tfvars.example` - Configuration template
  - `modules/ecr/` - Container registry
  - `modules/s3/` - Storage bucket with lifecycle policies
  - `modules/rds/` - PostgreSQL 17 database
  - `modules/elasticache/` - Redis 7 cache
  - `modules/ecs/` - Fargate cluster and service
  - `modules/iam/` - Roles and policies
  - `modules/security/` - Security groups
  - `modules/cloudwatch/` - Logging
- ✅ `scripts/deploy.sh` - Automated deployment script
- ✅ `scripts/migrate-db.sh` - Database migration script
- ✅ `backend/migrations/` - Migration directory structure
- ✅ `backend/migrations/README.md` - Migration guidelines
- ✅ `backend/init_db.py` - Database initialization helper
- ✅ `docs/DATABASE_INITIALIZATION.md` - Database setup guide
- ✅ `README.md` - Project documentation with deployment instructions

**Infrastructure Deployed:**
- ✅ ECR Repository (Docker images)
- ✅ S3 Bucket (video storage, lifecycle policies: 7/30/90 day auto-delete)
- ✅ RDS PostgreSQL 17 (db.t4g.micro, 20GB, VPC-secured)
- ✅ ElastiCache Redis 7 (cache.t4g.micro, VPC-secured)
- ✅ ECS Fargate Cluster (1 task, 1 vCPU, 2GB RAM)
- ✅ Security Groups (VPC-only database access)
- ✅ IAM Roles (least privilege: execution + task roles)
- ✅ CloudWatch Logs (7-day retention)

**Database Schema:**
- ✅ 9 tables initialized (user_sessions, generation_jobs, clips, compositions, brand_assets, task_queue, job_metrics, system_config, schema_migrations)
- ✅ Multiple indexes for performance
- ✅ 2 views (active_jobs, job_summary)
- ✅ 3 functions (cleanup utilities, status updates)
- ✅ 1 trigger (auto-update timestamps)
- ✅ Default configuration inserted
- ✅ Schema version tracking enabled

**Acceptance Criteria (All Met):**
- ✅ All AWS resources provisioned in us-east-2
- ✅ Docker image built and pushed to ECR
- ✅ ECS service running and healthy
- ✅ Database schema fully initialized
- ✅ Redis cluster operational
- ✅ S3 bucket with lifecycle policies configured
- ✅ Security groups properly configured (VPC-only access)
- ✅ IAM roles with least privilege
- ✅ CloudWatch logging enabled
- ✅ Deployment automation scripts created
- ✅ Database migration framework established
- ✅ Complete documentation provided
- ✅ Monthly cost ~$30-50 (optimized)

**Monthly Cost:** ~$30-50 USD
- RDS: ~$12/month
- ElastiCache: ~$11/month
- ECS Fargate: ~$15/month
- S3 + ECR + CloudWatch: ~$2-12/month

**Implementation Notes:**
- Used Terraform for infrastructure as code
- Database secured in VPC (not publicly accessible)
- Database initialization via one-off ECS task (runs in VPC)
- Deployment scripts handle build → push → deploy workflow
- Migration framework ready for schema evolution
- All secrets in terraform.tfvars (gitignored)

### PR-D002: Backend Docker Container Configuration (Task 3)
**Status:** Complete ✅ | **Est:** 3 hours | **Completed by:** White
**Dependencies:** Task 1 (Complete ✅), Task 2.5 (Complete ✅)
**Description:** Create production-ready Dockerfile for Python FastAPI backend with FFmpeg support, optimized for Option B (static file serving).

**Files to Create:**
- `fastapi/Dockerfile` - Multi-stage production build
- `fastapi/.dockerignore` - Exclude unnecessary files from build context
- `fastapi/docker-compose.test.yml` - Local testing configuration
- `scripts/build-backend.sh` - Build script for local and CI use
- `scripts/test-backend.sh` - Testing script
- `docs/docker-backend.md` - Documentation

**Acceptance Criteria:**
- [ ] Multi-stage Dockerfile (builder + runtime stages)
- [ ] Python 3.13 with venv
- [ ] FFmpeg installed and verified (ffmpeg -version)
- [ ] All requirements.txt dependencies installed
- [ ] FastAPI app configured to serve static files from /frontend/dist
- [ ] Health check endpoint configured
- [ ] Image size optimized (<500MB target)
- [ ] Non-root user for security
- [ ] Proper logging to stdout
- [ ] Works with docker-compose.yml from PR-D001
- [ ] Test scripts verify container starts and responds to health checks
- [ ] Documentation covers build, run, and troubleshooting

**Implementation Notes:**
- Base image: python:3.13-slim (balance size/compatibility)
- Install FFmpeg from Debian repos
- Copy frontend/dist/* to /app/frontend/dist (static serving)
- Use .dockerignore to exclude .git, node_modules, __pycache__, *.pyc
- Set working directory to /app
- Expose port 8000 (FastAPI default)
- CMD: uvicorn app.main:app --host 0.0.0.0 --port 8000
- Add HEALTHCHECK instruction with /health endpoint

**All DevOps PRs Now Unblocked!** ✅
All dependencies have been satisfied. The following PRs are ready to start:
- PR-D004: CI/CD Pipeline (Task 7) - 2-3h
- PR-D006: Monitoring & Observability (Task 9) - 2h
- PR-D007: Load Testing & Performance (Task 10) - 3h
- PR-D008: Security Hardening (Task 12) - 3h
- PR-D009: Deployment Documentation (Task 13) - 2h

**User Tasks** (require AWS credentials):
- Task 2: AWS Account Setup and IAM
- Task 4: ECS Infrastructure
- Task 5: Database Infrastructure

---

## Phase 1: MVP Infrastructure (Hours 0-24)

### Task 1: Local Development Environment Setup
**Priority:** Critical
**Estimated Time:** 2 hours
**Dependencies:** None

**Subtasks:**
- [ ] Create Docker Compose configuration for local development
- [ ] Set up PostgreSQL container with initial schema
- [ ] Set up Redis container for job queuing
- [ ] Create environment variable template (.env.example)
- [ ] Write local development setup documentation
- [ ] Test full stack runs locally with all 4 services

**Deliverables:**
- `docker-compose.yml` for local dev
- `.env.example` with all required variables
- `docs/local-setup.md` instructions

---

### Task 2: AWS Account Setup and IAM Configuration
**Priority:** Critical
**Estimated Time:** 2 hours
**Dependencies:** None

**Subtasks:**
- [ ] Create/configure AWS account for project
- [ ] Set up IAM user for deployment with minimal required permissions
- [ ] Configure S3 bucket for video/asset storage
- [ ] Set up ECR (Elastic Container Registry) for Docker images
- [ ] Create secrets in .env file for local development
- [ ] Document AWS resource names and configurations

**Deliverables:**
- AWS resources provisioned
- IAM policy documentation
- S3 bucket with proper CORS configuration

---

### Task 2.5: Frontend Deployment Decision
**Priority:** Critical
**Estimated Time:** 1 hour
**Dependencies:** None

**Decision Point:** Choose frontend deployment approach before proceeding with infrastructure.

**Options:**

**Option A: Vercel Deployment (RECOMMENDED FOR MVP)**
- **Pros:** Simplest setup, no Docker needed, automatic CI/CD, edge caching
- **Cons:** Requires CORS configuration, separate deployment
- **Effort:** Minimal (2 hours setup)
- **Best for:** Fast MVP iteration

**Option B: FastAPI Serves Static Files**
- **Pros:** Single container, simpler CORS, unified deployment
- **Cons:** Backend handles static file serving, less separation of concerns
- **Effort:** Low (add static file mounting to backend)
- **Best for:** Simplicity, single service

**Note:** Option C (separate nginx container in ECS) has been ruled out as unnecessarily complex for this project.

**Decision Required:**
- [ ] Choose deployment approach (document in this task)
- [ ] Update subsequent tasks based on decision
- [ ] Inform frontend team of deployment target

**Deliverables:**
- Documented deployment decision
- Updated task list reflecting chosen approach

---

### Task 3: Backend Docker Container Configuration
**Priority:** Critical
**Estimated Time:** 3 hours
**Dependencies:** Task 1, Task 2.5

**Subtasks:**
- [ ] Create Dockerfile for Python backend (FastAPI + FFmpeg)
- [ ] Create multi-stage build for optimization
- [ ] Ensure FFmpeg is properly installed in backend container
- [ ] Configure Python 3.13 with venv in container
- [ ] **If Option B chosen:** Add static file serving capability to backend
- [ ] Optimize image size (target <500MB)
- [ ] Test backend container locally

**Deliverables:**
- `backend/Dockerfile`
- `backend/docker-compose.test.yml` for local testing
- Build and test scripts

**Note:** Frontend deployment handled separately based on Task 2.5 decision

---

### Task 4: ECS Infrastructure Setup
**Priority:** Critical
**Estimated Time:** 4 hours
**Dependencies:** Tasks 2, 2.5, 3

**Subtasks:**
- [ ] Create ECS cluster with Fargate
- [ ] Write task definition for backend service
- [ ] Set up CloudWatch log groups (basic logging only)
- [ ] Configure task networking (no ALB per requirements)
- [ ] Set up direct task IP access
- [ ] **If Option B chosen:** Configure backend to serve frontend static files

**Deliverables:**
- `deploy/ecs-task-backend.json`
- `deploy/ecs-service-config.json`
- Deployment documentation
- **If Option A:** Document CORS configuration for Vercel

---

### Task 5: Database Infrastructure
**Priority:** Critical
**Estimated Time:** 3 hours
**Dependencies:** Task 2

**Subtasks:**
- [ ] Create RDS PostgreSQL instance (smallest tier for MVP)
- [ ] Configure security groups for ECS access
- [ ] Create initial database and schema
- [ ] Set up connection pooling configuration
- [ ] Create ElastiCache Redis cluster (smallest tier)
- [ ] Test connectivity from ECS tasks

**Deliverables:**
- RDS instance running
- Redis cluster running
- Database connection strings in .env

---

### Task 6: Storage Configuration
**Priority:** Critical
**Estimated Time:** 2 hours
**Dependencies:** Task 2

**Subtasks:**
- [ ] Configure S3 bucket structure (uploads/, generations/, compositions/)
- [ ] Set up lifecycle policies for temporary files (auto-delete after 7 days)
- [ ] Configure IAM roles for ECS tasks to access S3
- [ ] Set up presigned URL generation for downloads
- [ ] Test upload/download from ECS tasks

**Deliverables:**
- S3 bucket with proper structure
- IAM policies for S3 access
- Lifecycle policies configured

---

### Task 6A: Frontend Deployment Setup - Option A (Vercel)
**Priority:** Critical (if Option A chosen)
**Estimated Time:** 2 hours
**Dependencies:** Task 2.5 (if Option A chosen)

**Execute only if Vercel deployment chosen in Task 2.5**

**Subtasks:**
- [ ] Create Vercel account and connect to GitHub repo
- [ ] Configure Vercel project for frontend directory
- [ ] Set up environment variables in Vercel
- [ ] Configure API endpoint to point to ECS backend
- [ ] Set up CORS in backend to allow Vercel domain
- [ ] Test deployment and API connectivity

**Deliverables:**
- Frontend deployed to Vercel
- CORS configuration documented
- Vercel deployment URL

---

### Task 6B: Frontend Deployment Setup - Option B (FastAPI Static)
**Priority:** Critical (if Option B chosen)
**Estimated Time:** 1 hour
**Dependencies:** Task 2.5 (if Option B chosen), Task 3

**Execute only if FastAPI static serving chosen in Task 2.5**

**Subtasks:**
- [ ] Add static file mounting to FastAPI application
- [ ] Configure frontend build output directory
- [ ] Set up build step in backend Docker container
- [ ] Test static file serving locally
- [ ] Document build and deployment process

**Deliverables:**
- FastAPI configured to serve static files
- Frontend build integrated into backend container
- Single deployment artifact

---

## Phase 2: MVP Deployment (Hours 24-36)

### Task 7: CI/CD Pipeline Setup (PR-D004)
**Priority:** High
**Estimated Time:** 2-3 hours (varies by Task 2.5 decision)
**Dependencies:** Tasks 3, 4, and 6A/6B (based on choice) - ALL COMPLETE ✅
**Status:** UNBLOCKED

**Description:** Implement GitHub Actions workflows for automated build, test, and deployment of the FastAPI backend to AWS ECS.

**Files to Create:**
- `.github/workflows/deploy-backend.yml` - Main deployment workflow
- `.github/workflows/pr-checks.yml` - Pull request validation
- `.github/workflows/test.yml` - Automated testing

**Detailed Acceptance Criteria:**

**1. deploy-backend.yml** - Production deployment
- [ ] Triggers:
  - [ ] Push to `main` branch
  - [ ] Manual workflow dispatch (for emergency deploys)
- [ ] Build job:
  - [ ] Checkout code
  - [ ] Setup Docker Buildx
  - [ ] Cache Docker layers for faster builds
  - [ ] Build image from `fastapi/Dockerfile`
  - [ ] Tag with commit SHA and `latest`
- [ ] Test job:
  - [ ] Run pytest suite (`fastapi/tests/`)
  - [ ] Code coverage reporting
  - [ ] Lint checks (black, flake8, mypy)
  - [ ] Fail pipeline if tests fail
- [ ] Push job (only if tests pass):
  - [ ] Login to AWS ECR
  - [ ] Push image to ECR repository
  - [ ] Update image tags
- [ ] Deploy job:
  - [ ] Update ECS task definition with new image
  - [ ] Deploy to ECS service (force new deployment)
  - [ ] Wait for deployment to stabilize
  - [ ] Run health checks (`/health` endpoint)
  - [ ] Rollback if health checks fail
- [ ] Notifications:
  - [ ] Deployment success/failure (GitHub Actions summary)
  - [ ] Optional: Slack/email notifications
- [ ] Secrets configuration (GitHub Secrets):
  - [ ] `AWS_ACCESS_KEY_ID`
  - [ ] `AWS_SECRET_ACCESS_KEY`
  - [ ] `AWS_REGION` (us-east-2)
  - [ ] `ECR_REPOSITORY` name
  - [ ] `ECS_CLUSTER` name
  - [ ] `ECS_SERVICE` name

**2. pr-checks.yml** - Pull request validation
- [ ] Triggers:
  - [ ] Pull request opened, synchronized, reopened
  - [ ] Target branch: `main`
- [ ] Code quality job:
  - [ ] Run black (code formatting check)
  - [ ] Run flake8 (linting)
  - [ ] Run mypy (type checking)
  - [ ] Fail PR if quality checks fail
- [ ] Test job:
  - [ ] Setup Python 3.13
  - [ ] Install dependencies (`requirements.txt`)
  - [ ] Run pytest with coverage
  - [ ] Minimum coverage: 80% (configurable)
  - [ ] Upload coverage report as artifact
- [ ] Build validation:
  - [ ] Build Docker image (no push)
  - [ ] Ensure image builds successfully
  - [ ] Check image size (warn if >500MB)
- [ ] PR status:
  - [ ] Block merge if checks fail
  - [ ] Add status check badges to PR

**3. test.yml** - Automated testing
- [ ] Test matrix:
  - [ ] Python versions: 3.13 (primary), 3.12 (compatibility)
  - [ ] OS: ubuntu-latest (Linux for Docker compat)
- [ ] Unit tests:
  - [ ] Run all tests in `fastapi/tests/`
  - [ ] Parallel test execution for speed
  - [ ] Generate JUnit XML report
- [ ] Integration tests (if available):
  - [ ] Spin up test dependencies (PostgreSQL, Redis via docker-compose.test.yml)
  - [ ] Run integration test suite
  - [ ] Clean up containers after
- [ ] Test artifacts:
  - [ ] Upload coverage reports
  - [ ] Upload test results
  - [ ] Store for 30 days

**4. Deployment automation**
- [ ] Configure AWS credentials in GitHub Secrets
- [ ] ECR repository authentication (AWS CLI in workflow)
- [ ] ECS service update strategy:
  - [ ] Rolling update (0 downtime)
  - [ ] Minimum healthy percent: 100%
  - [ ] Maximum percent: 200%
- [ ] Rollback mechanism:
  - [ ] Store previous task definition ARN
  - [ ] Revert on health check failure
  - [ ] Manual rollback workflow (optional)

**5. Documentation**
- [ ] Add CI/CD badge to README.md
- [ ] Document workflow triggers and jobs
- [ ] Secrets setup instructions
- [ ] Troubleshooting common CI/CD issues

**Implementation Notes:**
- Reference `ffmpeg-backend/.github/workflows/ci.yml` for workflow structure
- Use Docker layer caching to speed up builds (GitHub Actions cache)
- Consider using AWS OIDC for GitHub Actions (more secure than long-lived keys)
- Add workflow status badges to README
- Keep workflows fast (<5 minutes for PR checks, <10 minutes for deploy)

---

### Task 8: Environment Configuration Management
**Priority:** High
**Estimated Time:** 2 hours
**Dependencies:** Task 4

**Subtasks:**
- [ ] Create .env files for each environment (dev, prod)
- [ ] Configure Replicate API keys in task definitions
- [ ] Set up database connection strings
- [ ] Configure Redis connection parameters
- [ ] Set up CORS and API endpoints
- [ ] Document all environment variables

**Deliverables:**
- Environment configuration documented
- All services can communicate
- Secrets properly managed

---

### Task 9: Monitoring and Logging (PR-D006)
**Priority:** Medium
**Estimated Time:** 2 hours
**Dependencies:** Task 4 - COMPLETE ✅ (ECS deployed via PR-D010)
**Status:** UNBLOCKED

**Description:** Implement CloudWatch-based monitoring, alerting, and logging for operational visibility.

**Files to Create:**
- `docs/monitoring.md` - Monitoring setup and dashboards
- `terraform/modules/cloudwatch/dashboards.tf` - CloudWatch dashboard definitions
- `terraform/modules/cloudwatch/alarms.tf` - CloudWatch alarms
- `terraform/modules/cloudwatch/outputs.tf` - Dashboard and alarm outputs

**Detailed Acceptance Criteria:**

**1. CloudWatch Dashboards**
- [ ] **Application Dashboard:**
  - [ ] ECS metrics:
    - [ ] CPU utilization (per task and service average)
    - [ ] Memory utilization
    - [ ] Task count (running, pending, stopped)
    - [ ] Network I/O
  - [ ] Application metrics:
    - [ ] API request rate (requests/minute)
    - [ ] API error rate (4xx, 5xx)
    - [ ] Response time (p50, p95, p99)
    - [ ] Active generation jobs
  - [ ] Custom metrics (if implemented):
    - [ ] Video generation queue depth
    - [ ] Generation success/failure rate
    - [ ] Average generation time

- [ ] **Infrastructure Dashboard:**
  - [ ] RDS PostgreSQL:
    - [ ] CPU utilization
    - [ ] Database connections
    - [ ] Storage space used
    - [ ] Read/write IOPS
    - [ ] Replication lag (if read replicas exist)
  - [ ] ElastiCache Redis:
    - [ ] CPU utilization
    - [ ] Memory usage
    - [ ] Cache hit rate
    - [ ] Evictions
    - [ ] Connection count
  - [ ] S3 Bucket:
    - [ ] Storage used (by class: temp, generations, compositions)
    - [ ] Request rate (GET, PUT)
    - [ ] Data transfer (in/out)

- [ ] **Cost Dashboard:**
  - [ ] Estimated monthly costs by service
  - [ ] S3 storage costs (by lifecycle tier)
  - [ ] ECS task running hours
  - [ ] RDS/ElastiCache uptime

**2. CloudWatch Alarms** (Email notifications via SNS)
- [ ] Critical alarms (immediate action required):
  - [ ] ECS service unhealthy (0 running tasks)
  - [ ] RDS CPU >90% for 5 minutes
  - [ ] RDS storage space <10% free
  - [ ] API error rate >10% for 5 minutes
  - [ ] ECS task stopped unexpectedly
- [ ] Warning alarms (investigate soon):
  - [ ] ECS CPU >70% for 10 minutes
  - [ ] ECS memory >80% for 10 minutes
  - [ ] RDS connections >80% of max
  - [ ] Redis memory >80%
  - [ ] API response time p95 >2 seconds
- [ ] Cost alarms:
  - [ ] Monthly cost >$60 (20% over budget)
  - [ ] S3 storage >50GB (unexpected growth)

**3. Logging Configuration**
- [ ] CloudWatch Log Groups:
  - [ ] `/ecs/fastapi-backend` - Application logs
  - [ ] `/ecs/migrations` - Database migration logs
  - [ ] `/aws/rds/postgresql` - Database slow queries (if enabled)
- [ ] Log retention policies:
  - [ ] Application logs: 7 days (MVP), 30 days (production)
  - [ ] Migration logs: 30 days
  - [ ] Database logs: 7 days
- [ ] Log insights queries (saved queries):
  - [ ] Error rate by endpoint
  - [ ] Slowest API endpoints
  - [ ] Failed generation jobs
  - [ ] Database connection errors
- [ ] Structured logging format (JSON):
  - [ ] Timestamp, level, message, request_id, user_id, context

**4. Application Instrumentation**
- [ ] Health check endpoint enhancements:
  - [ ] `/health` - Basic liveness check (200 OK)
  - [ ] `/health/detailed` - Dependency checks:
    - [ ] Database connectivity
    - [ ] Redis connectivity
    - [ ] S3 access
    - [ ] Replicate API reachability
  - [ ] Return 503 if any dependency is down
- [ ] Custom metrics (optional for MVP, recommended for production):
  - [ ] Publish to CloudWatch via boto3:
    - [ ] `VideoGeneration/QueueDepth` (jobs in queue)
    - [ ] `VideoGeneration/CompletionTime` (generation duration)
    - [ ] `VideoGeneration/SuccessRate` (successful vs failed)
    - [ ] `API/RequestCount` (by endpoint)

**5. Monitoring Documentation** (docs/monitoring.md)
- [ ] Dashboard access instructions (AWS Console links)
- [ ] Alarm response playbook:
  - [ ] What each alarm means
  - [ ] How to investigate (where to look)
  - [ ] Common resolutions
- [ ] Log query examples (CloudWatch Insights)
- [ ] Metrics explanation and thresholds
- [ ] On-call runbook (if team has on-call rotation)

**6. Terraform Integration**
- [ ] Update `terraform/modules/cloudwatch/` with:
  - [ ] Dashboard JSON definitions
  - [ ] Alarm configurations
  - [ ] SNS topic for email notifications
  - [ ] IAM permissions for ECS tasks to publish metrics
- [ ] Add CloudWatch module to `terraform/main.tf`
- [ ] Output dashboard URLs for easy access

**Implementation Notes:**
- Start with basic CloudWatch monitoring (no custom metrics for MVP)
- Use AWS Console to manually create dashboards, then export to Terraform
- Email alerts via SNS (simple email subscription)
- Consider AWS Chatbot for Slack alerts (post-MVP)
- Keep alarm thresholds conservative to avoid alert fatigue
- Test alarms by manually triggering conditions (stop ECS task, fill RDS disk)

---

### Task 10: Load Testing and Optimization (PR-D007)
**Priority:** Medium
**Estimated Time:** 3 hours
**Dependencies:** Tasks 7, 8 (deployment complete via PR-D010) - ALL COMPLETE ✅
**Status:** UNBLOCKED

**Description:** Create load testing scripts to validate performance under concurrent load and identify bottlenecks.

**Files to Create:**
- `tests/load/locustfile.py` - Locust load test scenarios
- `tests/load/k6-script.js` - k6 load test (alternative)
- `tests/load/test-data/prompts.json` - Sample prompts
- `tests/load/test-data/sample-logo.png` - Sample assets
- `tests/load/README.md` - Load testing guide
- `docs/performance.md` - Performance benchmarks and results

**Detailed Acceptance Criteria:**

**1. Load Testing Tool Setup** (Locust recommended)
- [ ] Install Locust (`pip install locust`)
- [ ] Configure test environment:
  - [ ] Target: Deployed ECS service (public IP or ALB if added)
  - [ ] Test data: Sample prompts, brand assets
  - [ ] Load profiles: Ramp-up, sustained, spike

**2. Test Scenarios** (tests/load/locustfile.py)
- [ ] **Scenario 1: API Health Check**
  - [ ] GET `/health` endpoint
  - [ ] Target: 100 requests/second
  - [ ] Expected: <50ms response time, 0% errors

- [ ] **Scenario 2: Video Generation Submission**
  - [ ] POST `/api/v1/generations` with valid prompt
  - [ ] Simulates user submitting new generation request
  - [ ] Load profile:
    - [ ] 5 concurrent users (MVP requirement)
    - [ ] 10 concurrent users (stress test)
    - [ ] 20 concurrent users (breaking point)
  - [ ] Success criteria:
    - [ ] 100% success rate at 5 users
    - [ ] <500ms API response time (job queued)
    - [ ] No database connection errors

- [ ] **Scenario 3: Generation Status Polling**
  - [ ] GET `/api/v1/generations/{id}` (status check)
  - [ ] Simulates users polling for progress
  - [ ] Load profile: 10 users polling every 5 seconds
  - [ ] Success criteria: <200ms response time

- [ ] **Scenario 4: WebSocket Connections**
  - [ ] Connect to `/ws/generations/{id}`
  - [ ] Maintain connection for 5 minutes
  - [ ] Test connection stability and reconnection
  - [ ] Load profile: 5 concurrent WebSocket connections
  - [ ] Success criteria: No unexpected disconnections

- [ ] **Scenario 5: Asset Upload**
  - [ ] POST `/api/v1/assets/upload` with 5MB image
  - [ ] Test file upload performance
  - [ ] Load profile: 3 concurrent uploads
  - [ ] Success criteria: <10s upload time

- [ ] **Scenario 6: End-to-End Workflow** (realistic user journey)
  - [ ] Submit generation request
  - [ ] Poll status until complete (or timeout at 10 minutes)
  - [ ] Download final video
  - [ ] Load profile: 2-3 concurrent E2E workflows
  - [ ] Success criteria: 90% success rate

**3. Load Test Execution**
- [ ] Run tests against deployed environment:
  ```bash
  locust -f tests/load/locustfile.py --host=https://your-ecs-ip:8000
  ```
- [ ] Test runs:
  - [ ] Baseline: 5 concurrent users, 10 minutes (MVP requirement)
  - [ ] Stress: 10 concurrent users, 5 minutes
  - [ ] Spike: Ramp 0→20 users in 1 minute
  - [ ] Endurance: 5 users, 30 minutes (stability test)
- [ ] Monitor during tests:
  - [ ] CloudWatch dashboards (CPU, memory, database connections)
  - [ ] Application logs (errors, slow queries)
  - [ ] Response times and error rates

**4. Performance Benchmarks** (docs/performance.md)
- [ ] Document test results:
  - [ ] **Baseline (5 users):**
    - [ ] Throughput: X requests/second
    - [ ] Response times: p50, p95, p99
    - [ ] Error rate: X%
    - [ ] Resource usage: CPU X%, Memory X%
  - [ ] **Stress (10 users):**
    - [ ] Identify bottlenecks (database, AI API rate limits)
    - [ ] Document degradation points
  - [ ] **Spike test:**
    - [ ] Recovery time after spike
    - [ ] Error rate during spike
- [ ] Bottleneck analysis:
  - [ ] Database connection pool exhaustion?
  - [ ] ECS task CPU/memory limits?
  - [ ] AI API rate limiting?
  - [ ] S3 upload bandwidth?
- [ ] Optimization recommendations:
  - [ ] Connection pool tuning
  - [ ] ECS task scaling policies
  - [ ] Caching strategies
  - [ ] Database query optimization

**5. Performance Tuning**
- [ ] Based on test results, tune:
  - [ ] **Database connection pool:**
    - [ ] SQLAlchemy pool size: min 5, max 20
    - [ ] Overflow: 10
    - [ ] Pool recycle: 3600s
  - [ ] **ECS task resources:**
    - [ ] CPU: 1024 (1 vCPU) - upgrade if CPU >70%
    - [ ] Memory: 2048 (2GB) - upgrade if memory >80%
  - [ ] **API timeouts:**
    - [ ] Request timeout: 30s
    - [ ] Generation timeout: 10 minutes (long-running)
  - [ ] **Redis caching:**
    - [ ] Cache frequently accessed data (job status)
    - [ ] TTL: 60 seconds for status

**6. Continuous Performance Monitoring**
- [ ] Add performance tests to CI/CD:
  - [ ] Run light load test on every deployment
  - [ ] Fail deployment if performance degrades >20%
  - [ ] Track performance metrics over time
- [ ] Create performance regression alerts:
  - [ ] Response time increases
  - [ ] Throughput decreases
  - [ ] Error rate spikes

**7. Documentation** (tests/load/README.md)
- [ ] How to run load tests locally
- [ ] How to interpret results
- [ ] Performance benchmarks and SLOs
- [ ] Troubleshooting slow performance

**Implementation Notes:**
- Use Locust for flexibility and Python ecosystem integration
- Run load tests from a separate EC2 instance (not local machine) for realistic network conditions
- Test during off-peak hours to avoid disrupting real users (if any)
- Coordinate with backend/AI teams on AI API rate limits (Replicate)
- Start conservatively (5 users), ramp up slowly
- Keep an eye on costs (Replicate API charges per generation)

---

## Phase 3: MVP Hardening (Hours 36-48)

### Task 11: Backup and Recovery
**Priority:** Medium
**Estimated Time:** 2 hours
**Dependencies:** Task 5

**Subtasks:**
- [ ] Set up automated RDS backups
- [ ] Create database restore procedure
- [ ] Document recovery process
- [ ] Test backup restoration
- [ ] Set up S3 versioning for critical assets

**Deliverables:**
- Backup procedures documented
- Recovery tested and working

---

### Task 12: Security Hardening (PR-D008)
**Priority:** High
**Estimated Time:** 3 hours
**Dependencies:** All infrastructure tasks - ALL COMPLETE ✅ (infrastructure deployed via PR-D010)
**Status:** UNBLOCKED

**Description:** Conduct security audit and implement hardening measures to protect the application and infrastructure.

**Files to Create:**
- `docs/security.md` - Security documentation and audit
- `scripts/security-scan.sh` - Automated security scanning
- `.github/workflows/security-scan.yml` - CI/CD security checks

**Detailed Acceptance Criteria:**

**1. Security Audit Checklist**
- [ ] **Network Security:**
  - [ ] Review security groups:
    - [ ] RDS: ONLY accessible from ECS tasks (private subnet) ✅
    - [ ] ElastiCache: ONLY accessible from ECS tasks (private subnet) ✅
    - [ ] ECS tasks: ONLY ports 8000 exposed (or behind ALB if added)
    - [ ] No public access to databases (already VPC-only per PR-D010)
  - [ ] VPC configuration:
    - [ ] Private subnets for databases
    - [ ] Public subnet for ECS tasks (if public IP needed)
    - [ ] NAT gateway for private subnet internet access
  - [ ] SSL/TLS:
    - [ ] HTTPS enforcement (if ALB added)
    - [ ] Certificate management (ACM)
    - [ ] TLS 1.2+ minimum

- [ ] **IAM Security:**
  - [ ] Review IAM roles:
    - [ ] ECS task execution role (minimal permissions for ECR, CloudWatch)
    - [ ] ECS task role (minimal permissions for S3, RDS, Redis, Replicate)
    - [ ] Principle of least privilege (already implemented per PR-D010)
  - [ ] No long-lived AWS credentials in code
  - [ ] Use IAM roles for service-to-service auth
  - [ ] Enable MFA for AWS root account
  - [ ] Rotate IAM access keys (if any)

- [ ] **Data Security:**
  - [ ] RDS encryption at rest (check if enabled in terraform)
  - [ ] S3 bucket encryption (enable server-side encryption)
  - [ ] Redis encryption in transit (enable if supported)
  - [ ] Environment variables encrypted (AWS Secrets Manager vs ECS env vars)
  - [ ] Database backups encrypted
  - [ ] Secure secrets management:
    - [ ] Move .env secrets to AWS Secrets Manager
    - [ ] Replicate API keys in Secrets Manager
    - [ ] Database passwords auto-rotated

- [ ] **Application Security:**
  - [ ] Input validation:
    - [ ] Prompt length limits (500-2000 chars)
    - [ ] File upload validation (type, size, content)
    - [ ] SQL injection protection (ORM usage, parameterized queries)
    - [ ] XSS protection (input sanitization)
  - [ ] Rate limiting:
    - [ ] API rate limits per user (prevent abuse)
    - [ ] DDoS protection (basic with ALB rate limiting)
  - [ ] CORS configuration:
    - [ ] Option B: No CORS needed (same origin)
    - [ ] If Vercel added: Whitelist only frontend domain
  - [ ] Authentication/Authorization:
    - [ ] Session management (secure cookies)
    - [ ] JWT token validation (if implemented)
    - [ ] API key rotation policy

- [ ] **Container Security:**
  - [ ] Docker image security:
    - [ ] Use official base images (python:3.13-slim)
    - [ ] Scan for vulnerabilities (Trivy, Snyk)
    - [ ] No secrets in Dockerfile or image layers
    - [ ] Run as non-root user (check Dockerfile)
    - [ ] Minimal attack surface (remove unnecessary packages)
  - [ ] ECR image scanning:
    - [ ] Enable automated vulnerability scanning
    - [ ] Fail deployment on critical vulnerabilities

- [ ] **Logging & Monitoring:**
  - [ ] Enable CloudTrail (AWS API audit logs)
  - [ ] Enable VPC Flow Logs (network traffic analysis)
  - [ ] Application logging (no sensitive data in logs)
  - [ ] Log retention policies (comply with security requirements)
  - [ ] Security alerts:
    - [ ] Failed login attempts
    - [ ] Unusual API activity
    - [ ] Privilege escalation attempts

**2. Security Hardening Actions**
- [ ] **Terraform configuration:**
  - [ ] Enable RDS encryption at rest:
    ```hcl
    storage_encrypted = true
    kms_key_id       = aws_kms_key.rds.arn
    ```
  - [ ] Enable S3 bucket encryption:
    ```hcl
    server_side_encryption_configuration {
      rule {
        apply_server_side_encryption_by_default {
          sse_algorithm = "AES256"
        }
      }
    }
    ```
  - [ ] Enable S3 bucket versioning (for accidental deletions)
  - [ ] Block public access on S3 bucket (enforce private)
  - [ ] Enable ElastiCache encryption in transit

- [ ] **Secrets Management Migration:**
  - [ ] Create AWS Secrets Manager entries:
    - [ ] `prod/db/password` (RDS password)
    - [ ] `prod/redis/password` (if Redis auth enabled)
    - [ ] `prod/replicate/api-key`
  - [ ] Update ECS task definition to fetch from Secrets Manager
  - [ ] Remove plaintext secrets from environment variables
  - [ ] Update deployment scripts

- [ ] **Container Hardening:**
  - [ ] Update Dockerfile:
    ```dockerfile
    # Use non-root user
    RUN useradd -m -u 1000 appuser
    USER appuser

    # Read-only filesystem where possible
    # Remove unnecessary tools (wget, curl if not needed)
    ```
  - [ ] Image vulnerability scanning:
    ```bash
    # Add to CI/CD
    trivy image <ecr-image-url>
    ```

**3. Vulnerability Scanning** (scripts/security-scan.sh)
- [ ] Dependency scanning:
  ```bash
  # Python dependencies
  pip install safety
  safety check --json

  # Known vulnerabilities in requirements.txt
  pip-audit
  ```
- [ ] Docker image scanning:
  ```bash
  # Install Trivy
  trivy image fastapi:latest
  ```
- [ ] Code security scanning:
  ```bash
  # Install Bandit (Python security linter)
  bandit -r fastapi/app/
  ```
- [ ] Configuration scanning:
  ```bash
  # Terraform security scanning
  tfsec terraform/
  ```

**4. CI/CD Security Integration** (.github/workflows/security-scan.yml)
- [ ] Automated security scans on every PR:
  - [ ] Dependency vulnerability check (safety, pip-audit)
  - [ ] Code security check (Bandit)
  - [ ] Docker image scanning (Trivy)
  - [ ] Secrets detection (git-secrets, TruffleHog)
- [ ] Fail build on:
  - [ ] Critical/High vulnerabilities in dependencies
  - [ ] Hardcoded secrets detected
  - [ ] Known malicious code patterns
- [ ] Schedule weekly full security scans (GitHub Actions cron)

**5. Security Documentation** (docs/security.md)
- [ ] Security architecture overview
- [ ] Secrets management procedures
- [ ] Incident response plan:
  - [ ] Security incident classification (low, medium, high, critical)
  - [ ] Escalation procedures
  - [ ] Communication plan
  - [ ] Forensics and remediation steps
- [ ] Security best practices for developers:
  - [ ] Never commit secrets
  - [ ] Input validation guidelines
  - [ ] Secure coding standards
  - [ ] Dependency update policy
- [ ] Compliance checklist (OWASP Top 10):
  - [ ] Injection
  - [ ] Broken Authentication
  - [ ] Sensitive Data Exposure
  - [ ] XML External Entities (XXE)
  - [ ] Broken Access Control
  - [ ] Security Misconfiguration
  - [ ] Cross-Site Scripting (XSS)
  - [ ] Insecure Deserialization
  - [ ] Using Components with Known Vulnerabilities
  - [ ] Insufficient Logging & Monitoring
- [ ] Penetration testing recommendations (post-MVP)

**6. Post-Implementation Validation**
- [ ] Run security scan and fix all critical/high issues
- [ ] Verify no public database access (test connection from external IP)
- [ ] Confirm encryption at rest and in transit
- [ ] Test secrets rotation procedure
- [ ] Review CloudTrail logs for unusual activity
- [ ] Conduct basic penetration testing (or plan for external audit)

**Implementation Notes:**
- Security is iterative - start with critical issues, improve over time
- Use automated tools (Trivy, Bandit, safety) - don't rely on manual review
- Document all security decisions and trade-offs
- Consider hiring external security audit for production deployment
- Keep dependencies updated (automated Dependabot PRs)
- Follow OWASP guidelines for web application security

---

### Task 13: Documentation and Handover
**Priority:** High
**Estimated Time:** 2 hours
**Dependencies:** All tasks

**Subtasks:**
- [ ] Write deployment runbook
- [ ] Document troubleshooting procedures
- [ ] Create architecture diagram
- [ ] Document all AWS resources
- [ ] Write scaling recommendations for post-MVP
- [ ] Create cost tracking spreadsheet

**Deliverables:**
- `docs/deployment-guide.md`
- `docs/architecture.md`
- `docs/troubleshooting.md`
- Cost tracking setup

---

## Phase 4: Post-MVP Enhancements (Days 3-8)

### Task 14: Music Video Pipeline Support
**Priority:** High (Post-MVP)
**Estimated Time:** 4 hours
**Dependencies:** MVP Complete

**Subtasks:**
- [ ] Increase ECS task memory/CPU for longer videos
- [ ] Adjust S3 lifecycle policies for larger files
- [ ] Optimize database for longer job tracking
- [ ] Update timeout configurations
- [ ] Test 3-minute video generation
- [ ] Document infrastructure changes

---

### Task 15: Production Optimizations
**Priority:** Medium (Post-MVP)
**Estimated Time:** 6 hours
**Dependencies:** Task 14

**Subtasks:**
- [ ] Implement CloudFront CDN for video delivery
- [ ] Add Application Load Balancer for reliability
- [ ] Set up auto-scaling policies
- [ ] Implement comprehensive monitoring (CloudWatch dashboards)
- [ ] Add distributed tracing
- [ ] Optimize costs based on usage patterns

---

### Task 16: Advanced Features
**Priority:** Low (Post-MVP)
**Estimated Time:** 4 hours
**Dependencies:** Task 15

**Subtasks:**
- [ ] Set up A/B deployment capability
- [ ] Implement blue-green deployments
- [ ] Add performance profiling
- [ ] Create automated scaling policies
- [ ] Set up cost alerts and budgets
- [ ] Implement log analysis and metrics

---

## Critical Path for MVP (48 hours)

**First 8 hours:**
1. Task 1: Local Development Environment
2. Task 2: AWS Account Setup
3. **Task 2.5: Frontend Deployment Decision** (CRITICAL - affects all following tasks)

**Hours 8-16:**
4. Task 3: Backend Docker Container (3 hours)
5. Task 5: Database Infrastructure (3 hours)
6. Task 6: Storage Configuration (2 hours)

**Hours 16-24:**
7. Task 4: ECS Infrastructure (4 hours)
8. **Execute ONE of:** Task 6A (Vercel) or 6B (FastAPI static)

**Hours 24-36:**
9. Task 7: CI/CD Pipeline (varies by deployment choice)
10. Task 8: Environment Configuration
11. Task 9: Basic Monitoring

**Hours 36-48:**
12. Task 10: Load Testing
13. Task 12: Security Hardening
14. Task 13: Documentation

**Note:** Path complexity and time requirements vary based on Task 2.5 decision:
- **Option A (Vercel):** Fastest path, ~30 hours total
- **Option B (FastAPI):** Slightly more complex, ~32 hours total

---

## Success Metrics

### MVP (48 hours)
- [ ] All services deployed and accessible via direct IP
- [ ] Database and Redis operational
- [ ] S3 storage working for video files
- [ ] Basic CI/CD pipeline functional
- [ ] Can handle 5 concurrent users
- [ ] Basic monitoring in place
- [ ] Documentation complete

### Final Submission (Day 8)
- [ ] Music video support added
- [ ] Production optimizations complete
- [ ] Comprehensive monitoring
- [ ] Cost optimized
- [ ] Full documentation
- [ ] Demo video showcasing infrastructure

---

## Risk Mitigation

### High-Risk Items
1. **ECS Networking without ALB**: Test direct IP access thoroughly
2. **Database Performance**: Monitor connection pools closely
3. **S3 Costs**: Implement lifecycle policies immediately
4. **Container Sizes**: Optimize to reduce deployment time
5. **Environment Variables**: Double-check all configurations

### Contingency Plans
- **If ECS fails**: Fall back to EC2 with Docker
- **If RDS is too expensive**: Use containerized PostgreSQL
- **If deployment is slow**: Pre-build and cache containers
- **If S3 is slow**: Implement local caching layer
- **If chosen frontend deployment fails**: Switch to Vercel (always available as backup)
- **If CORS issues**: Fall back to FastAPI static serving (Option B)

---

## Notes

- **CRITICAL DECISION FIRST:** Complete Task 2.5 (frontend deployment decision) before starting infrastructure work
- Focus on simplicity for MVP - no Terraform, no complex orchestration
- **Recommended for MVP:** Option A (Vercel) for fastest iteration, defer complexity to post-MVP
- Prioritize working deployment over optimization
- Document everything for handover to other teams
- Keep costs minimal during development
- Test with realistic video generation loads early
- Coordinate with Backend/AI teams on API contracts
- **Frontend deployment is flexible:** Don't assume Docker/ECS until decision is made