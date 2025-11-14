# AI Backend & Gateway – MVP Task Breakdown (Draft 1, Full Version)

---

# 🔴 BLOCK 0 (P0): API Skeleton & Core Infrastructure
**Purpose:** Unblock all teams. Establish API routes, shared models, error format, and system-wide request/response structures.  
**Dependencies:** None  
**Parallelizable:** Must be completed before all other blocks begin  
**Total Time:** ~20–28 hours  
**Impact:** Critical path for entire project

---

## PR #001: FastAPI Project Bootstrap & Routing Structure **(COMPLETED - Orange)**
**Prerequisites:** None
**Time:** 4–6 hours
**Impact:** Creates the project foundation

### Tasks:
- [x] Initialize FastAPI project layout
- [x] Create `/api/v1/` and `/internal/v1/` routers
- [x] Add health endpoints (`/health`, `/health/detailed`)
- [x] Set up logging middleware with request IDs
- [x] Add startup/shutdown lifecycle hooks  

### Files Created:
- `app/main.py`  
- `app/api/routes/`  
- `app/core/config.py`  
- `app/core/logging.py`

### Testing:
- [ ] Unit: Router registration  
- [ ] Unit: Health endpoints  
- [ ] Unit: Logging middleware  

### Validation:
- [ ] cURL test of base routes  
- [ ] Service boots cleanly with no errors  

---

## PR #002: Error Handling, Validation, and Response Models **(COMPLETED - Orange)**
**Prerequisites:** PR #001
**Time:** 4–6 hours
**Impact:** Required for consistent API behavior across teams

### Tasks:
- [x] Implement global exception handler
- [x] Define `ErrorResponse`, `GenerationResponse`, `ProgressResponse` schemas
- [x] Centralize validation logic
- [x] Set up shared enums (status, aspect ratio, etc.)  

### Files Modified:
- `app/models/schemas.py`  
- `app/core/errors.py`  

### Testing:
- [ ] Unit: Error handler returns correct format  
- [ ] Unit: Validation rejects invalid prompts  
- [ ] Integration: Endpoints return standardized errors  

### Validation:
- [ ] Test invalid/malformed requests from frontend  

---

## PR #003: Generation Lifecycle API Skeleton **(COMPLETED - White)**
**Prerequisites:** PR #002
**Time:** 4–5 hours
**Impact:** Frontend is fully unblocked

### Tasks:
- [x] Stub `POST /api/v1/generations`
- [x] Stub `GET /api/v1/generations/{id}`
- [x] Add placeholder Redis + Postgres integration points
- [x] Ensure correct async patterns

### Testing:
- [x] Unit: Route resolves
- [x] Unit: Schema validation
- [x] Integration: Smoke test with mock data

### Validation:
- [x] Frontend is able to call all endpoints without model logic  

---

## PR #004: Internal Service Contract & Callouts (FFmpeg Integration Skeleton) **(COMPLETED - Blonde)**  
**Prerequisites:** PR #003  
**Time:** 4–6 hours  
**Impact:** FFmpeg backend becomes unblocked

### Tasks:
- [ ] Stub `/internal/v1/audio-analysis`  
- [ ] Stub `/internal/v1/process-clips`  
- [ ] Stub `/internal/v1/processing-complete`  
- [ ] Define request/response schemas  

### Testing:
- [ ] Unit: Schema compliance  
- [ ] Integration: Mock FFmpeg service call  

### Validation:
- [ ] FFmpeg team validates contract shape  

---

## BLOCK 0 Integration PR – PR #005  
**Prerequisites:** PR #001–#004  
**Time:** 2–3 hours  
**Impact:** Confirms full skeleton functionality

### Tests:
- [ ] End-to-end API smoke test  
- [ ] Contract validation with frontend & FFmpeg  
- [ ] 100% test pass on skeleton  

---

# 🟢 BLOCK A: Prompt Processing & Enhancement  
*(Scene understanding, brand parsing, tone extraction)*  
**Dependencies:** BLOCK 0  
**Parallelizable:** Yes  
**Total Time:** 20–30 hours

---

## PR #101: Prompt Parsing Module (OpenAI Integration)  
**Time:** 6 hours  
**Purpose:** Convert raw user prompt into structured semantic info

### Tasks:
- [ ] Implement `PromptAnalysisService`  
- [ ] Extract tone, style, product focus, narrative intent  
- [ ] Implement OpenAI call + retry policy  
- [ ] Add guardrails (max tokens, safety filters)  

### Testing:
- [ ] Unit: LLM request  
- [ ] Unit: Parsed response schema  
- [ ] Integration: Mock OpenAI and test failures  

