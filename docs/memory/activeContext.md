# Active Context - Current Work Focus

**Purpose:** What's happening right now, recent changes, current focus areas.

**Last Updated:** 2025-11-17 by Silver (Docker integration: FFmpeg backend services added to root docker-compose)

---

## Current Sprint Focus

**Phase:** Initial Setup and Foundation
**Timeline:** MVP in 48 hours, currently at Hour ~4
**Active Agents:** White (planning + coordination)

---

## In-Flight Work

### Just Completed
- ✅ PR-D001: Local Development Environment (commit b020358)
- ✅ PR-F001: Project Initialization (commit 68eee3f)
- ✅ PR-D005: Environment Config Templates (commit 1215253)
- ✅ PR-F002: Design System Foundation (commit dec2632)
- ✅ Consolidated task list created (docs/task-list.md)

### Just Completed
- ✅ Block 0 PR 1: FastAPI Project Bootstrap & Routing Structure (Orange)
- ✅ Block 0 PR 2: Error Handling, Validation, and Response Models (Orange)
- ✅ Block A PR 101: Prompt Parsing Module (OpenAI Integration) (Orange)
- ✅ Block A PR 102: Brand & Metadata Extraction Layer (Orange)
- ✅ Block 0 PR 4: Internal Service Contract & Callouts (Blonde) - Complete
- ✅ Block C PR 301: Micro-Prompt Builder (Replicate Integration) (Orange)
- ✅ Block C PR 303: Clip Assembly & DB/Redis Integration (Orange)
- ✅ Block D PR 401: Edit Intent Classifier (OpenAI) (Orange)
- ✅ Block D PR 402: Timeline Edit Planner (White) - Complete
- ✅ Block E PR 501: Style Vector Builder (White) - Complete
- ✅ Block E PR 502: Brand Harmony Module (White) - Complete
- ✅ Block E PR 503: Consistency Enforcement Layer (White) - Complete

### Ready to Start
**AI**
- 🎯 **Block 0 PR 3: Generation Lifecycle API Skeleton** (4-5h) - UNBLOCKED
- 🎯 PR-D003: Storage Documentation (1h)
- 🎯 PR-D005: Environment Config Templates (2h)
- 🎯 PR-D009: Deployment Documentation (2h)
- 🎯 PR-F002: Design System Foundation (3h) - dependencies met
- 🎯 PR-F003: API Client Setup (2h) - dependencies met
- 🎯 PR-F016: User Documentation (2h)
### Ready to Start (4 Unblocked PRs)
**DevOps:**
- 🎯 PR-D003: Storage Documentation (1h) - no dependencies
- 🎯 PR-D009: Deployment Documentation (2h) - can document in parallel

**Frontend:**
- 🎯 PR-F003: API Client Setup (2h) - dependencies met (F001 ✅)
- 🎯 PR-F005: Routing and Layout (2h) - dependencies met (F001 ✅, F002 ✅)
- 🎯 PR-F016: User Documentation (2h) - no dependencies (parallel work)

