# AI Backend & API Gateway Team PRD (Updated Draft)
*AI Planning, Orchestration, and Backend Intelligence*

## 1. Overview

This document defines the product and engineering requirements for the **AI Backend & API Gateway Team** within the AI Video Generation Pipeline project. It focuses on:

- Prompt analysis and enhancement  
- Scene and timeline planning  
- Brand/style/visual consistency logic  
- Audio-driven planning using beat metadata  
- Model orchestration (OpenAI, Replicate, others)  
- Natural-language-driven video editing (AI-assisted trimming, reordering, CTA timing adjustments)  
- Orchestration logic within the API gateway  
- Backend APIs for the frontend and FFmpeg services  
- Internal architecture and module responsibilities  

This PRD is derived from the project-level PRD but focuses exclusively on the responsibilities, deliverables, and interactions of the AI Backend team.

The final deliverable is an AI-driven orchestration engine capable of translating user prompts, brand requirements, and optional audio into structured scene plans and clip-generation requests, then coordinating FFmpeg composition, progress reporting, and natural-language edits.

## 2. Team Scope

### In Scope
- Prompt Parsing & Enhancement using LLMs
- Scene Planning Engine for ads and music pipelines
- AI Model Orchestration for clip generation
- API Gateway Orchestration (complex logic routing)
- AI-Assisted Editing Logic for natural-language edit requests
- Style & Brand Consistency Logic
- Clip-Oriented Metadata Storage

### Post-MVP Features
- Beat & Audio Integration using FFmpeg's audio-analysis API
- Rhythm-synchronized scene timing
- Tempo-aware visual pacing

### Out of Scope
- CTA rendering (owned by Frontend + FFmpeg)  
- Video encoding, trimming, transitions  
- UI for editing or preview  
- Authentication/session handling  
- Infrastructure/build/deployment (DevOps)  

## 3. Objectives

1. Convert freeform prompts + assets into structured clip sequences.  
2. Support both ad and music video pipelines with consistent planning.  
3. Provide a stable, well-defined API for frontend and FFmpeg backend teams.  
4. Enable natural-language editing using AI-driven interpretation.  
5. Ensure predictable orchestration flows across the system.  
6. Provide comprehensive progress tracking and recovery.

## 4. Functional Requirements

### 4.1 Prompt Processing & Enhancement
- Interpret user prompt into narrative, style, pacing, and brand constraints  
- Produce structured storyboard + micro-prompts  
- Provide fallback heuristics when user prompt is underspecified

### 4.2 Scene Planning Engine
**Ads (15–60s):**
- 3–5 scenes  
- Shot diversity + brand alignment  

**Music Videos (60–180s):**
- 10–20 scenes
- Scene boundaries based on duration-based heuristics (post-MVP: beat synchronization)

### 4.3 Scene Timing Planning
- For MVP: Duration-based scene distribution for music videos
- Post-MVP: Beat-aligned planning consuming audio metadata from FFmpeg
- Align scenes to content pacing and narrative flow  

### 4.4 Clip Generation Orchestration
- Build micro-prompts  
- Trigger video model generation  
- Manage clip ordering, metadata, progress  

### 4.5 Natural-Language Editing Mode
- Interpret edit instructions (trim/crop/swap/timing)  
- Produce `edit_plan`  
- If `apply_immediately` == true: trigger FFmpeg recomposition automatically  

## 5. API Requirements

### 5.1 Frontend-Facing APIs
- `POST /api/v1/generations`  
- `GET /api/v1/generations/{id}`  
- `POST /api/v1/compositions/{id}/edit`  

### 5.2 Internal Service APIs
- `POST /internal/v1/audio-analysis` (beat detection)  
- `POST /internal/v1/process-clips`  
- `POST /internal/v1/processing-complete`  

## 6. Internal Architecture

### Modules
- Prompt Analysis Module  
- Scene Planner  
- Style Consistency Engine  
- Clip Builder  
- Gateway Orchestrator  
- Edit Interpreter  

## 7. Data Flows

### Ad Pipeline Flow
1. Prompt → AI Backend  
2. Scene Plan → Clip Micro-prompts  
3. Model Generation → Clips  
4. FFmpeg Composition → Final Video  

### Music Pipeline Flow
1. Prompt + Audio → AI Backend
2. Duration-based scene planning (MVP) / Beat analysis (post-MVP)
3. Clip Gen → FFmpeg
4. Final Video

**Note:** Post-MVP flow includes: AI Backend → FFmpeg for beat detection → Beat metadata → Scene planning  

### Edit Flow
1. Natural-language edit → AI Backend  
2. `edit_plan` → Confirmation or Immediate Apply  
3. FFmpeg recomposition  

## 8. Engineering Guidance

### 8.1 Prompt Patterns
- Break into: Overview → Scenes → Shots  
- Use stable visual anchors for consistency  
- Enforce brand colors early in the prompt  

### 8.2 Scene Duration Heuristics
- Ads: 4–7s  
- Music: 1–4 bars depending on bpm  

### 8.3 Beat Mapping
- Prefer downbeat-aligned boundaries  
- If close to next bar, snap to bar start  

### 8.4 Style Consistency
- Maintain a stable "style vector" text description  
- Use repeating visual anchors (color scheme, environmental traits, lighting)  
- Avoid contradictory styles  

### 8.5 Error Handling Strategy
- Model retries for transient failures  
- Graceful fallback if no beat metadata returns  
- Repair malformed user instructions gracefully  
- Use OpenAI to re-evaluate inconsistent edit requests  

## 9. Non-Functional Requirements

- <500ms status API latency  
- <30s per orchestrator API call  
- Support 5 concurrent full pipelines  
- Stable orchestration even when FFmpeg or Replicate are slow  
- Deterministic orchestration state machine  

## 10. Acceptance Criteria

1. Generates structured scenes reliably for both pipelines
2. Duration-based scene timing works for music videos (MVP)
3. Natural-language edits produce correct timeline diffs
4. API gateway orchestrates without deadlocks or loops
5. Style consistency across clips meets design requirements
6. All endpoints fully documented and integrated

**Post-MVP Criteria:**
- Beat-driven planning works end-to-end
- Audio analysis integration with FFmpeg  

## 11. Anticipated Python Library Stack (Python 3.13.9 Compatible)

### Core Frameworks
- FastAPI 0.115.7  
- Uvicorn 0.32.0  
- Pydantic 2.14.8  

### AI / Model Interaction
- openai 1.52.0  
- replicate 0.31.0  
- tenacity 9.0.0  

### Async Processing & Orchestration
- Celery 5.4.0  
- Redis 5.2.1  
- aiohttp 3.10.10  
- httpx 0.28.1  

### Data & Storage
- SQLAlchemy 2.0.36  
- asyncpg 0.30.0  
- psycopg[binary] 3.2.4  

### Utilities
- python-dotenv 1.0.1  
- loguru 0.7.2  
- orjson 3.10.7  
- numpy 2.2.1  
- scipy 1.14.2  

### Testing
- pytest 8.4.3  
- pytest-asyncio 0.23.5  
- httpx-mock 0.20.0  