---

## PR #102: Brand & Metadata Extraction Layer  
**Prerequisites:** PR #101  
**Time:** 4 hours  

### Tasks:
- [ ] Parse branding JSON  
- [ ] Merge with LLM descriptors  
- [ ] Establish style vector placeholder  

### Testing:
- [ ] Unit: brand extraction  
- [ ] Unit: fallback defaults  

---

## PR #103: Scene Decomposition (Ads & Music)  
**Prerequisites:** PR #102  
**Time:** 6–8 hours

### Tasks:
- [ ] Ads: 3–5 scene decomposition  
- [ ] Music: 10–20 scene decomposition  
- [ ] Duration & style heuristics  

### Testing:
- [ ] Unit: scene distribution logic  
- [ ] Integration: prompt → scene plan  

---

## BLOCK A Integration PR – PR #104  
**Prerequisites:** #101–#103  
**Time:** 4 hours  

### Tests:
- [ ] Full flow: prompt → parsed → scenes  
- [ ] Failure handling  
- [ ] Schema validation  

---

# 🟣 BLOCK B: Scene Planning & Beat-Aligned Timeline (Post-MVP)
*(Beat integration and scene-time alignment)*
**Dependencies:** MVP Complete
**Parallelizable:** Yes
**Total Time:** 18–25 hours
**Status:** Phase 2 feature, not required for MVP

---

## PR #201: Audio Analysis Client (FFmpeg Consumer)  
**Time:** 4–5 hours  

### Tasks:
- [ ] Implement `AudioAnalysisService`  
- [ ] Call `/internal/v1/audio-analysis`  
- [ ] Normalize beat/downbeat/energy structure  

### Testing:
- [ ] Unit: request formatting  
- [ ] Integration: mock FFmpeg  

---

## PR #202: Beat-Aligned Scene Timing Module  
**Prerequisites:** PR #201  
**Time:** 6–7 hours  

### Tasks:
- [ ] Map scenes to downbeats  
- [ ] Snap boundaries to musical structure  
- [ ] Fallback timing if no beats  
- [ ] Add intensity/energy hints  

### Testing:
- [ ] Unit: beat snapping  
- [ ] Unit: fallback logic  
- [ ] Integration: scene plan + beat data → timeline  

---

## PR #203: Combined Ad/Music Planner Interface  
**Prerequisites:** PR #202  
**Time:** 4–6 hours  

### Tasks:
- [ ] Unified planner interface  
- [ ] Planner selection logic  
- [ ] Metrics logging and debug mode  

### Testing:
- [ ] Unit: routing logic  
- [ ] Integration: complete planner flow  

---

## BLOCK B Integration PR – PR #204  
**Time:** 3–4 hours  

### Tests:
- [ ] audio → beats → aligned scenes  
- [ ] ad planning smoke tests  

---

# 🟡 BLOCK C: Clip Generation Orchestration  
*(Model calls, micro-prompts, clip metadata)*  
**Dependencies:** BLOCK A  
**Parallelizable:** Yes  
**Total Time:** 22–30 hours

---

## PR #301: Micro-Prompt Builder  
**Time:** 6 hours  

### Tasks:
- [ ] Convert scenes → model prompts  
- [ ] Integrate brand + style vectors  
- [ ] Include shot descriptors  

### Testing:
- [ ] Unit: micro-prompt formatting  
- [ ] Integration: scenes → prompts  

---

## PR #302: Replicate Model Client  
**Prerequisites:** PR #301  
**Time:** 4–6 hours  

### Tasks:
- [ ] Async client wrapper  
- [ ] Retry with backoff  
- [ ] Parse clip metadata  

### Testing:
- [ ] Unit: client I/O  
- [ ] Integration: mock Replicate  

---

## PR #303: Clip Assembly & DB/Redis Integration  
**Prerequisites:** PR #302  
**Time:** 6–8 hours  

### Tasks:
- [ ] Save clip metadata  
- [ ] Update progress in Redis  
- [ ] Maintain clip ordering  

### Testing:
- [ ] Unit: DB writes  
- [ ] Integration: full clip generation pipeline  

---

## BLOCK C Integration PR – PR #304  
**Time:** 3–4 hours  

### Tests:
- [ ] scenes → prompts → clips  
- [ ] model failure simulation  

---

# 🔵 BLOCK D: AI-Assisted Editing  
*(Interpretation, timeline operations, recompose triggers)*  
**Dependencies:** BLOCK A & C  
**Parallelizable:** Yes  
**Total Time:** 20–25 hours

---

## PR #401: Edit Intent Classifier (OpenAI)  
**Time:** 4–5 hours  

