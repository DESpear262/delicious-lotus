# AI Video Generation Pipeline - FastAPI Backend

**Block 0: API Skeleton & Core Infrastructure**

This is the FastAPI backend for the AI Video Generation Pipeline project.

## Features

- ✅ FastAPI application with automatic API documentation
- ✅ Request ID tracking and logging middleware
- ✅ Health check endpoints (`/health`, `/health/detailed`)
- ✅ API v1 router (`/api/v1/`) for public endpoints
- ✅ Internal v1 router (`/internal/v1/`) for FFmpeg integration
- ✅ CORS middleware configured
- ✅ Global exception handling
- ✅ Startup/shutdown lifecycle hooks

## Project Structure

```
fastapi/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application setup
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py     # Application configuration
│   │   └── logging.py    # Logging middleware and setup
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── v1.py           # Public API v1 routes
│   │   │   └── internal_v1.py  # Internal API v1 routes
│   └── models/
│       └── __init__.py
├── requirements.txt      # Python dependencies
└── README.md
```

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Copy environment configuration:
```bash
cp .env.example .env  # Create this file with your configuration
```

## Running the Application

### Development
```bash
uvicorn app.main:create_application --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
uvicorn app.main:create_application --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Checks
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health check with system information

### API v1 (Public)
- `GET /api/v1/` - API root
- `POST /api/v1/generations` - Create video generation (placeholder)
- `GET /api/v1/generations/{id}` - Get generation status (placeholder)

### Internal v1 (FFmpeg Integration)
- `GET /internal/v1/` - Internal API root
- `POST /internal/v1/audio-analysis` - Audio analysis (placeholder)
- `POST /internal/v1/process-clips` - Process video clips (placeholder)
- `POST /internal/v1/processing-complete` - Mark processing complete (placeholder)

## API Documentation

When running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Next Steps

This is Block 0 of the implementation. Next blocks will add:

- **Block A**: Prompt processing and enhancement
- **Block C**: Clip generation orchestration
- **Block D**: AI-assisted editing
- **Block E**: Style/brand consistency
- **Block Z**: End-to-end integration testing

## Request ID Tracking

All requests include a unique `x-request-id` header for tracing. This ID is also included in all log messages and error responses for debugging.
