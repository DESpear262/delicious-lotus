# Task List - Frontend Track (REVISED)
## AI Video Generation Pipeline

### Overview
This task list covers the React/Vite web application for the video generation pipeline. Team 1 (DevOps + Frontend) is responsible for these tasks.

**MVP Focus:** Ad Creative Pipeline interface (15-60 seconds)
**Post-MVP:** Add Music Video Pipeline interface (1-3 minutes)
**Timeline:** 48 hours to MVP, 8 days total

**DEPLOYMENT APPROACH:** Frontend builds to static files, served by FastAPI backend (Option B)

---

## PR Status Summary

**Completed:** 3/16+ ✅
**Unblocked (Ready to Start):** 4
**Blocked (Dependencies Not Met):** 9+
**Total Remaining:** 13+ tasks

**COMPLETED FOUNDATION:**
- ✅ PR-F001: Project structure with React 19 + Vite + TypeScript
- ✅ PR-F002: Complete design system (CSS variables, base components)
- ✅ PR-F003: API client with all service modules and error handling

---

## Currently Unblocked PRs (Ready to Start)

### PR-F004: WebSocket Integration
**Status:** Unblocked | **Est:** 3 hours | **Agent:** Available
**Dependencies:** PR-F001 ✅, PR-F003 ✅
**Description:** Implement Socket.io client for real-time generation and composition progress updates.

**Files to Create:**
- `frontend/src/hooks/useWebSocket.ts` - React hook for WebSocket connections
- `frontend/src/utils/websocket.ts` - WebSocket client configuration and manager
- `frontend/src/utils/messageQueue.ts` - Message queue for offline handling
- `frontend/src/types/websocket.ts` - TypeScript types for WebSocket messages
- `frontend/src/api/services/websocket.ts` - WebSocket service layer

**Acceptance Criteria:**
- [ ] Socket.io client configured with auto-reconnection
- [ ] Custom `useWebSocket` hook with:
  - [ ] Connection state management
  - [ ] Automatic reconnection with exponential backoff
  - [ ] Message queue for offline messages
  - [ ] Event subscription/unsubscription
- [ ] Event handlers for generation progress (`/ws/generations/{id}`):
  - [ ] `progress` - Step updates with percentage
  - [ ] `clip_completed` - Individual clip completion
  - [ ] `status_change` - Status transitions
  - [ ] `completed` - Final video ready
  - [ ] `error` - Error notifications
- [ ] Event handlers for composition progress (`/ws/compositions/{id}`):
  - [ ] `encoding_progress` - Frame-level progress
- [ ] Graceful fallback to polling if WebSocket fails
- [ ] Connection status indicator component
- [ ] TypeScript types for all message formats (from API spec)
- [ ] Reconnection logic (5min idle timeout, immediate reconnect on disconnect)
- [ ] Message validation and error handling

**Implementation Notes:**
- Follow WebSocket message formats from Section D of API spec
- Include `X-Request-ID` in connection headers
- Support multiple concurrent connections (for multiple jobs)
- Store connection state in React Context or Zustand
- Test with mock WebSocket server before backend integration

---

### PR-F005: Routing and Layout
**Status:** Unblocked | **Est:** 2 hours | **Agent:** Available
**Dependencies:** PR-F001 ✅, PR-F002 ✅
**Description:** React Router setup with main layout, navigation, and route structure.

**Files to Create/Modify:**
- `frontend/src/App.tsx` - Update with route configuration
- `frontend/src/layouts/MainLayout.tsx` - Main layout with header/footer
- `frontend/src/components/Navigation.tsx` - Navigation menu component
- `frontend/src/pages/Home.tsx` - Home/pipeline selection page
- `frontend/src/pages/History.tsx` - Generation history page
- `frontend/src/pages/NotFound.tsx` - 404 error page

**Acceptance Criteria:**
- [ ] React Router v6 configured with routes:
  - [ ] `/` - Home/Pipeline Selection
  - [ ] `/history` - Generation history
  - [ ] `*` - 404 page