### Blocked & Waiting
- ⏸️ PR-D002: Backend Docker Container (waiting for backend team's FastAPI structure)
- ⏸️ PR-D004-D008: DevOps PRs blocked by PR-D002 or user AWS setup
- ⏸️ PR-F004-F015: Frontend PRs blocked by PR-F003, PR-F004, or PR-F005
- ⏸️ User AWS setup tasks (Tasks 2, 4, 5)

---

## Recent Decisions

1. **Deployment Strategy** (2025-11-14)
   - Chose Option B: FastAPI serves static files
   - Single container deployment
   - Simpler than Vercel but unified

2. **Work Approach** (2025-11-14)
   - Parallel tracks: DevOps + Frontend simultaneously
   - Credentials provided as needed
   - Focus on immediately unblocked PRs first

3. **Conflict Management** (2025-11-14)
   - One PR = one commit
   - One planning session = one commit
   - Follow commit-policy.md strictly

---

## Current Questions & Blockers

### Resolved
- ✅ Which deployment approach? → Option B
- ✅ When do we get credentials? → As needed
- ✅ Work priority? → Parallel tracks

### Open
- How aggressively should we rely on database/Redis vs in-memory fallbacks for local development when Postgres schema is out of sync?

---

## Next Up (After Current PRs)

**DevOps:**
- PR-D003: Storage Documentation (1h)
- PR-D005: Environment Config Templates (2h)
- PR-D009: Deployment Documentation (2h)

**Frontend:**
- PR-F002: Design System (3h) - after F001
- PR-F003: API Client (2h) - after F001
- PR-F005: Routing/Layout (2h) - after F001, F002

---

## Communication Log

**2025-11-14 14:05** - Orange claimed identity, released White (expired)
**2025-11-14 14:15** - Asked deployment strategy questions
**2025-11-14 14:16** - User chose Option B, parallel tracks, credentials as needed
**2025-11-14 14:20** - Planned unblocked PRs (9 total: 4 DevOps, 5 Frontend)
**2025-11-14 14:25** - User requested: Launch 2 agents (one for D001, one for F001)
**2025-11-14 14:26** - Creating memory bank, then launching agents
**2025-11-14 14:30** - Orange starting work on Block 0 PR 1: FastAPI Project Bootstrap & Routing Structure
**2025-11-14 15:00** - Orange completed Block 0 PR 1: FastAPI skeleton with routers, logging, health endpoints, and lifecycle hooks. All Block 0 PRs now unblocked.
**2025-11-14 15:30** - Orange completed Block 0 PR 2: Error handling, validation, and response models with standardized error format, Pydantic schemas, and centralized validation logic.
**2025-11-14 16:15** - Orange completed Block A PR 101: Prompt parsing module with comprehensive OpenAI 4o-mini integration, structured analysis schema, and mock testing framework.
**2025-11-14 16:45** - Orange completed Block A PR 102: Brand & metadata extraction layer with GPT-4o-mini brand completion, flexible BrandConfig schema, and intelligent brand-prompt analysis merging.
**2025-11-14 17:15** - Orange completed Block C PR 301: Micro-prompt builder with Replicate-optimized prompts, brand-style vector integration, scene-to-prompt conversion, and comprehensive testing suite.
**2025-11-14 18:00** - Orange completed Block C PR 303: Clip assembly & DB/Redis integration with PostgreSQL storage, Redis progress tracking, clip ordering maintenance, and full API integration for persistent clip management.
**2025-11-14 18:45** - Orange completed Block D PR 401: Edit intent classifier with strict LLM-based parsing using OpenAI tool calls, structured FFmpeg operation output, minimal safety guardrails, and comprehensive API integration for natural language video editing.
**2025-11-14 ~15:00** - PR-D001 and PR-F001 completed by Orange
**2025-11-14 ~16:00** - PR-D005 and PR-F002 completed by Orange and White (parallel)
**2025-11-14 ~16:30** - White claimed identity for planning session
**2025-11-14 ~16:35** - Created consolidated task-list.md with all tracks
**2025-11-15** - Blue: Transcribed bughunt notes, removed prompt character limit validation, implemented comprehensive cyberpunk theme facelift across entire frontend
**2025-11-15** - Blue: Created ConfirmDialog component to replace browser confirm dialogs with styled modals using "Resume" and "Discard" button labels
**2025-11-15** - Blue: Extracted Replicate video generation logic from cli.py into centralized generate_video_clips function in ffmpeg-backend/src/app/api/v1/replicate.py. Added parallelization support (concurrent vs sequential generation). Added UI switch in ReviewStep for parallelize_generations option. Updated both cli.py and FastAPI backend to use the centralized function.
**2025-11-15** - Blue: Implemented S3 and database storage for generations. Created StorageService (S3/local filesystem), GenerationStorageService (PostgreSQL), updated generate_video_clips to upload videos to storage, added GET /api/v1/generations endpoint, fixed History page null safety, added thumbnail generation to TODO.md.
**2025-11-15** - Blue: Implemented Replicate webhook-based async video generation. Created webhook endpoint POST /api/v1/webhooks/replicate, updated generate_video_clips to use webhooks instead of polling, added prediction_id mapping storage, webhook handler processes results and uploads to S3. Generation now returns immediately instead of blocking on Replicate completion.
**2025-11-15** - Blue: Enhanced video generation progress page with verbose CLI-style step display. Updated GenerationProgress page to show detailed steps (Analyzing Prompt, Decomposing Scenes, Building Micro-Prompts, Generating Videos, Composition, Rendering). Added comprehensive console logging throughout backend (FastAPI and ffmpeg-backend) matching CLI output format. Enhanced frontend console logging with formatted progress messages. All logging accessible from browser dev tools and backend terminal for debugging infinite loading issues.
**2025-11-17** - Silver: Debugged end-to-end generation via web app. Fixed frontend → backend API proxying, aligned brand payload with backend `BrandConfig` (nested `ColorPalette`), updated scene decomposition and micro-prompt builder to handle new brand color format, wired FastAPI Socket.io ASGI app and frontend Socket.io client (`/socket.io` + `generation_id` query), and ensured in-memory `_generation_store` is always populated so `GET /api/v1/generations/{id}` works even when Postgres/Redis or clip storage are misconfigured.
**2025-11-17** - Silver: Integrated FFmpeg backend services into root docker-compose.yml. Added `ffmpeg-backend-api` (port 8001) and `ffmpeg-backend-worker` services that share the same postgres and redis instances as the main backend. Created automatic database initialization script (`docker/postgres/init-ffmpeg-db.sh`) to create `ffmpeg_backend` database on first startup. All changes isolated to root docker-compose.yml so ffmpeg-backend team can continue using their own docker-compose.yml independently.
