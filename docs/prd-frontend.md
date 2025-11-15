# Frontend Product Requirements Document
## AI Video Generation Pipeline - Web Interface

### Overview

This document defines the scope and requirements for the **Web Frontend (Track 1)** component of the AI Video Generation Pipeline. The frontend team is responsible for building the user-facing interface that enables users to create AI-generated videos through both Ad Creative and Music Video pipelines.

**Timeline Context:**
- MVP Deadline: 48 hours
- Focus: Core functionality over polish
- Must interface with AI Backend and FFmpeg Backend via defined API contracts

### Team Scope & Boundaries

**Your Responsibilities:**
- User interface for video generation requests
- Real-time progress tracking and updates
- Video preview and download functionality
- Client-side validation and error handling
- Responsive layout for desktop/tablet use

**External Dependencies (Other Teams):**
- **AI Backend (Track 2):** Provides content generation and orchestration APIs
- **FFmpeg Backend (Track 3):** Handles video composition and processing
- **DevOps (Track 4):** Manages deployment infrastructure

**Interface Contract:** All API interactions must follow `api-specification-edited.md`

### Technology Stack

**Required:**
- React 18 with TypeScript
- Vite for build tooling
- WebSocket client for real-time updates
- Axios for REST API communication

**Recommended:**
- Tailwind CSS or Material-UI for styling
- React Query for API state management
- Zustand or Context API for app state
- React Hook Form for form handling

### Core Features (MVP)

#### 1. Pipeline Selection Interface
**Purpose:** Allow users to choose between Ad Creative and Music Video workflows

**Requirements:**
- Clear visual distinction between pipeline types
- Brief description of each pipeline's capabilities
- Single-click navigation to appropriate workflow
- Return to selection without losing progress

**UI Elements:**
- Two large, clickable cards/buttons
- Pipeline icons and labels
- Capability summary (duration ranges, key features)

#### 2. Ad Creative Workflow

**2.1 Prompt Input**
- Rich text area supporting 500-2000 characters
- Character counter with visual feedback
- Placeholder text with examples
- Optional: Prompt suggestions/templates

**2.2 Configuration Controls**
- **Aspect Ratio Selector:** 16:9, 9:16, 1:1 (radio buttons or dropdown)
- **Duration Selector:** 15-60 seconds (slider or number input)
- **Brand Assets Upload:** Logo/product images (drag-and-drop optional)
  - File type validation (JPEG, PNG, max 50MB)
  - Visual preview of uploaded assets
  - Remove/replace functionality

**2.3 Advanced Options (Collapsible)**
- Brand color specifications (color picker)
- CTA text input (optional)
- Style intensity controls

#### 3. Music Video Workflow

**3.1 Prompt Input**
- Same rich text area as Ad Creative
- Character counter with visual feedback
- Genre/style suggestions

**3.2 Audio Upload**
- Audio file upload (MP3, WAV, max 100MB)
- File type and size validation
- Audio preview player
- Duration detection and display
- Clear indication if no audio uploaded (system will generate)

**3.3 Configuration Controls**
- **Duration Selector:** 60-180 seconds (slider)
- **Visual Style:** Dropdown/radio for genre-appropriate themes
- **Clip Count:** Auto-calculated based on duration (display only)

#### 4. Generation Progress Interface

**4.1 Progress Display**
- Step-by-step progress indicator showing:
  - Input validation
  - Content planning
  - Asset generation (with clip count progress: "5/10 clips")
  - Video composition
  - Final rendering
- Percentage complete for each major stage
- Estimated time remaining
- Current status message

**4.2 Real-Time Updates**
- WebSocket connection for live progress
- Graceful fallback to polling if WebSocket unavailable
- Visual loading indicators
- Cancel job functionality

**4.3 Error Handling**
- Clear error messages for:
  - Validation failures
  - API errors
  - Generation failures
  - Network issues
- Retry button for recoverable errors
- Return to edit for input errors

#### 5. Video Preview & Download