- [ ] MainLayout component with:
  - [ ] Header with logo and navigation
  - [ ] Main content area with `<Outlet>`
  - [ ] Footer with status/help
- [ ] Navigation menu with:
  - [ ] "Home" and "History" links
  - [ ] Active route highlighting
  - [ ] Responsive mobile menu (hamburger icon)
- [ ] Breadcrumb navigation component
- [ ] 404 page with helpful message and "Go Home" button
- [ ] Keyboard navigation support (Tab, Enter, Escape)
- [ ] ARIA labels for accessibility

**Implementation Notes:**
- Use Button component from PR-F002
- Navigation should be sticky on scroll
- Mobile menu should slide in from side
- Active route highlight uses CSS variable `--color-primary`

---

### PR-F008: Video Preview Component
**Status:** Unblocked | **Est:** 3 hours | **Agent:** Available
**Dependencies:** PR-F002 ✅
**Description:** Build HTML5 video player with controls, fullscreen, download, and preview features.

**Files to Create:**
- `frontend/src/components/VideoPlayer/VideoPlayer.tsx` - Main player component
- `frontend/src/components/VideoPlayer/VideoControls.tsx` - Custom controls
- `frontend/src/components/VideoPlayer/Timeline.tsx` - Scrubber timeline
- `frontend/src/hooks/useVideoPlayer.ts` - Video player state management
- `frontend/src/utils/video.ts` - Video utilities (format time, generate thumbnail)

**Acceptance Criteria:**
- [ ] HTML5 video player with custom controls:
  - [ ] Play/Pause toggle
  - [ ] Volume control with mute
  - [ ] Seek timeline with scrubber
  - [ ] Current time / Duration display
  - [ ] Fullscreen toggle
  - [ ] Playback speed selector (0.5x, 1x, 1.5x, 2x)
- [ ] Video loading states:
  - [ ] Thumbnail preview while loading
  - [ ] Loading spinner overlay
  - [ ] Progress bar for buffering
- [ ] Download functionality:
  - [ ] Download button with file size
  - [ ] Download progress indicator
  - [ ] Success confirmation
- [ ] Keyboard shortcuts:
  - [ ] Space - Play/Pause
  - [ ] Arrow keys - Seek forward/back
  - [ ] F - Fullscreen
  - [ ] M - Mute
- [ ] Responsive design (mobile-friendly controls)
- [ ] Accessibility (ARIA labels, keyboard navigation)

**Implementation Notes:**
- Use native HTML5 `<video>` element
- Custom controls overlay (hide native controls)
- Timeline scrubber should show preview thumbnail on hover (nice-to-have)
- Fullscreen API for cross-browser compatibility
- Video format: MP4 with H.264 codec (from API spec)

---

### PR-F016: User Documentation
**Status:** Unblocked | **Est:** 2 hours | **Agent:** Available
**Dependencies:** None (parallel work)
**Description:** Create user-facing documentation including user guide, FAQ, and prompt engineering best practices.

**Files to Create:**
- `docs/user-guide.md` - Comprehensive user guide
- `docs/faq.md` - Frequently asked questions
- `docs/prompt-best-practices.md` - Tips for effective prompts
- `frontend/src/components/HelpTooltip.tsx` - In-app help component
- `frontend/src/data/helpContent.ts` - Help content data

**Acceptance Criteria:**
- [ ] User guide covering:
  - [ ] Getting started
  - [ ] Creating your first Ad Creative video
  - [ ] Understanding the generation process
  - [ ] Using brand assets (logo, colors)
  - [ ] Configuring video parameters (duration, aspect ratio)
  - [ ] Downloading and sharing videos
  - [ ] Troubleshooting common issues
- [ ] FAQ with 10-15 questions:
  - [ ] What is the maximum video duration?
  - [ ] What aspect ratios are supported?
  - [ ] How long does generation take?
  - [ ] What file formats can I upload?
  - [ ] Can I cancel a generation?
  - [ ] How do I write better prompts?
  - [ ] What if generation fails?
  - [ ] Etc.
