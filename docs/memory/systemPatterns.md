# System Patterns - Architecture Decisions

**Purpose:** Track architectural decisions and patterns established during implementation.

**Last Updated:** 2025-11-14 by Orange

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

*(To be populated as implementation progresses)*

---

## Integration Patterns

*(To be populated as backend/frontend/ffmpeg integration patterns emerge)*

---

## Data Flow Patterns

*(To be populated as video generation pipeline is implemented)*
