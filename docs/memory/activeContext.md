# Active Context - Current Work Focus

**Purpose:** What's happening right now, recent changes, current focus areas.

**Last Updated:** 2025-11-22 by Agent (Generation Fixes)

---

## Current Sprint Focus

**Phase:** MVP Completion & Polish
**Timeline:** MVP deadline approaching (48 hours total)
**Active Agents:** Orange (debugging)

---

## In-Flight Work

### Just Completed
- ✅ **Fix Video Generation Pipeline**: Connected frontend "Generate" button to advanced AI pipeline (prompt analysis -> scene decomposition -> micro-prompts -> video generation).
- ✅ **Fix Replicate API Integration**: Resolved `422 Unprocessable Entity` by correcting resolution format from `1280x720` to `1280*720` for Wan Video 2.5 model.
- ✅ **Fix NameError**: Restored missing `generate_video_clips` function in backend.
- ✅ **Self-Healing Logic**: Implemented logic to auto-update "processing" generations from Redis if webhooks fail (e.g. local dev without tunnel).
- ✅ **Real-time Updates**: Added WebSocket broadcasting for individual clip completion events (`generation:{id}`) so frontend Info Board updates live.
- ✅ **Frontend UX**: Removed blocking "Loading generation status" screen, allowing immediate view of progress board.

### Just Completed (Previous)
- ✅ **Fix Empty History List**: Resolved issue where generation history was empty even with active jobs. Updated `list_generations` to merge results from both database and in-memory store, ensuring that jobs existing only in memory (due to dev setup or persistence lag) are visible.
- ✅ **Fix History Page Crash**: Resolved `TypeError` in GenerationCard.tsx by ensuring `generation_id` is correctly mapped in API responses.
- ✅ **Backend Startup Fixes**: Resolved crashing issues due to logging configuration (case sensitivity) and `UnboundLocalError` in `app/main.py`.
- ✅ **Model Configuration Fixed**: Updated docker-compose.yml and example.env to use `wan-video/wan-2.2-t2v-fast` instead of hardcoded `google/veo-3.1-fast`

### Ready to Start
**AI**
- 🎯 **Block 0 PR 3: Generation Lifecycle API Skeleton** (4-5h) - UNBLOCKED
- 🎯 PR-D003: Storage Documentation (1h)
- 🎯 PR-D005: Environment Config Templates (2h)
- 🎯 PR-D009: Deployment Documentation (2h)
- 🎯 PR-F002: Design System Foundation (3h) - dependencies met
- 🎯 PR-F003: API Client Setup (2h) - dependencies met
- 🎯 PR-F016: User Documentation (2h)

### Blocked & Waiting
- ⏸️ PR-D002: Backend Docker Container (waiting for backend team's FastAPI structure)
- ⏸️ PR-D004-D008: DevOps PRs blocked by PR-D002 or user AWS setup
- ⏸️ PR-F004-F015: Frontend PRs blocked by PR-F003, PR-F004, or PR-F005
- ⏸️ User AWS setup tasks (Tasks 2, 4, 5)

---

## Recent Decisions

1. **Real-time Clip Broadcasting** (2025-11-22)
   - **Decision:** Broadcast `clip_completed` events to `generation:{id}` WebSocket channel in addition to job-specific channels.
   - **Context:** Frontend Info Board listens to generation-level updates, but backend was only sending low-level job updates.
   - **Rationale:** Enables granular, real-time UI updates as each video clip finishes, without full page refresh.

2. **Self-Healing Generation Status** (2025-11-22)
   - **Decision:** `get_generation` endpoint proactively checks Redis for status updates if generation is "processing" but has no progress.
   - **Context:** Local development often lacks public webhooks, causing generations to appear stuck.
   - **Rationale:** Improves resilience and developer experience by recovering state from Redis cache even if webhook callbacks are dropped.

3. **Hybrid History Retrieval** (2025-11-22)
   - **Decision:** Merge database and in-memory generation records in `list_generations` API.
   - **Context:** Local dev environment often has split state (active jobs in memory, old jobs in DB), leading to "missing" videos in history.
   - **Rationale:** Ensures robust user experience where "what I just made" is always visible, regardless of persistence latency or configuration issues.

4. **API Response Mapping** (2025-11-22)
   - **Decision:** Map database columns to API fields explicitly in route handlers.
   - **Context:** Frontend crash due to missing `generation_id`.
   - **Rationale:** Keeps service layer clean, handles mapping at the API boundary.

---

## Current Questions & Blockers

### Resolved
- ✅ **Stuck Generations** -> Fixed by Replicate resolution fix and self-healing logic.
- ✅ **Missing Real-time Updates** -> Fixed by broadcasting to correct WebSocket channel.
- ✅ **Empty History List** -> Fixed by merging in-memory and DB results.
- ✅ **Crash in Generation History page** -> Fixed by mapping `id` to `generation_id`.

### Open
- How aggressively should we rely on database/Redis vs in-memory fallbacks for local development when Postgres schema is out of sync? (Current approach: aggressive fallback to in-memory for UX safety).

---

## Next Up (After Current PRs)

**DevOps:**
- PR-D003: Storage Documentation
- PR-D009: Deployment Documentation

**Frontend:**
- PR-F003: API Client
- PR-F005: Routing/Layout

---

## Communication Log

**2025-11-22** - Agent: Connected generation workflow, fixed Replicate API integration, implemented self-healing for stuck jobs, and enabled real-time clip updates on frontend.
**2025-11-22** - Orange: Fixed empty history list issue by implementing hybrid retrieval strategy (DB + Memory) in `list_generations` endpoint. This ensures active jobs are visible even if not yet fully persisted to DB.
**2025-11-22** - Orange: Fixed critical crash in History page where generations fetched from database were missing `generation_id` field required by frontend.
