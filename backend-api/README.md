# FFmpeg Backend Service

A FastAPI-based backend service for processing video compositions using FFmpeg. This service handles video processing jobs, manages media assets, and provides a REST API for creating and managing video compositions.

## Features

- **FFmpeg Integration**: Built-in FFmpeg 7.0.2 for video processing
- **Job Queue System**: Redis Queue (RQ) for asynchronous job processing
- **Database**: PostgreSQL 17 for data persistence
- **S3 Storage**: Integrated S3-compatible storage for media assets
- **Docker Support**: Complete Docker setup for development and production
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Type Safety**: Full type hints with mypy validation
- **Code Quality**: Pre-commit hooks with black, ruff, and security checks

## Quick Start

### Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- Python 3.11+ (for local development)
- Git

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ffmpeg-backend
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
# At minimum, configure:
# - DATABASE_URL
# - REDIS_URL
# - S3 credentials (if using S3)
```

### 3. Start Development Environment

```bash
# Build and start all services
make dev-build

# Or use docker-compose directly
docker-compose up --build
```

### 4. Verify Installation

The following services will be available:

- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

Test the health endpoint:

```bash
curl http://localhost:8000/api/v1/health
```

## Development

### Project Structure

```
ffmpeg-backend/
├── src/
│   ├── api/              # FastAPI application
│   │   ├── routes/       # API route handlers
│   │   │   ├── compositions.py
│   │   │   ├── jobs.py
│   │   │   └── health.py
│   │   └── middleware/   # Custom middleware
│   │       ├── cors.py
│   │       ├── request_id.py
│   │       └── error_handler.py
│   ├── core/             # Core configuration and settings
│   │   ├── config.py     # Application settings
│   │   └── logging.py    # Logging configuration
│   ├── db/               # Database models and migrations
│   │   ├── models/       # SQLAlchemy models
│   │   └── session.py    # Database session management
│   ├── services/         # Business logic
│   │   └── ffmpeg/       # FFmpeg processing service
│   ├── workers/          # Background job workers
│   │   └── tasks.py      # RQ task definitions
│   └── main.py           # Application entry point
├── tests/                # Test suite
├── migrations/           # Alembic database migrations
├── docker-compose.yml    # Docker services configuration
├── Dockerfile            # Production Docker image
├── Dockerfile.dev        # Development Docker image
├── Makefile             # Development commands
└── pyproject.toml       # Python project configuration
```

### Common Development Tasks

```bash
# Start development environment
make dev

# View logs
make logs                    # All services
make logs SERVICE=api        # Specific service

# Run tests
make test                    # Run all tests
make test-cov               # With coverage report

# Code quality
make format                  # Auto-format code
make lint                    # Run linters

# Database operations
make migrate                 # Apply migrations
make migrate-new MSG="description"  # Create new migration
make db-shell               # Open PostgreSQL shell

# Docker operations
make shell                   # Open shell in API container
make build                   # Rebuild images
make clean                   # Stop and remove volumes
make ps                      # Show running services

# See all available commands
make help
```

### Setting Up Local Development

If you prefer to run the application locally without Docker:

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
make install

# Install pre-commit hooks
pre-commit install

# Run the application (requires Redis and PostgreSQL running)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

Key environment variables (see `.env.example` for complete list):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@db:5432/ffmpeg_backend` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `AWS_ACCESS_KEY_ID` | S3 access key | - |
| `AWS_SECRET_ACCESS_KEY` | S3 secret key | - |
| `S3_BUCKET_NAME` | S3 bucket for media | - |
| `ENVIRONMENT` | Environment (dev/staging/prod) | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `WORKER_CONCURRENCY` | RQ worker concurrency | `2` |

## API Documentation

### API Endpoints

#### Health Check
- `GET /api/v1/health` - Service health status

#### Compositions
- `POST /api/v1/compositions` - Create new composition
- `GET /api/v1/compositions` - List compositions
- `GET /api/v1/compositions/{id}` - Get composition details
- `PUT /api/v1/compositions/{id}` - Update composition
- `DELETE /api/v1/compositions/{id}` - Delete composition

#### Jobs
- `POST /api/v1/jobs` - Create processing job
- `GET /api/v1/jobs` - List jobs
- `GET /api/v1/jobs/{id}` - Get job status
- `DELETE /api/v1/jobs/{id}` - Cancel job

### Interactive API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_api/test_health.py -v

# Run tests matching pattern
pytest -k "test_health" -v

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

## Code Quality

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`:

- **black**: Code formatting
- **ruff**: Linting and code quality
- **mypy**: Type checking
- **bandit**: Security checks
- **trailing-whitespace**: Remove trailing whitespace
- **end-of-file-fixer**: Ensure files end with newline

Install pre-commit hooks:

```bash
pre-commit install
```

Run manually:

```bash
pre-commit run --all-files
```

### Code Formatting

```bash
# Format all code
make format

# Check formatting
black --check src/ tests/
```

### Linting

```bash
# Run all linters
make lint

# Run ruff only
ruff check src/ tests/

# Run mypy only
mypy src/
```

## Docker

### Production Build

```bash
# Build production image
make build-prod

# Run production container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  ffmpeg-backend:latest
```

### Docker Compose Override

For local customization without modifying `docker-compose.yml`:

```bash
# Copy override example
cp docker-compose.override.yml.example docker-compose.override.yml

# Edit with your local settings
# This file is ignored by git
```

## Deployment

### Environment Setup

1. Set all required environment variables
2. Configure S3 bucket and credentials
3. Set up PostgreSQL database
4. Set up Redis instance
5. Build and deploy Docker image

### Database Migrations

```bash
# Apply migrations
docker-compose exec api alembic upgrade head

# Create new migration
docker-compose exec api alembic revision --autogenerate -m "description"
```

### Health Monitoring

Monitor the health endpoint for service status:

```bash
curl http://your-domain/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "database": "connected",
    "redis": "connected",
    "ffmpeg": "available"
  }
}
```

## Troubleshooting

### Common Issues

#### Services not starting

```bash
# Check service status
make ps

# View logs
make logs

# Clean and restart
make clean
make dev-build
```

#### Database connection errors

```bash
# Check PostgreSQL is running
docker-compose ps db

# Verify connection
make db-shell
```

#### Redis connection errors

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
make redis-cli
ping
```

#### FFmpeg not found

```bash
# Verify FFmpeg in container
make shell
ffmpeg -version
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `make test`
4. Run linters: `make lint`
5. Format code: `make format`
6. Commit (pre-commit hooks will run)
7. Create pull request

## License

MIT

## Support

For issues and questions, please open a GitHub issue.
