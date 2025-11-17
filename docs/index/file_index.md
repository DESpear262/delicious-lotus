# File Index - AI Backend & Gateway

This index tracks all files created during the AI Backend development process.

## FastAPI Backend Files

### Core Application Files
- `fastapi/app/main.py` - Main FastAPI application with lifespan management and middleware
- `fastapi/app/core/config.py` - Application configuration settings
- `fastapi/app/core/logging.py` - Logging configuration with request ID tracking
- `fastapi/app/core/errors.py` - Global exception handlers and error responses

### API Routes
- `fastapi/app/api/routes/v1.py` - Public API v1 endpoints for video generation
- `fastapi/app/api/routes/internal_v1.py` - Internal API v1 endpoints for FFmpeg integration (PR #004)

### Data Models
- `fastapi/app/models/schemas.py` - Pydantic models and schemas for all API endpoints

### Tests
- `fastapi/tests/test_basic.py` - Basic application tests
- `fastapi/tests/test_v1_routes.py` - Tests for public API v1 endpoints
- `fastapi/tests/test_internal_routes.py` - Tests for internal API v1 endpoints (PR #004)

## Documentation Files

### Project Requirements
- `docs/prd.md` - Product Requirements Document
- `docs/prd-edited.md` - Edited version of PRD with updates
- `docs/ai-backend-prd.md` - AI Backend specific requirements
- `docs/ffmpeg-backend-prd.md` - FFmpeg Backend requirements
- `docs/api-specification.md` - API specification document
- `docs/api-specification-edited.md` - Edited API specification

### Task Management
- `docs/ai-backend-tasks-list.md` - Detailed task breakdown for AI backend
- `docs/task-list-devops.md` - DevOps task list
- `docs/task-list-frontend.md` - Frontend task list

### Memory Bank
- `docs/memory/projectbrief.md` - Project brief and foundation (pending)
- `docs/memory/productContext.md` - Product context and goals (pending)
- `docs/memory/activeContext.md` - Current work status and focus
- `docs/memory/systemPatterns.md` - System architecture decisions
- `docs/memory/techContext.md` - Technology stack and constraints
- `docs/memory/progress.md` - Implementation progress and status

### Setup and Deployment
- `docs/local-setup.md` - Local development environment setup

## AI Processing Backend Files

### Core Services
- `ai/core/openai_client.py` - OpenAI API client wrapper
- `ai/services/brand_analysis_service.py` - Brand configuration analysis (PR #102)
- `ai/services/prompt_analysis_service.py` - User prompt semantic analysis (PR #101)
- `ai/services/scene_decomposition_service.py` - Video scene planning (PR #103)
- `ai/services/style_vector_builder_service.py` - Style vector generation (PR #501)
- `ai/services/brand_harmony_service.py` - Brand color harmony analysis (PR #502)
- `ai/services/timeline_edit_planner_service.py` - Timeline edit planning (PR #402)
- `ai/services/micro_prompt_builder_service.py` - Micro-prompt generation for clips

### Data Models
- `ai/models/brand_config.py` - Brand configuration models (PR #102)
- `ai/models/brand_style_vector.py` - Style vector models (PR #102)
- `ai/models/brand_harmony.py` - Brand harmony analysis models (PR #502)
- `ai/models/prompt_analysis.py` - Prompt analysis result models (PR #101)
- `ai/models/scene_decomposition.py` - Scene planning models (PR #103)

### Tests
- `ai/tests/test_prompt_analysis.py` - Prompt analysis service tests
- `ai/tests/test_scene_decomposition.py` - Scene decomposition tests
- `ai/tests/test_scene_integration.py` - End-to-end integration tests
- `test_real_video.py` - Real Replicate video generation integration test
- `ai/tests/test_style_vector_builder.py` - Style vector builder tests (PR #501)
- `ai/tests/test_brand_harmony.py` - Brand harmony analysis tests (PR #502)
- `ai/tests/test_timeline_edit_planner.py` - Timeline edit planner tests (PR #402)
- `ai/tests/test_consistency_enforcement.py` - Consistency enforcement tests (PR #503)

### Configuration
- `ai/requirements.txt` - Python dependencies for AI processing
- `ai/README.md` - AI processing module documentation
- `ai/cli.py` - Interactive CLI for testing AI modules
- `ai/setup_cli.py` - CLI setup and environment verification script
- `run_ai_cli.py` - CLI launcher script (project root)

## Infrastructure Files

### Docker
- `docker-compose.yml` - Root docker-compose configuration with all services (main backend, FFmpeg backend API, FFmpeg backend worker, postgres, redis)
- `docker/postgres/init.sql` - Main database initialization (ai_video_pipeline)
- `docker/postgres/init-ffmpeg-db.sh` - FFmpeg backend database initialization script (creates ffmpeg_backend database)
- `docker/postgres/init-ffmpeg-db.sql` - Reference SQL file (actual creation done via shell script)
- `docker/redis/redis.conf` - Redis configuration

### FastAPI Backend
- `fastapi/requirements.txt` - Python dependencies
- `fastapi/README.md` - Backend documentation

## Frontend Files

### React Application
- `frontend/package.json` - Node.js dependencies
- `frontend/vite.config.ts` - Vite build configuration
- `frontend/tsconfig.json` - TypeScript configuration
- `frontend/eslint.config.js` - ESLint configuration
- `frontend/index.html` - HTML entry point with Google Fonts (Inter, Orbitron, JetBrains Mono)

### Frontend Styling & Theme
- `frontend/src/styles/globals.css` - Global CSS variables and cyberpunk theme tokens
- `frontend/src/styles/components.css` - Base component styles with dark theme
- `frontend/src/styles/animations.css` - Cyberpunk animations (neon glow, shimmer, scanlines)
- `frontend/src/styles/responsive.css` - Responsive design breakpoints
- `frontend/src/components/ui/Button.module.css` - Button component with neon styling
- `frontend/src/components/ui/Card.module.css` - Card component with glassmorphism effects
- `frontend/src/components/ui/Input.module.css` - Input component with dark theme
- `frontend/src/components/ui/Textarea.module.css` - Textarea component with dark theme
- `frontend/src/components/ui/ConfirmDialog.module.css` - ConfirmDialog styling with cyberpunk theme
- `frontend/src/layouts/MainLayout.module.css` - Main layout with backdrop blur and neon borders

### Frontend Form Validation
- `frontend/src/utils/formValidation.ts` - Form validation rules (updated: removed 500-char minimum)
- `frontend/src/components/GenerationForm/PromptInput.tsx` - Prompt input component (updated: removed character limit validation)

### Frontend UI Components
- `frontend/src/components/ui/ConfirmDialog.tsx` - Custom confirmation dialog component with customizable buttons
- `frontend/src/components/ui/ConfirmDialog.module.css` - Styling for ConfirmDialog with cyberpunk theme
- `frontend/src/components/ui/index.ts` - UI components export index

### Frontend Hooks
- `frontend/src/hooks/useFormPersistence.ts` - Form draft persistence hook with localStorage (updated: uses ConfirmDialog instead of window.confirm)
- `frontend/src/hooks/useGenerationForm.ts` - Generation form state management hook (updated: exposes ConfirmDialog state)

### Frontend Pages
- `frontend/src/pages/AdCreativeForm.tsx` - Ad creative generation form page (updated: renders ConfirmDialog for draft restoration)

## Agent Coordination

### Identity Management
- `.claude/agent-identity.lock` - Agent identity tracking

### Commits
- `commits/Orange/` - Orange agent commit records
- `fastapi/commits/Orange/` - Backend-specific Orange commits
- `commits/Blonde/` - Blonde agent commit records (PR #004)
- `commits/Blue/` - Blue agent commit records (Frontend theme implementation, prompt validation fixes)
- `commits/Silver/` - Silver agent commit records (Vite dev proxy for frontend API/WebSocket traffic)

## Root Files

- `requirements.txt` - Consolidated Python dependencies from all modules
- `LICENSE` - Project license
- `README.md` - Project overview (pending)
- `bughunt.md` - Transcribed notes from the front-end bughunt on 2025-11-15