**5.1 Preview Player**
- In-browser HTML5 video player
- Standard playback controls (play, pause, seek, volume)
- Fullscreen capability
- Timeline scrubbing
- Preview thumbnail while loading

**5.2 Download Options**
- Primary download button (MP4, H.264, 720p)
- File size indicator
- Download progress feedback
- Success confirmation

**5.3 Post-Generation Actions**
- "Create Another Video" button
- Return to pipeline selection
- Share generation parameters (optional, nice-to-have)

#### 6. Job History (Optional for MVP)

If time permits:
- List of recent generation jobs
- Status badges (processing, completed, failed)
- Quick access to completed videos
- Re-run with same parameters option

### User Interface Requirements

#### Layout Structure
```
┌─────────────────────────────────────┐
│ Header (Logo, Pipeline Selection)   │
├─────────────────────────────────────┤
│                                     │
│  Main Content Area                  │
│  - Pipeline Selection OR            │
│  - Configuration Form OR            │
│  - Progress View OR                 │
│  - Preview/Download                 │
│                                     │
├─────────────────────────────────────┤
│ Footer (Help, Status)               │
└─────────────────────────────────────┘
```

#### Responsive Design
- **Primary Target:** Desktop (1280px+)
- **Secondary Target:** Tablet landscape (1024px+)
- **Mobile:** Out of scope for MVP

#### Visual Design Principles
- Clean, professional appearance
- Clear visual hierarchy
- Consistent spacing and typography
- Loading states for all async operations
- Disabled states for unavailable actions
- Error states with actionable guidance

### API Integration Requirements

**Base URL Configuration:**
- Environment variable for API base URL
- Separate endpoints for development and production

**Required API Endpoints (Reference api-specification-edited.md):**

1. **POST /api/jobs** - Create new generation job
2. **GET /api/jobs/{jobId}** - Get job status
3. **POST /api/assets/upload** - Upload brand assets/audio
4. **GET /api/videos/{videoId}** - Download completed video
5. **DELETE /api/jobs/{jobId}** - Cancel job
6. **WebSocket /ws/jobs/{jobId}** - Real-time progress updates

**Request/Response Handling:**
- All requests include proper headers and authentication (if required)
- Parse and display API error messages
- Handle network timeouts gracefully
- Implement retry logic for failed requests
- Display appropriate loading states

### Validation Requirements

#### Client-Side Validation
**Prompt Input:**
- Minimum 50 characters
- Maximum 2000 characters
- No empty submissions
- Warn if prompt is too generic

**File Uploads:**
- File type validation (JPEG, PNG for images; MP3, WAV for audio)
- File size limits (50MB for images, 100MB for audio)
- Image dimension checks (min 512x512, max 4096x4096)
- Audio duration validation (max 180 seconds for music videos)

**Duration & Aspect Ratio:**
- Ad Creative: 15-60 seconds
- Music Video: 60-180 seconds
- Aspect ratio must be selected before submission

#### Error Messages
- Specific, actionable error messages
- Visual highlighting of invalid fields
- Persist validation errors until corrected
- Summary of all errors before submission

### Performance Requirements

**Page Load:**
- Initial page load: <3 seconds
- Assets optimized (lazy loading for images)
- Code splitting for route-based chunks

**Responsiveness:**
- Form interactions: <100ms response
- API calls: Show loading state immediately
- Progress updates: <500ms latency

**Browser Support:**
- Chrome 90+ (primary)
- Firefox 88+
- Safari 14+
- Edge 90+

### State Management

**Application State:**
- Current pipeline selection
- Form input values
- Uploaded asset references
- Active job ID and status
- WebSocket connection status

**Persistence:**
- Form auto-save to localStorage (optional)
- Session recovery on page refresh
- Clear state on successful completion

**Error State:**
- Network connectivity status
- API error messages
- Validation errors
- Recovery actions available

### WebSocket Integration

**Connection Management:**
- Establish connection when job starts
- Automatic reconnection on disconnect
- Close connection on job completion
- Fallback to polling if WebSocket fails