- [ ] Prompt best practices guide:
  - [ ] Structure of effective prompts
  - [ ] Example prompts for different ad types (product, service, event)
  - [ ] How to describe brand identity
  - [ ] Tips for visual consistency
  - [ ] Common mistakes to avoid
  - [ ] Character limit guidelines (500-2000 chars)
- [ ] HelpTooltip component (icon with popover)
- [ ] Help content data structure for in-app tooltips

**Implementation Notes:**
- Write in clear, user-friendly language (non-technical)
- Include placeholder images/screenshots (update later with real ones)
- Focus on MVP features (Ad Creative pipeline)
- Prepare structure for Music Video docs (post-MVP)
- Help tooltips should use design system components

---

## Blocked PRs (Awaiting Dependencies)

### PR-F006: Pipeline Selection Interface
**Status:** Blocked | **Est:** 2 hours | **Agent:** Waiting
**Dependencies:** PR-F005 (Routing), PR-F002 ✅
**Description:** Create home page with pipeline selection (Ad Creative vs Music Video).

**Files to Create:**
- `frontend/src/pages/PipelineSelection.tsx` - Main selection page
- `frontend/src/components/PipelineCard.tsx` - Individual pipeline card
- `frontend/src/types/pipeline.ts` - Pipeline type definitions

**Acceptance Criteria:**
- [ ] Two large, clickable cards:
  - [ ] Ad Creative (15-60 seconds)
  - [ ] Music Video (60-180 seconds) - Disabled for MVP
- [ ] Each card shows:
  - [ ] Pipeline icon
  - [ ] Title and brief description
  - [ ] Key features list
  - [ ] Duration range
  - [ ] "Start Creating" button
- [ ] Music Video card has "Coming Soon" badge
- [ ] Clicking Ad Creative navigates to generation form
- [ ] Hover effects and animations
- [ ] Responsive layout (stacks on mobile)

**Blockers:** Needs routing setup (PR-F005)

---

### PR-F007: Generation Form - Ad Creative
**Status:** Blocked | **Est:** 5 hours | **Agent:** Waiting
**Dependencies:** PR-F002 ✅, PR-F003 ✅, PR-F005, PR-F012 (Asset Upload)
**Description:** Multi-step form for Ad Creative video generation with prompt input, brand settings, and parameters.

**Files to Create:**
- `frontend/src/pages/AdCreativeForm.tsx` - Main form page
- `frontend/src/components/GenerationForm/PromptInput.tsx` - Prompt textarea
- `frontend/src/components/GenerationForm/BrandSettings.tsx` - Brand config
- `frontend/src/components/GenerationForm/VideoParameters.tsx` - Duration, aspect ratio
- `frontend/src/components/GenerationForm/ReviewStep.tsx` - Final review
- `frontend/src/hooks/useGenerationForm.ts` - Form state management
- `frontend/src/utils/validation.ts` - Form validation functions

**Acceptance Criteria:**
- [ ] Multi-step form (4 steps):
  1. **Prompt Input:**
     - [ ] Textarea with 500-2000 character limit
     - [ ] Character counter with visual feedback
     - [ ] Placeholder text with examples
     - [ ] Optional: Prompt suggestions/templates
  2. **Brand Settings:**
     - [ ] Brand name input
     - [ ] Logo upload (via AssetUploader component)
     - [ ] Brand color picker (primary and secondary)
     - [ ] CTA toggle and text input (optional)
  3. **Video Parameters:**
     - [ ] Duration selector (15, 30, 45, 60 seconds) - radio or slider
     - [ ] Aspect ratio selector (16:9, 9:16, 1:1) - radio buttons
     - [ ] Style dropdown (professional, casual, modern, etc.)
     - [ ] Music style dropdown (corporate, upbeat, cinematic)
  4. **Review & Submit:**
     - [ ] Summary of all settings
     - [ ] Edit buttons for each section
     - [ ] Estimated generation time
     - [ ] Submit button