### Tasks:
- [ ] Trim/swap/reorder classification  
- [ ] CTA timing detection  
- [ ] Safety guardrails  

### Testing:
- [ ] Unit: classifier logic  
- [ ] Integration: mock OpenAI  

---

## PR #402: Timeline Edit Planner  
**Prerequisites:** PR #401  
**Time:** 6–8 hours  

### Tasks:
- [ ] Clip index mapping  
- [ ] Implement trim logic  
- [ ] Implement reorder logic  
- [ ] Implement overlay timing changes  

### Testing:
- [ ] Unit: timeline transforms  
- [ ] Integration: edit → plan  

---

## PR #403: Recomposition Trigger  
**Prerequisites:** PR #402  
**Time:** 4–6 hours  

### Tasks:
- [ ] Build updated composition config  
- [ ] Trigger FFmpeg job  
- [ ] Persist recomposition record  

### Testing:
- [ ] Unit: config generation  
- [ ] Integration: plan → FFmpeg recomposition  

---

## BLOCK D Integration PR – PR #404  
**Time:** 3 hours  

### Tests:
- [ ] Natural-language edit → recomposed job  
- [ ] Validate behavior against PRD examples  

---

# 🟠 BLOCK E: Style/Brand Consistency Engine  
*(Shared across all scenes and clips)*  
**Dependencies:** BLOCK A  
**Parallelizable:** Yes  
**Total Time:** 15–20 hours

---

## PR #501: Style Vector Builder  
**Time:** 4 hours  

### Tasks:
- [ ] Derive style vector from prompt metadata  
- [ ] Normalize descriptor structure  

### Testing:
- [ ] Unit: style extraction  

---

## PR #502: Brand Harmony Module  
**Prerequisites:** PR #501  
**Time:** 4–5 hours  

### Tasks:
- [ ] Combine palette + style vector  
- [ ] Detect conflicts  

### Testing:
- [ ] Unit: conflict detection  

---

## PR #503: Consistency Enforcement Layer  
**Prerequisites:** PR #502  
**Time:** 5–7 hours  

### Tasks:
- [ ] Inject visual anchors into micro-prompts  
- [ ] Detect style inconsistencies  
- [ ] Integrate with clip generation pipeline  

### Testing:
- [ ] Unit: anchor correctness  
- [ ] Integration: scenes → prompts (consistent)  

---

## BLOCK E Integration PR – PR #504  
**Time:** 3 hours  

### Tests:
- [ ] scene → prompt consistency  
- [ ] brand alignment  

---

# 🟣 BLOCK Z: End-to-End Integration, QA, & Contract Testing  
**Dependencies:** BLOCKS 0, A, B, C, D, E  
**Parallelizable:** No  
**Total Time:** 12–20 hours  
**Purpose:** Ensure entire AI backend works cohesively with FFmpeg + Frontend  

---

## PR #901: Block-Level Integration Tests  
**Time:** 4–6 hours  

### Tests:
- [ ] Integration suite for A, B, C, D, E  
- [ ] Mock FFmpeg + Replicate  
- [ ] Schema consistency validation  

---

## PR #902: Full-System Pipeline Test  
**Prerequisites:** PR #901  
**Time:** 4–6 hours  

### Tests:
- [ ] Prompt → scenes → micro-prompts → clips → FFmpeg job  
- [ ] Music pipeline with audio → beats → aligned clips  
- [ ] Natural-language edit pipeline  

---

## PR #903: External Contract Validation  
**Prerequisites:** PR #902  
**Time:** 2–4 hours  

### Tasks:
- [ ] Validate all public APIs with frontend team  
- [ ] Validate all internal APIs with FFmpeg backend  
- [ ] Run failure-mode tests (rate limits, invalid prompts, malformed edits)  

---

## PR #005: Block 0 Integration PR **(COMPLETED - QC)**
**Prerequisites:** PR #001–#004
**Time:** 2–3 hours
**Impact:** Confirms full skeleton functionality

### Tests:
- [x] End-to-end API smoke test
- [x] Contract validation with frontend & FFmpeg
- [x] 100% test pass on skeleton

---

# 📊 Dependency Graph Summary
BLOCK 0 (P0) ── MVP Critical Path ──┐
│                                     │
├── BLOCK A (Prompt Processing)       │
│                                     │
├── BLOCK C (Clip Generation) ────────┼──→ BLOCK Z (Integration)
│                                     │
├── BLOCK D (AI-Assisted Editing)     │
│                                     │
└── BLOCK E (Style/Brand Consistency) │
                                      │
BLOCK B (Beat + Scene Timing) ────────┘
*(Post-MVP - Phase 2)*