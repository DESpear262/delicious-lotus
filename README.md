# AI Video Generation Pipeline

An AI-powered video generation pipeline for creating professional-quality videos from text prompts. Built for the AI Video Generation Competition (November 14-22, 2025).

## Features

- **Ad Creative Pipeline**: Generate 15-60 second advertising videos with brand elements
- **Music Video Pipeline**: Create 1-3 minute music videos synchronized to audio (post-MVP)
- **Multiple aspect ratios**: 16:9, 9:16, 1:1
- **Cloud-native**: Deployed on AWS with auto-scaling capabilities
- **AI-powered**: Uses Replicate's state-of-the-art models

## Quick Start

### Local Development

1. **Prerequisites**
   - Docker and Docker Compose
   - Python 3.13+
   - Node.js 18+

2. **Setup**
   ```bash
   # Copy environment template
   cp .env.example .env
   # Edit .env with your configuration

   # Start all services
   docker-compose up
   ```

3. **Access**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

See [docs/local-setup.md](docs/local-setup.md) for detailed instructions.

### AWS Deployment

**Full infrastructure deployment in one command:**

```bash
# First time setup
./scripts/deploy.sh init

# Deploy/update everything
./scripts/deploy.sh apply
```

This will:
- Build and push Docker images to ECR
- Deploy infrastructure via Terraform (RDS, Redis, S3, ECS)
- Initialize/migrate database schema
- Update running services

See [terraform/README.md](terraform/README.md) for detailed deployment documentation.

### Database Migrations

```bash
# Initialize database (first time only)
./scripts/migrate-db.sh init

# Apply pending migrations
./scripts/migrate-db.sh migrate

# Check migration status
./scripts/migrate-db.sh status
```

Migrations are automatically run via ECS tasks within the VPC - no bastion host required!

See [backend/migrations/README.md](backend/migrations/README.md) for migration guidelines.

## Architecture

```
┌─────────────┐
│   Frontend  │ (React + Vite)
│  (Served by │
│   Backend)  │
└──────┬──────┘
       │
       ↓
┌─────────────┐      ┌──────────────┐
│   FastAPI   │─────→│  Replicate   │ (AI Models)
│   Backend   │      │     API      │
└──────┬──────┘      └──────────────┘
       │
       ├──────→ PostgreSQL (Jobs, Clips, Compositions)
       ├──────→ Redis (Task Queue, Caching)
       ├──────→ S3 (Video Storage)
       └──────→ FFmpeg (Video Composition)
```

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

## Project Structure

```
├── backend/           # FastAPI backend + FFmpeg processing
│   ├── app/          # Application code
│   ├── migrations/   # Database migrations
│   └── Dockerfile    # Production container
├── frontend/         # React frontend
│   ├── src/          # Source code
│   └── dist/         # Build output (served by backend)
├── terraform/        # AWS infrastructure as code
│   ├── modules/      # Reusable Terraform modules
│   └── *.tf          # Main configuration
├── docker/           # Docker configurations
│   ├── postgres/     # Database initialization
│   └── redis/        # Redis configuration
├── scripts/          # Deployment and utility scripts
│   ├── deploy.sh     # Full AWS deployment
│   └── migrate-db.sh # Database migrations
└── docs/             # Documentation
    ├── prd.md                       # Product requirements
    ├── local-setup.md               # Local dev setup
    ├── DATABASE_INITIALIZATION.md   # DB setup guide
    └── memory/                      # Implementation notes
```

## Development Workflow

### Making Code Changes

1. **Backend changes**
   ```bash
   # Make your changes in backend/
   docker-compose restart backend
   ```

2. **Frontend changes**
   ```bash
   cd frontend
   npm run dev  # Hot reload enabled
   ```

3. **Database changes**
   ```bash
   # Create new migration
   vim backend/migrations/00X_your_change.sql

   # Apply migration
   ./scripts/migrate-db.sh migrate
   ```

### Deploying Changes

```bash
# Deploy everything (infrastructure + code)
./scripts/deploy.sh apply

# Just update code (faster)
docker build -t delicious-lotus-backend:latest -f backend/Dockerfile backend/
# Then push to ECR and update ECS (see scripts/deploy.sh)
```

## Documentation

- **[PRD](docs/prd.md)** - Product requirements and specifications
- **[Local Setup](docs/local-setup.md)** - Development environment setup
- **[Terraform README](terraform/README.md)** - AWS infrastructure details
- **[Database Init](docs/DATABASE_INITIALIZATION.md)** - Database setup guide
- **[Storage Architecture](docs/storage-architecture.md)** - S3 and file storage
- **[Environment Setup](docs/environment-setup.md)** - Configuration variables
- **[Memory Bank](docs/memory/)** - Implementation notes and patterns

## Scripts Reference

### `scripts/deploy.sh`

Complete AWS infrastructure deployment and updates.

```bash
./scripts/deploy.sh init      # Initialize Terraform
./scripts/deploy.sh plan       # Preview changes
./scripts/deploy.sh apply      # Deploy everything
./scripts/deploy.sh destroy    # Destroy all resources (WARNING!)
```

### `scripts/migrate-db.sh`

Database schema management and migrations.

```bash
./scripts/migrate-db.sh init      # Initialize fresh database
./scripts/migrate-db.sh migrate   # Apply pending migrations
./scripts/migrate-db.sh status    # Check current version
```

## Technology Stack

**Frontend**
- React 18 + TypeScript
- Vite (build tool)
- Axios (HTTP client)
- CSS Modules (styling)

**Backend**
- Python 3.13
- FastAPI (web framework)
- FFmpeg (video processing)
- Celery (task queue)
- psycopg2 (PostgreSQL)

**Infrastructure**
- AWS ECS Fargate (container orchestration)
- RDS PostgreSQL 17 (database)
- ElastiCache Redis 7 (caching/queue)
- S3 (video storage)
- ECR (container registry)
- CloudWatch (logging)

**AI/ML**
- Replicate API (video/image generation)
- Multiple state-of-the-art models

## Cost Optimization

Current infrastructure costs ~$30-50/month:
- RDS db.t4g.micro: ~$12/month
- ElastiCache cache.t4g.micro: ~$11/month
- ECS Fargate (1 task): ~$15/month
- S3 with lifecycle policies: ~$1-2/month
- ECR + CloudWatch: ~$1-2/month

S3 lifecycle policies automatically delete:
- Temp files after 7 days
- Generated clips after 30 days
- Final compositions after 90 days

See [docs/storage-architecture.md](docs/storage-architecture.md) for cost optimization strategies.

## Competition Deliverables

- [x] Working MVP deployed to AWS
- [x] Ad Creative Pipeline (15-60 seconds)
- [x] Database schema and infrastructure
- [x] Complete documentation
- [ ] Music Video Pipeline (1-3 minutes)
- [ ] Demo video
- [ ] Sample AI-generated videos
- [ ] Technical deep dive document

**Timeline**: MVP in 48 hours, final submission in 8 days

## Contributing

See [docs/task-list-devops.md](docs/task-list-devops.md) and [docs/task-list-frontend.md](docs/task-list-frontend.md) for current tasks and PRs.

## License

Competition entry - All rights reserved.

## Support

For issues or questions:
1. Check [docs/troubleshooting.md](docs/troubleshooting.md)
2. Review CloudWatch logs: `aws logs tail /ecs/dev/ai-video-backend --follow`
3. Check infrastructure: `cd terraform && terraform state list`

## Acknowledgments

Built for the AI Video Generation Competition (November 14-22, 2025)
- Prize: $5,000
- Team: Gauntlet Development Squad
- Powered by Replicate, AWS, and Claude Code