- [ ] Form validation:
  - [ ] Prompt: 500-2000 chars, not empty
  - [ ] Brand name: optional but recommended
  - [ ] Logo: optional, max 50MB, JPEG/PNG only
  - [ ] Colors: valid hex codes
  - [ ] All required fields validated before submit
- [ ] Error messages for invalid fields
- [ ] Progress indicator showing current step
- [ ] Save to localStorage (auto-save on change)
- [ ] Success redirect to progress page after submit

**API Integration:**
- [ ] POST `/api/v1/generations` with request body from API spec
- [ ] Upload logo via POST `/api/v1/assets/upload` (if provided)
- [ ] Handle validation errors from backend

**Blockers:** 
- Needs routing (PR-F005)
- Needs AssetUploader (PR-F012)

---

### PR-F009: Progress Tracking Component
**Status:** Blocked | **Est:** 4 hours | **Agent:** Waiting
**Dependencies:** PR-F002 ✅, PR-F004 (WebSocket)
**Description:** Real-time progress display for video generation with step-by-step updates, clip previews, and estimated time.

**Files to Create:**
- `frontend/src/pages/GenerationProgress.tsx` - Progress page
- `frontend/src/components/Progress/ProgressBar.tsx` - Overall progress bar
- `frontend/src/components/Progress/StepIndicator.tsx` - Step-by-step display
- `frontend/src/components/Progress/ClipPreview.tsx` - Individual clip preview
- `frontend/src/hooks/useGenerationProgress.ts` - Progress state management

**Acceptance Criteria:**
- [ ] Overall progress display:
  - [ ] Percentage complete (0-100%)
  - [ ] Progress bar with smooth animations
  - [ ] Current status message
  - [ ] Estimated time remaining
- [ ] Step-by-step indicator showing:
  - [ ] Input validation ✓
  - [ ] Content planning (in progress)
  - [ ] Asset generation (5/10 clips)
  - [ ] Video composition (pending)
  - [ ] Final rendering (pending)
- [ ] Clip preview section:
  - [ ] Grid of generated clips as they complete
  - [ ] Thumbnail for each clip
  - [ ] Duration label
  - [ ] Clip number
- [ ] Real-time updates via WebSocket:
  - [ ] `progress` events update percentage and step
  - [ ] `clip_completed` events add clip previews
  - [ ] `status_change` events update overall status
  - [ ] `completed` event redirects to preview page
  - [ ] `error` events show error message
- [ ] Cancel button:
  - [ ] Confirmation dialog
  - [ ] POST `/api/v1/generations/{id}/cancel`
  - [ ] Redirect to history on cancel
- [ ] Fallback to polling if WebSocket fails (every 5 seconds)
- [ ] Loading animations and transitions

**Blockers:** Needs WebSocket integration (PR-F004)

---

### PR-F010: Video Preview & Download Page
**Status:** Blocked | **Est:** 3 hours | **Agent:** Waiting
**Dependencies:** PR-F008 (Video Player), PR-F003 ✅
**Description:** Page to preview completed video and download final composition.

**Files to Create:**
- `frontend/src/pages/VideoPreview.tsx` - Preview page
- `frontend/src/components/VideoActions.tsx` - Action buttons
- `frontend/src/hooks/useVideoDownload.ts` - Download logic

**Acceptance Criteria:**
- [ ] Video player (using VideoPlayer from PR-F008)
- [ ] Video metadata display:
  - [ ] Generation ID
  - [ ] Duration
  - [ ] Resolution
  - [ ] File size
  - [ ] Creation date
- [ ] Action buttons:
  - [ ] Download (primary button)
  - [ ] Create Another Video
  - [ ] Return to History
  - [ ] Share (copy link) - optional
- [ ] Download functionality:
  - [ ] GET `/api/v1/compositions/{id}/download`
  - [ ] Progress indicator during download
  - [ ] Success notification
  - [ ] Error handling for failed downloads
- [ ] Generation parameters summary (original prompt, settings)
- [ ] Re-run option (loads same parameters into form)

