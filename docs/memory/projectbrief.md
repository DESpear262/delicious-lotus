# Project Brief - Core Requirements & Goals

**Purpose:** Foundation document defining core requirements, goals, and project scope.

**Last Updated:** 2025-11-17 by Silver (Video generation integration fixes)

---

## Project Overview

**Name:** Delicious Lotus - AI Video Generation Platform

**Mission:** Transform natural language prompts into professional-quality video advertisements using AI, with focus on brand consistency, accessibility, and user experience.

**Competition Timeline:** November 14-22, 2025 (8 days total, MVP due in 48 hours)

---

## Core Requirements

### Functional Requirements

**1. Video Generation Pipeline**
- Input: Natural language prompt (e.g., "Make an ad spot for a Ford Mustang featuring a quokka wearing a cowboy hat as a mascot")
- Output: Professional MP4 video (720p, H.264, AAC audio)
- Length: 30-60 seconds
- Style: Brand-consistent, accessible, visually coherent

**2. AI Processing Chain**
- **Prompt Analysis:** Extract brand identity, target audience, key messages
- **Scene Decomposition:** Break video into logical scenes with timing
- **Micro-Prompt Generation:** Create detailed prompts for each scene
- **Video Synthesis:** Generate individual video clips via AI (Replicate API)
- **Composition:** Assemble clips into final video (FFmpeg)
- **Quality Assurance:** Ensure brand consistency and accessibility

**3. User Experience**
- Web-based interface with real-time progress updates
- Generation history and management
- Video editing capabilities (cut, trim, reorder scenes)
- Brand configuration and style management

### Technical Requirements

**1. Architecture**
- **Frontend:** React 19 + TypeScript + Vite
- **Backend:** Python 3.13 + FastAPI
- **AI Services:** Replicate API (wan-video/wan-2.2-t2v-fast model)
- **Video Processing:** FFmpeg with Python bindings
- **Storage:** S3 for production, local filesystem for development
- **Database:** PostgreSQL for metadata, Redis for caching/queues

**2. Performance**
- 30-second video: <5 minutes generation time
- 60-second video: <10 minutes generation time
- Support 5+ concurrent users
- Real-time progress updates via WebSockets

**3. Quality Standards**
- Resolution: 1280x720 (720p)
- Audio: 128 kbps AAC minimum
- Color: sRGB color space
- Format: MP4 with H.264 encoding

---

## Success Criteria

### MVP (48 hours)
- ✅ End-to-end video generation from natural language prompts
- ✅ Real-time progress updates
- ✅ Basic video editing (cut, trim, reorder)
- ✅ Brand consistency enforcement
- ✅ Professional-quality output
- ✅ Web-based interface

### Final Submission (8 days)
- Enhanced editing capabilities
- Advanced brand management
- Performance optimizations
- Production deployment
- Comprehensive testing

---

## Constraints & Assumptions

### Timeline
- **MVP Deadline:** 48 hours from project start
- **Final Deadline:** November 22, 2025
- **Team:** 4 parallel workstreams (DevOps, Frontend, AI Backend, FFmpeg)

### Budget
- Use cheaper AI models during development
- Smart caching for repeated elements
- S3 lifecycle policies (7-day auto-delete)
- Cost monitoring and alerting

### Technical
- AWS infrastructure (RDS, ElastiCache, S3, ECS)
- Docker-based development environment
- Hot reload for development
- Production deployment via ECS Fargate

---

## Risk Mitigation

### High Priority
1. **48-hour MVP deadline** → Parallel workstreams, focus on core features
2. **Backend team dependency** → Clear API contracts, early integration
3. **AWS credentials timing** → User provides as needed, proceed with documentation

### Medium Priority
1. **Multiple agents coordination** → Strict file locking, commit policy
2. **Integration complexity** → Early testing, clear contracts

---

## Current Status

**Phase:** Active Development (Hour ~24/48 for MVP)
**Progress:** Video generation pipeline working end-to-end with real MP4 output
**Blockers:** None currently - all core systems integrated and functional

---

## Key Decisions Made

1. **Deployment Strategy** → Option B (FastAPI serves static files)
2. **Theme** → Cyberpunk aesthetic with dark backgrounds, neon accents
3. **Storage** → Environment-aware service (S3 prod, local dev)
4. **Architecture** → Async webhook-based generation (no polling)
5. **Model** → wan-video/wan-2.2-t2v-fast for quality video generation</contents>
</xai:function_call<parameter name="contents"># Active Context - Current Work Focus

**Purpose:** What's happening right now, recent changes, current focus areas.

**Last Updated:** 2025-11-17 by Silver (Model configuration fixes and storage logging)

---

## Current Sprint Focus

**Phase:** MVP Completion & Polish
**Timeline:** MVP deadline approaching (48 hours total)
**Active Agents:** Silver (integration & debugging)

---

## In-Flight Work

### Just Completed
- ✅ **Model Configuration Fixed**: Updated docker-compose.yml and example.env to use `wan-video/wan-2.2-t2v-fast` instead of hardcoded `google/veo-3.1-fast`
- ✅ **Enhanced Logging Added**: Comprehensive logging for Replicate prediction URLs and storage locations
- ✅ **Video Generation Verified**: End-to-end pipeline working with proper model selection and webhook integration
- ✅ **Webhook Completion Fix**: Replicate webhook now promotes generations to `completed`/`failed`, updates the in-memory fallback store, and emits WebSocket status changes so the UI exits the loading screen.

### Current Focus
- **Memory Bank Updates**: Documenting all recent changes and current system state
- **Commit Documentation**: Recording all substantive code changes in commits directory
- **Final Integration Testing**: Ensuring all components work together seamlessly

---

## Recent Decisions

1. **Model Configuration** (2025-11-17)
   - **Decision:** Use `wan-video/wan-2.2-t2v-fast` as default model (user preference)
   - **Implementation:** Added `REPLICATE_DEFAULT_MODEL` to docker-compose.yml and example.env
   - **Rationale:** User has specific model requirements from their environment setup

2. **Storage Logging Enhancement** (2025-11-17)
   - **Decision:** Add detailed logging for Replicate URLs and storage locations
   - **Implementation:** Enhanced webhook handler and ffmpeg-backend with comprehensive logging
   - **Rationale:** Need visibility into generation process and access to created videos

---

## Current Questions & Blockers

### Resolved
- ✅ Model configuration - now properly reads from environment variables
- ✅ Video generation URLs - now logged with direct Replicate links
- ✅ Storage locations - now logged with S3/local paths

### Open
- None currently - system is fully integrated and functional

---

## Next Up (Post-MVP)

**Testing & Polish:**
- End-to-end integration testing
- Performance optimization
- User experience refinements
- Production deployment preparation

---

## Communication Log

**2025-11-17** - Silver: Fixed model configuration to use wan-video/wan-2.2-t2v-fast, added comprehensive logging for Replicate URLs and storage locations, verified end-to-end video generation pipeline working correctly.
