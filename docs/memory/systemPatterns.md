# System Patterns - Architecture Decisions

**Purpose:** Track architectural decisions and patterns established during implementation.

**Last Updated:** 2025-11-15 by Blue

---

## Deployment Architecture

### Decision: Single-Container Deployment (Option B)
**Date:** 2025-11-14
**Context:** Frontend deployment strategy for MVP
**Decision:** FastAPI backend serves static frontend files (single container)
**Rationale:**
- Simpler CORS management (same-origin)
- Single deployment artifact
- Unified deployment process
- Slightly more complexity (~32h vs 30h for Vercel) but acceptable for MVP
**Alternatives Considered:**
- Option A: Vercel deployment (faster but separate deployments, more CORS complexity)
- Option C: Nginx container in ECS (ruled out as unnecessarily complex)

---

## Technology Stack Decisions

### Frontend Theme: Cyberpunk Aesthetic
**Date:** 2025-11-15
**Context:** Frontend UI/UX styling requirements
**Decision:** Implemented light cyberpunk theme with dark backgrounds, neon accents, and glassmorphism
**Rationale:**
- Matches project PRD aesthetic requirements
- Modern, sleek appearance with high contrast
- Neon accents provide clear visual hierarchy
- Glassmorphism creates depth without overwhelming
**Implementation Details:**
- Color palette: Dark backgrounds (#0A0F14, #111820) with neon accents (Neon Blue #00E5FF, Holographic Purple #BD59FF, Soft Teal #43FFC9)
- Typography: Inter (body), Orbitron (headings), JetBrains Mono (monospace)
- Effects: Glassmorphism with backdrop blur, scanline patterns, holographic shimmer animations
- Components: All UI components styled with neon glows, glassmorphism cards, dark theme inputs

---

## Integration Patterns

### Pattern: Frontend → Backend API & WebSocket Integration (Dev)
**Date:** 2025-11-17
**Context:** Local development flow for web UI → FastAPI backend
**Decision:** Use Vite dev proxy for REST + WebSockets and Socket.io ASGI wrapper in FastAPI.
**Details:**
- Frontend dev server proxies:
  - `/api` → `http://localhost:8000` (REST API)
  - `/socket.io` → `http://localhost:8000` (Socket.io Engine.IO endpoint)
  - `/ws` → `ws://localhost:8000` (raw WebSocket endpoints if needed)
- Backend runs `app.main:socketio_app` (Socket.io ASGI wrapper) so Socket.io and FastAPI share the same port.
- Socket.io client always connects to `/socket.io` and passes `generation_id` via query parameters; backend extracts it in `handle_connect` and/or `subscribe` to validate and subscribe to the correct generation room.
- `GET /api/v1/generations/{id}` first tries persisted clip/progress data (Postgres/Redis via `ClipAssemblyService`), then falls back to in-memory `_generation_store` so status lookups work even when DB/Redis are misconfigured in dev.

---

## Storage Architecture

### Decision: Environment-Aware Storage Service
**Date:** 2025-11-15
**Context:** Need to support both local development (filesystem) and production (S3)
**Decision:** Created unified StorageService that automatically switches between backends based on USE_LOCAL_STORAGE env var
**Rationale:**
- Single code path for both environments
- Easy local development without AWS credentials
- Production-ready S3 integration
- Presigned URL support for secure access
**Implementation:**
- Local: Files stored in `./storage` directory with same folder structure as S3
- Production: Files uploaded to S3 bucket with path `generations/{generation_id}/clips/{clip_id}.mp4`
- Automatic fallback if S3 upload fails (uses Replicate URL as backup)

### Decision: PostgreSQL for Generation Metadata
**Date:** 2025-11-15
**Context:** Need persistent storage for generation metadata
**Decision:** Created GenerationStorageService using PostgreSQL with JSONB fields for flexible metadata
**Rationale:**
- Structured data (generation_id, status, timestamps) in columns
- Flexible metadata (prompt_analysis, brand_config, scenes) in JSONB
- Connection pooling for performance
- Automatic table creation on first connection
**Implementation:**
- Tables: `generations` (id, status, prompt, metadata JSONB, thumbnail_url, duration_seconds, timestamps)
- Indexes: status, created_at (for fast filtering and sorting)
- Fallback: In-memory `_generation_store` if database unavailable

## Data Flow Patterns

### Video Generation → Storage Flow
1. User submits generation request via POST /api/v1/generations
2. Generation metadata stored in PostgreSQL immediately (status: QUEUED)
3. AI pipeline generates scenes and micro-prompts
4. `generate_video_clips` called with storage_service parameter
5. For each clip:
   - Replicate generates video → returns URL
   - StorageService downloads from Replicate URL
   - StorageService uploads to S3/local storage
   - Returns storage URL (S3 path or local path)
6. Generation status updated to PROCESSING with video_results metadata
7. Frontend can list generations via GET /api/v1/generations

*(Additional patterns to be populated as video generation pipeline evolves)*