**API Integration:**
- [ ] GET `/api/v1/generations/{id}` for metadata
- [ ] GET `/api/v1/generations/{id}/assets` for video URL
- [ ] GET `/api/v1/compositions/{id}/download` for file download

**Blockers:** Needs VideoPlayer component (PR-F008)

---

### PR-F011: Generation History Page
**Status:** Blocked | **Est:** 4 hours | **Agent:** Waiting
**Dependencies:** PR-F003 ✅, PR-F005 (Routing)
**Description:** Paginated list of user's generation jobs with filtering, search, and status badges.

**Files to Create:**
- `frontend/src/pages/History.tsx` - History page
- `frontend/src/components/History/GenerationCard.tsx` - Individual job card
- `frontend/src/components/History/FilterSidebar.tsx` - Filter controls
- `frontend/src/components/Pagination.tsx` - Reusable pagination
- `frontend/src/hooks/useGenerationHistory.ts` - History state management

**Acceptance Criteria:**
- [ ] Paginated list of generations:
  - [ ] Card-based layout with thumbnail
  - [ ] Status badge (queued, processing, composing, completed, failed, cancelled)
  - [ ] Generation ID
  - [ ] Creation date/time
  - [ ] Duration (if completed)
  - [ ] Quick actions (view, download, delete)
- [ ] Filtering options:
  - [ ] Status filter (all, completed, processing, failed)
  - [ ] Date range picker
  - [ ] Pipeline type (Ad Creative, Music Video)
- [ ] Search functionality:
  - [ ] Search by prompt text
  - [ ] Debounced search input
- [ ] Sort options:
  - [ ] By date (newest/oldest)
  - [ ] By duration
  - [ ] By status
- [ ] Pagination controls:
  - [ ] Previous/Next buttons
  - [ ] Page numbers
  - [ ] Items per page selector (20, 50, 100)
- [ ] Empty state (no generations yet)
- [ ] Loading skeleton while fetching

**API Integration:**
- [ ] GET `/api/v1/generations` with query params:
  - [ ] `page`, `limit`, `status`, `sort`
- [ ] DELETE `/api/v1/generations/{id}` for delete action

**Blockers:** Needs routing setup (PR-F005)

---

### PR-F012: Asset Upload Manager
**Status:** Blocked | **Est:** 3 hours | **Agent:** Waiting
**Dependencies:** PR-F002 ✅, PR-F003 ✅
**Description:** Drag-and-drop file upload component for brand assets (logos, product images) and audio files.

**Files to Create:**
- `frontend/src/components/AssetUploader/AssetUploader.tsx` - Main uploader
- `frontend/src/components/AssetUploader/DropZone.tsx` - Drag-and-drop zone
- `frontend/src/components/AssetUploader/FilePreview.tsx` - Preview component
- `frontend/src/components/AssetUploader/UploadProgress.tsx` - Progress bar
- `frontend/src/hooks/useFileUpload.ts` - Upload state management
- `frontend/src/utils/fileValidation.ts` - Validation helpers

**Acceptance Criteria:**
- [ ] Drag-and-drop upload zone:
  - [ ] Visual feedback on drag over
  - [ ] Click to browse files
  - [ ] Multiple file selection support
- [ ] File validation:
  - [ ] Image files: JPEG, PNG, max 50MB
  - [ ] Audio files: MP3, WAV, max 100MB
  - [ ] Minimum dimensions for images (512x512)
  - [ ] Maximum dimensions for images (4096x4096)
  - [ ] Audio duration validation (max 180s)
  - [ ] Error messages for invalid files
- [ ] Upload progress:
  - [ ] Individual progress bar per file
  - [ ] Percentage complete
  - [ ] Cancel upload button
  - [ ] Success/error states
- [ ] File preview:
  - [ ] Thumbnail for images
  - [ ] Waveform or duration for audio
  - [ ] File name and size
  - [ ] Remove button
- [ ] Asset gallery:
  - [ ] Grid of uploaded files
  - [ ] Click to enlarge/play
  - [ ] Delete confirmation dialog