**Message Handling:**
- Parse progress updates
- Update UI in real-time
- Handle error messages
- Graceful degradation

**Events to Handle:**
- `job.started`
- `job.progress` (with percentage and stage)
- `job.completed`
- `job.failed`
- `connection.lost`

### Non-Functional Requirements

#### Accessibility
- Keyboard navigation support
- ARIA labels for screen readers
- Sufficient color contrast
- Focus indicators on interactive elements

#### Error Recovery
- Retry failed API calls
- Preserve form data on errors
- Clear error recovery paths
- Helpful error messages

#### Security
- Sanitize user input before display
- Validate file types on client before upload
- No sensitive data in localStorage
- HTTPS-only API calls (in production)

### Testing Requirements

**Unit Tests (Minimum):**
- Form validation logic
- API request/response parsing
- WebSocket message handling
- Error boundary components

**Integration Tests (Nice-to-have):**
- Complete workflow for each pipeline
- File upload and validation
- Progress tracking through job lifecycle

**Manual Testing (Required):**
- Happy path for both pipelines
- Error scenarios (API failures, network issues)
- File upload edge cases
- Browser compatibility

### Development Workflow

**Setup:**
1. Clone repository
2. Install dependencies (`npm install`)
3. Configure environment variables
4. Start development server (`npm run dev`)

**Development Mode:**
- Hot module replacement enabled
- Mock API responses available (optional)
- WebSocket connection to development backend

**Build Process:**
- Production build: `npm run build`
- Preview production build: `npm run preview`
- TypeScript type checking: `npm run type-check`
- Linting: `npm run lint`

### MVP Acceptance Criteria

**Functional:**
- [ ] Both pipeline workflows functional end-to-end
- [ ] File uploads work for brand assets and audio
- [ ] Real-time progress updates display correctly
- [ ] Video preview and download work reliably
- [ ] Error handling covers common failure cases

**Quality:**
- [ ] No console errors in normal operation
- [ ] Forms validate input correctly
- [ ] Loading states provide clear feedback
- [ ] Responsive layout works on desktop and tablet
- [ ] TypeScript compiles without errors

**Documentation:**
- [ ] README with setup instructions
- [ ] Component documentation for key features
- [ ] API integration notes
- [ ] Known limitations documented

### Out of Scope (MVP)

**Excluded Features:**
- Mobile responsive design (<768px)
- User authentication and accounts
- Job history beyond current session
- Advanced video editing controls
- Social media sharing
- Analytics tracking
- Internationalization (i18n)
- Dark mode
- Custom themes
- Collaborative features
- Video timeline editor
- Advanced audio controls

### Success Metrics

**MVP Goals:**
- Users can successfully create videos through both pipelines
- <5% error rate on valid inputs
- Progress updates within 1 second of backend events
- Zero critical UI bugs in submission

**Timeline:**
- Core UI: 12 hours
- API integration: 8 hours
- Progress/WebSocket: 6 hours
- Testing & polish: 6 hours
- Buffer for issues: 16 hours
- **Total: 48 hours**

### Dependencies & Blockers

**Critical Path Items:**
1. API specification finalized (Day 0)
2. Backend endpoints available for testing (Day 1)
3. WebSocket endpoint functional (Day 1)
4. Sample API responses for development (Day 0)

**Communication:**
- Daily sync with AI Backend team on API changes
- Immediate notification of breaking changes
- Shared understanding of error codes and messages

### Appendix: Component Checklist

**Required Components:**
- PipelineSelector
- AdCreativeForm
- MusicVideoForm
- PromptInput
- FileUploader
- AspectRatioSelector
- DurationSelector
- ProgressTracker
- VideoPreview
- DownloadButton
- ErrorBoundary
- LoadingSpinner

**Required Utilities:**
- API client wrapper
- WebSocket manager
- Form validation helpers
- File type validators
- Error message formatter

---

**Note:** This document focuses exclusively on frontend concerns. Refer to `api-specification-edited.md` for complete API contract details and coordinate with other teams for integration requirements.