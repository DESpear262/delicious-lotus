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

**Completed:** 5/9
**Unblocked (Ready to Start):** 1
**Blocked (Dependencies Not Met):** 3

---

## Currently Unblocked PRs

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

**Acceptance Criteria:**
- [ ] Deployment runbook with step-by-step instructions
- [ ] Architecture diagram (can be ASCII art or Mermaid diagram)
- [ ] Component interaction documentation (Frontend → Backend → AI → FFmpeg)
- [ ] Deployment sequence documented (Docker build → ECR push → ECS update)
- [ ] Rollback procedures documented
- [ ] Troubleshooting guide with common issues:
  - [ ] Container startup failures
  - [ ] Database connection issues
  - [ ] S3 access problems
  - [ ] Frontend not loading
  - [ ] API errors
- [ ] AWS resource inventory (RDS, ElastiCache, S3, ECR, ECS, CloudWatch)
- [ ] Cost tracking spreadsheet structure
- [ ] Scaling recommendations for post-MVP

**Implementation Notes:**
- Can be written before full implementation (describe intended architecture)
- Focus on Option B deployment model (single container with static files)
- Include both local development and production deployment
- Document prerequisites (AWS CLI, Docker, credentials)
- Include monitoring and health check procedures

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

**Blocked PRs** (will plan when dependencies clear):
- PR-D004: CI/CD Pipeline (needs PR-D002)
- PR-D006: Monitoring (needs user to set up ECS)
- PR-D007: Load Testing (needs deployment)
- PR-D008: Security Hardening (needs infrastructure)

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

### Task 7: CI/CD Pipeline Setup
**Priority:** High
**Estimated Time:** 2-3 hours (varies by Task 2.5 decision)
**Dependencies:** Tasks 3, 4, and 6A/6B (based on choice)

**Subtasks:**
- [ ] Create GitHub Actions workflow for backend
- [ ] Set up ECR push on main branch commits
- [ ] Configure ECS service updates on new images
- [ ] Add basic health checks
- [ ] Set up rollback capability
- [ ] **If Option A:** Vercel handles frontend CI/CD automatically
- [ ] **If Option B:** Frontend builds as part of backend deployment

**Deliverables:**
- `.github/workflows/deploy-backend.yml`
- **If Option B:** Integrated build process documented
- Deployment automation working

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

### Task 9: Monitoring and Logging (Minimal MVP)
**Priority:** Medium
**Estimated Time:** 2 hours
**Dependencies:** Task 4

**Subtasks:**
- [ ] Set up CloudWatch log streams for ECS tasks
- [ ] Create simple log aggregation view
- [ ] Set up basic error alerting (email)
- [ ] Configure application logs to stdout
- [ ] Test log visibility from ECS

**Deliverables:**
- Logs visible in CloudWatch
- Basic error notifications working
- Debugging capability established

---

### Task 10: Load Testing and Optimization
**Priority:** Medium
**Estimated Time:** 3 hours
**Dependencies:** Tasks 7, 8

**Subtasks:**
- [ ] Create test script for concurrent video generation
- [ ] Test with 5 simultaneous users (requirement)
- [ ] Identify and fix bottlenecks
- [ ] Optimize container resource allocation
- [ ] Tune database connection pools
- [ ] Document performance characteristics

**Deliverables:**
- Load testing results
- Performance documentation
- Optimized resource allocation

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

### Task 12: Security Hardening
**Priority:** High
**Estimated Time:** 3 hours
**Dependencies:** All infrastructure tasks

**Subtasks:**
- [ ] Review and tighten security groups
- [ ] Ensure no public database access
- [ ] Validate IAM permissions (principle of least privilege)
- [ ] Set up HTTPS if time permits (not required for MVP)
- [ ] Review and secure all environment variables
- [ ] Document security configuration

**Deliverables:**
- Security audit complete
- All unnecessary ports closed
- IAM policies minimized

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