**API Integration:**
- [ ] POST `/api/v1/assets/upload` with multipart/form-data
- [ ] Handle upload progress events
- [ ] Error handling for upload failures

**Blockers:** Can start immediately (only needs foundation PRs)

---

### PR-F013: Timeline Editor Component
**Status:** Blocked | **Est:** 6 hours | **Agent:** Waiting
**Dependencies:** PR-F002 ✅, PR-F008 (Video Player), PR-F009 (Progress - for clip data)
**Description:** Visual timeline editor for clip arrangement, trimming, and transitions.

**Files to Create:**
- `frontend/src/components/Timeline/TimelineEditor.tsx` - Main timeline
- `frontend/src/components/Timeline/ClipTrack.tsx` - Draggable clip track
- `frontend/src/components/Timeline/TransitionPicker.tsx` - Transition selector
- `frontend/src/components/Timeline/TimeRuler.tsx` - Time ruler with zoom
- `frontend/src/hooks/useTimeline.ts` - Timeline state management
- `frontend/src/utils/timeline.ts` - Timeline calculations

**Acceptance Criteria:**
- [ ] Visual timeline display:
  - [ ] Horizontal track with clip thumbnails
  - [ ] Time ruler at top (seconds)
  - [ ] Zoom in/out controls
  - [ ] Playhead indicator
- [ ] Clip manipulation:
  - [ ] Drag-and-drop reordering
  - [ ] Trim handles at clip edges (drag to trim)
  - [ ] Click to select clip
  - [ ] Delete selected clip
- [ ] Transition controls:
  - [ ] Transition icons between clips
  - [ ] Click to select transition type (fade, cut, dissolve)
  - [ ] Visual representation of transition
- [ ] Playback controls:
  - [ ] Play from timeline position
  - [ ] Pause
  - [ ] Scrub through timeline
- [ ] Timeline data management:
  - [ ] Sync with generation clip data
  - [ ] Calculate total duration
  - [ ] Validate timeline (no gaps, proper transitions)
- [ ] Save composition:
  - [ ] POST `/api/v1/compositions` with timeline config
  - [ ] Loading state during composition
  - [ ] Redirect to composition progress

**API Integration:**
- [ ] GET `/api/v1/generations/{id}/assets` for clip data
- [ ] POST `/api/v1/compositions` with timeline configuration

**Blockers:** 
- Needs VideoPlayer (PR-F008)
- Needs clip data from generation (PR-F009)

---

### PR-F014: Error Handling & Notifications
**Status:** Blocked | **Est:** 3 hours | **Agent:** Waiting
**Dependencies:** PR-F002 ✅, PR-F003 ✅, All form components
**Description:** Comprehensive error handling system with toast notifications, error boundaries, and retry mechanisms.

**Files to Create:**
- `frontend/src/components/ErrorBoundary.tsx` - React error boundary
- `frontend/src/components/Notifications/ToastContainer.tsx` - Toast container
- `frontend/src/components/Notifications/Toast.tsx` - Individual toast (enhance from PR-F002)
- `frontend/src/hooks/useNotification.ts` - Notification hook
- `frontend/src/utils/errorMessages.ts` - User-friendly error messages

**Acceptance Criteria:**
- [ ] Toast notification system:
  - [ ] Success, error, warning, info types
  - [ ] Auto-dismiss after 5 seconds
  - [ ] Manual dismiss button
  - [ ] Multiple toasts queue properly
  - [ ] Position: top-right corner
  - [ ] Slide-in animation
- [ ] Error boundary component:
  - [ ] Catches React component errors
  - [ ] Displays fallback UI
  - [ ] "Reload Page" button
  - [ ] Error logging (console)
- [ ] Error message mapping:
  - [ ] Backend error codes → user-friendly messages
  - [ ] Validation errors
  - [ ] Network errors
  - [ ] Timeout errors
- [ ] Retry mechanisms:
  - [ ] Retry button for failed API calls
  - [ ] Exponential backoff (already in API client)
  - [ ] Max retry attempts (3)
- [ ] Global error handler:
  - [ ] Catches unhandled promise rejections
  - [ ] Shows toast for critical errors
