# Technical Context - Stack & Constraints

**Purpose:** Tech stack details, setup procedures, and discovered constraints.

**Last Updated:** 2025-11-15 by Blue

---

## Tech Stack Overview

### Frontend
- **Framework:** React 19 with TypeScript
- **Build Tool:** Vite
- **Routing:** React Router v6
- **HTTP Client:** Axios
- **WebSocket:** Socket.io client
- **Styling:** CSS Modules + CSS Variables (NO Tailwind per project requirements)
- **Typography:** Inter (body), Orbitron (headings), JetBrains Mono (monospace) via Google Fonts
- **Theme:** Cyberpunk aesthetic with dark backgrounds, neon accents, glassmorphism effects
- **Target Output:** Static files served by backend

### Backend (AI + FFmpeg combined)
- **Framework:** Python 3.13 + FastAPI
- **AI Integration:** Replicate Python SDK
- **Video Processing:** FFmpeg with Python bindings
- **Task Queue:** Celery (async processing)
- **Static Files:** FastAPI StaticFiles middleware

### Infrastructure
- **Database:** PostgreSQL 16 (RDS for production)
- **Cache/Queue:** Redis 7 (ElastiCache for production) - using redis:7-alpine for stability
- **Storage:** S3 for video/asset storage
- **Deployment:** AWS ECS with Fargate
- **Container Registry:** AWS ECR
- **Monitoring:** CloudWatch (basic for MVP)

---

## Development Environment

### Local Setup (PR-D001)
- Docker Compose for local development
- PostgreSQL 16 container (port 5432)
- Redis 7 container (port 6379, using redis:7-alpine image)
- Environment variables via .env file
- Hot reload for both frontend and backend

---

## Known Constraints

### Timeline
- MVP Deadline: 48 hours from project start
- Final Submission: 8 days total
- Competition: November 14-22, 2025

### Performance Requirements
- 30-second video: <5 minutes generation time
- 60-second video: <10 minutes generation time
- Support 5 concurrent users minimum

### Cost Constraints
- Use cheaper models during development
- Smart caching for repeated elements
- Lifecycle policies for S3 (7-day auto-delete)

### Quality Standards
- 720p resolution (1280x720)
- 128 kbps AAC audio minimum
- sRGB color space
- H.264 MP4 encoding

---

## Credentials & Access

### Required (User-Provided)
- AWS credentials (IAM user with minimal permissions)
- Replicate API keys
- Database connection strings (post-RDS setup)
- Redis connection parameters (post-ElastiCache setup)

### Status
- **Deployment Decision:** ✅ Complete (Option B)
- **AWS Setup:** ⏳ Pending (user will provide)
- **Backend Structure:** 🔄 In Progress (backend team)

---

## Dependencies Between Teams

### Team 1 (DevOps + Frontend) - This Track
- Blocked on: Backend team for basic FastAPI app structure (PR-D002)
- Provides: Frontend build output, deployment infrastructure

### Backend/AI Team
- Working on: Basic FastAPI structure
- Will provide: API endpoints, Replicate integration

### FFmpeg Team
- Status: Unknown
- Will provide: Video composition endpoints