- [ ] Offline indicator:
  - [ ] Banner when network is offline
  - [ ] Auto-hide when back online

**Implementation Notes:**
- Use Toast component from PR-F002 as base (enhance if needed)
- Error messages should be actionable ("Try again" vs "Something went wrong")
- Map all error codes from Section F of API spec

**Blockers:** Needs form components to be integrated

---

### PR-F015: Mobile Responsive Design
**Status:** Blocked | **Est:** 4 hours | **Agent:** Waiting
**Dependencies:** All UI components (PR-F002 through PR-F013)
**Description:** Adapt all components for mobile and tablet viewports with touch-friendly interactions.

**Files to Modify:**
- All component CSS files
- `frontend/src/styles/responsive.css` - Update responsive utilities

**Acceptance Criteria:**
- [ ] Responsive navigation:
  - [ ] Hamburger menu for mobile
  - [ ] Slide-in drawer
  - [ ] Touch-friendly tap targets (min 44x44px)
- [ ] Responsive forms:
  - [ ] Single-column layout on mobile
  - [ ] Larger input fields
  - [ ] Touch-friendly sliders and pickers
- [ ] Responsive timeline:
  - [ ] Vertical layout option for mobile
  - [ ] Swipe to scroll
  - [ ] Simplified controls
- [ ] Responsive video player:
  - [ ] Full-width on mobile
  - [ ] Touch controls (tap to play/pause)
  - [ ] Mobile-friendly scrubber
- [ ] Responsive cards and lists:
  - [ ] Stack vertically on mobile
  - [ ] Larger tap targets
- [ ] Test on breakpoints:
  - [ ] Mobile: 375px, 414px
  - [ ] Tablet: 768px, 1024px
  - [ ] Desktop: 1280px, 1920px

**Blockers:** Needs all components to be built first

---

## Phase 5: Post-MVP Enhancements (Days 3-8)

### PR-F017: Music Video Interface
**Status:** Post-MVP | **Est:** 8 hours
**Dependencies:** MVP Complete
**Description:** Add Music Video pipeline with audio upload, longer duration support, and music-specific parameters.

**Files to Create:**
- `frontend/src/pages/MusicVideoForm.tsx` - Music video form
- `frontend/src/components/AudioUploader.tsx` - Audio file upload
- `frontend/src/components/AudioPreview.tsx` - Audio player with waveform
- `frontend/src/components/BeatVisualizer.tsx` - Beat detection visualization

**Key Differences from Ad Creative:**
- Duration: 60-180 seconds (vs 15-60)
- Audio upload required (or system generates)
- Genre/style selector instead of brand settings
- Visual style tied to music genre
- Longer timeline support
- No CTA or brand assets

---

### PR-F018: Advanced Features
**Status:** Post-MVP | **Est:** 6 hours
**Description:** Template library, batch generation, A/B testing interface.

---

### PR-F019: Performance Optimization
**Status:** Post-MVP | **Est:** 4 hours
**Description:** Code splitting, lazy loading, caching, service worker.

---

## Critical Path for MVP (48 hours)

### Phase 1: Foundation Complete ✅ (Hours 0-8)
- ✅ PR-F001: Project Initialization (1 hour)
- ✅ PR-F002: Design System (3 hours)
- ✅ PR-F003: API Client Setup (2 hours)

### Phase 2: Core Infrastructure (Hours 8-16)
1. **PR-F004: WebSocket Integration** (3 hours) - UNBLOCKED
2. **PR-F005: Routing and Layout** (2 hours) - UNBLOCKED
3. **PR-F016: User Documentation** (2 hours) - UNBLOCKED (parallel)
4. **PR-F008: Video Preview Component** (3 hours) - UNBLOCKED

**Deliverables:** Real-time updates, navigation, video player

### Phase 3: Generation Flow (Hours 16-28)
5. **PR-F012: Asset Upload Manager** (3 hours) - Ready after F002/F003
6. **PR-F006: Pipeline Selection** (2 hours) - Ready after F005
7. **PR-F007: Generation Form** (5 hours) - Ready after F005, F012
8. **PR-F009: Progress Tracking** (4 hours) - Ready after F004

**Deliverables:** Complete generation submission flow

### Phase 4: Preview & History (Hours 28-36)
9. **PR-F010: Video Preview & Download** (3 hours) - Ready after F008
10. **PR-F011: Generation History** (4 hours) - Ready after F005
11. **PR-F013: Timeline Editor** (6 hours) - Ready after F008, F009

**Deliverables:** Full video lifecycle (create, track, preview, download, history)

### Phase 5: Polish & Testing (Hours 36-48)
12. **PR-F014: Error Handling** (3 hours) - Ready after forms
13. **PR-F015: Mobile Responsive** (4 hours) - Ready after all components
14. Integration testing and bug fixes (5 hours)

---

## Updated Success Metrics

### MVP (48 hours)
- [ ] User can select Ad Creative pipeline
- [ ] User can submit generation request with prompt and brand assets
- [ ] Real-time progress updates display correctly via WebSocket
- [ ] User can preview generated video in browser
- [ ] User can download final video
- [ ] Generation history shows all jobs with status
- [ ] Timeline editor allows clip reordering (basic)
- [ ] Mobile responsive (tablet+)
- [ ] No critical bugs in happy path
- [ ] User documentation complete

### Post-MVP (Days 3-8)
- [ ] Music Video pipeline functional
- [ ] Advanced timeline editing (trimming, transitions)
- [ ] Template library
- [ ] Performance optimized
- [ ] Full mobile support (<768px)
- [ ] Comprehensive testing suite

---

## Risk Mitigation

### High-Risk Items (Updated)
1. **WebSocket Stability (PR-F004):** Implement robust reconnection and polling fallback
2. **Timeline Complexity (PR-F013):** Start with basic reordering, add trimming later
3. **API Integration:** All endpoints defined in API spec - follow strictly
4. **Asset Upload (PR-F012):** Handle large files, validate before upload
5. **Mobile Responsiveness (PR-F015):** Test early on actual devices

### Contingency Plans
- **If WebSocket fails:** Use polling as primary (already built into progress component)
- **If timeline too complex:** Simplify to basic ordering only (no trimming)
- **If upload issues:** Reduce file size limits, add chunking
- **If time runs short:** Skip timeline editor (use default composition)

---

## Integration Checklist

### API Contract Compliance (From api-specification-edited.md)
- [ ] All request/response types match API spec exactly
- [ ] Error codes mapped to user messages (Section F)
- [ ] WebSocket message formats correct (Section D)
- [ ] File upload follows multipart/form-data spec
- [ ] Rate limiting headers handled (Section G)
- [ ] Request ID tracking on all calls (Section J)
- [ ] Timeout configuration matches spec (30s API, 5min idle WS)

### Backend Coordination
- [ ] GET `/api/v1/generations/{id}` polling if WS fails
- [ ] Confirm upload limits with backend (50MB images, 100MB audio)
- [ ] Verify composition timeline format with FFmpeg backend
- [ ] Test error scenarios with backend team

---

## Notes

**Completed Work:**
- Strong TypeScript foundation with strict mode
- Complete design system with CSS variables (no Tailwind)
- Comprehensive API client with all services, error handling, retry logic
- Circuit breaker, rate limiting awareness, polling helpers

**Next Immediate Steps:**
1. Start PR-F004 (WebSocket) - Critical for progress tracking
2. Start PR-F005 (Routing) - Blocks multiple PRs
3. Start PR-F008 (Video Player) - Independent, reusable
4. Start PR-F016 (Docs) - Parallel work, no blockers

**Key Dependencies to Unblock:**
- PR-F004 unblocks → PR-F009 (Progress Tracking)
- PR-F005 unblocks → PR-F006, PR-F007, PR-F011 (Most pages)
- PR-F008 unblocks → PR-F010, PR-F013 (Preview/Timeline)
- PR-F012 unblocks → PR-F007 (Generation Form)