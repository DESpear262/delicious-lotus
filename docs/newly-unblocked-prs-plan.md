# Newly Unblocked Frontend PRs - Detailed Implementation Plans

**Date:** 2025-11-15
**Dependencies Complete:** PR-F001 ✅, PR-F002 ✅, PR-F003 ✅, PR-F004 ✅, PR-F005 ✅, PR-F008 ✅, PR-F012 ✅

## Summary

**5 PRs are now UNBLOCKED and ready to implement:**

1. **PR-F006:** Pipeline Selection Interface (2 hours)
2. **PR-F007:** Generation Form - Ad Creative (5 hours)
3. **PR-F009:** Progress Tracking Component (4 hours)
4. **PR-F010:** Video Preview & Download Page (3 hours)
5. **PR-F011:** Generation History Page (4 hours)

**Total Estimated Time:** 18 hours
**Parallelism Analysis:** 3-4 PRs can be worked on simultaneously

---

## Parallelism Matrix

### Group A (Can work in parallel - no file conflicts):
- **PR-F006** (Pipeline Selection)
- **PR-F009** (Progress Tracking)
- **PR-F010** (Video Preview)
- **PR-F011** (Generation History)

### Group B (Should work alone - major component):
- **PR-F007** (Generation Form) - Large PR, shares utilities with others

### Recommended Parallel Strategy:
**Wave 1 (Parallel):** F006, F009, F010, F011 (can all run simultaneously)
**Wave 2 (After Wave 1):** F007 (benefits from utilities created in Wave 1)

---

## PR-F006: Pipeline Selection Interface

### Status
- **Estimate:** 2 hours
- **Priority:** High (entry point to app)
- **Dependencies:** PR-F005 ✅, PR-F002 ✅
- **Can run in parallel with:** F009, F010, F011

### Description
Create the home page where users choose between Ad Creative (MVP) and Music Video (post-MVP) pipelines. This is the entry point after landing on the app.

### Files to Create (3 new files)
```
frontend/src/pages/PipelineSelection.tsx          [NEW] ~200 lines
frontend/src/components/PipelineCard.tsx          [NEW] ~150 lines
frontend/src/types/pipeline.ts                    [NEW] ~30 lines
```

### Files to Modify (1 file)
```
frontend/src/App.tsx                              [MODIFY] Add route for /pipeline-selection
```

### Implementation Details

#### File: `frontend/src/types/pipeline.ts`
```typescript
export type PipelineType = 'ad-creative' | 'music-video';

export interface PipelineInfo {
  id: PipelineType;
  title: string;
  description: string;
  features: string[];
  durationRange: string;
  icon: string;
  enabled: boolean;
  route: string;
}
```

#### File: `frontend/src/components/PipelineCard.tsx`
**Props:**
- `pipeline: PipelineInfo`
- `onClick: () => void`
- `disabled?: boolean`

**Features:**
- Card component using design system Card from PR-F002
- Icon display (placeholder for now)
- Title and description
- Feature list (bullet points)
- Duration range badge
- "Start Creating" button (uses Button from PR-F002)
- "Coming Soon" badge for disabled pipelines
- Hover effects with scale transform
- Click handler to navigate to form

**Styling:**
- Grid layout for features
- Primary color accent on hover
- Disabled state with reduced opacity
- Responsive (full width on mobile)

#### File: `frontend/src/pages/PipelineSelection.tsx`
**Features:**
- Page header: "Choose Your Video Pipeline"
- Two pipeline cards side-by-side (desktop) or stacked (mobile)
- Navigation using `useNavigate()` from react-router-dom
- Ad Creative enabled, Music Video disabled with "Coming Soon"

**Pipeline Configurations:**
```typescript
const pipelines: PipelineInfo[] = [
  {
    id: 'ad-creative',
    title: 'Ad Creative',
    description: 'Generate compelling video ads for your products or services',
    features: [
      'AI-powered video generation',
      'Brand customization (logo, colors)',
      'Multiple aspect ratios (16:9, 9:16, 1:1)',
      'Call-to-action integration',
      'Professional templates'
    ],
    durationRange: '15-60 seconds',
    icon: '🎬',
    enabled: true,
    route: '/ad-creative/new'
  },
  {
    id: 'music-video',
    title: 'Music Video',
    description: 'Create stunning music videos synced to your audio',
    features: [
      'Audio-driven visuals',
      'Beat detection & sync',
      'Genre-specific styles',
      'Extended duration support',
      'Waveform visualization'
    ],
    durationRange: '60-180 seconds',
    icon: '🎵',
    enabled: false,
    route: '/music-video/new'
  }
];
```

**Layout:**
- CSS Grid: 2 columns (desktop), 1 column (mobile)
- Max width: 1200px, centered
- Gap between cards: 2rem
- Responsive breakpoint: 768px

#### File: `frontend/src/App.tsx` (Modification)
Add route:
```typescript
<Route path="/" element={<PipelineSelection />} />
```

### Acceptance Criteria Checklist
- [ ] Two pipeline cards displayed (Ad Creative, Music Video)
- [ ] Ad Creative card is enabled and clickable
- [ ] Music Video card shows "Coming Soon" badge
- [ ] Each card displays: icon, title, description, features list, duration range
- [ ] "Start Creating" button navigates to generation form route
- [ ] Hover effects on enabled card (scale, shadow)
- [ ] Disabled card has reduced opacity, no hover effect
- [ ] Responsive layout (stacks on mobile <768px)
- [ ] TypeScript types defined for pipelines
- [ ] Accessible (ARIA labels, keyboard navigation)

### Testing Checklist
- [ ] Click Ad Creative → navigates to `/ad-creative/new`
- [ ] Click Music Video → no action (disabled)
- [ ] Responsive test at 375px, 768px, 1280px
- [ ] Keyboard navigation (Tab, Enter)
- [ ] Hover states work correctly

---

## PR-F007: Generation Form - Ad Creative

### Status
- **Estimate:** 5 hours
- **Priority:** Critical (core functionality)
- **Dependencies:** PR-F002 ✅, PR-F003 ✅, PR-F005 ✅, PR-F012 ✅
- **Can run in parallel with:** None (large component, recommend solo)

### Description
Multi-step form for creating Ad Creative videos with prompt input, brand settings, video parameters, and review/submit. This is the main user interaction for video generation.

### Files to Create (9 new files)
```
frontend/src/pages/AdCreativeForm.tsx                        [NEW] ~400 lines
frontend/src/components/GenerationForm/PromptInput.tsx       [NEW] ~200 lines
frontend/src/components/GenerationForm/BrandSettings.tsx     [NEW] ~250 lines
frontend/src/components/GenerationForm/VideoParameters.tsx   [NEW] ~200 lines
frontend/src/components/GenerationForm/ReviewStep.tsx        [NEW] ~180 lines
frontend/src/components/GenerationForm/StepIndicator.tsx     [NEW] ~100 lines
frontend/src/components/GenerationForm/index.ts              [NEW] ~20 lines
frontend/src/hooks/useGenerationForm.ts                      [NEW] ~300 lines
frontend/src/utils/validation.ts                             [NEW] ~150 lines
```

### Files to Modify (1 file)
```
frontend/src/App.tsx                                         [MODIFY] Add route
```

### Implementation Details

#### File: `frontend/src/utils/validation.ts`
**Validation Functions:**
- `validatePrompt(text: string)` - 500-2000 chars, not empty
- `validateBrandName(name: string)` - optional, 1-100 chars
- `validateLogoFile(file: File)` - JPEG/PNG, max 50MB, min 512x512
- `validateHexColor(color: string)` - valid hex format
- `validateCTA(text: string)` - optional, max 50 chars
- `validateDuration(seconds: number)` - 15, 30, 45, or 60
- `validateAspectRatio(ratio: string)` - '16:9', '9:16', or '1:1'

**Return Type:**
```typescript
interface ValidationResult {
  valid: boolean;
  error?: string;
}
```

#### File: `frontend/src/hooks/useGenerationForm.ts`
**State Management:**
```typescript
interface GenerationFormState {
  step: number; // 0-3
  prompt: string;
  brandName: string;
  logo: File | null;
  primaryColor: string;
  secondaryColor: string;
  enableCTA: boolean;
  ctaText: string;
  duration: 15 | 30 | 45 | 60;
  aspectRatio: '16:9' | '9:16' | '1:1';
  style: string;
  musicStyle: string;
}
```

**Hook Functions:**
- `nextStep()` - Validate current step, advance
- `prevStep()` - Go back one step
- `updateField(field, value)` - Update form field
- `submitForm()` - API call to create generation
- `saveToLocalStorage()` - Auto-save (debounced)
- `loadFromLocalStorage()` - Restore on mount
- `resetForm()` - Clear all fields

**LocalStorage Key:** `ad-creative-form-draft`

**API Integration:**
- Upload logo via `assetsService.uploadAsset(file)` (from PR-F003, PR-F012)
- Create generation via `generationService.createGeneration(params)` (from PR-F003)
- Navigate to `/generations/{id}/progress` on success

#### File: `frontend/src/components/GenerationForm/StepIndicator.tsx`
**Props:**
- `currentStep: number` (0-3)
- `steps: string[]` - ['Prompt', 'Brand', 'Parameters', 'Review']

**Features:**
- Horizontal progress bar
- Circle indicators for each step
- Active step highlighted
- Completed steps with checkmark
- Step labels below circles
- Responsive (shrink labels on mobile)

#### File: `frontend/src/components/GenerationForm/PromptInput.tsx`
**Props:**
- `value: string`
- `onChange: (value: string) => void`
- `error?: string`

**Features:**
- Large textarea (min 150px height, auto-expand)
- Character counter: "500 / 2000" format
- Color coding: red if <500 or >2000, green if valid
- Placeholder text with example prompt
- Error message display below
- Keyboard shortcuts (Cmd/Ctrl+Enter to continue?)

**Example Placeholder:**
```
"Create a 30-second video ad for our new eco-friendly water bottle.
Show it in outdoor adventure settings with active people.
Emphasize sustainability and durability. Include our tagline:
'Hydrate Responsibly.'"
```

**Optional Enhancement:**
- Prompt suggestion button (shows 3-5 templates)
- Template categories: Product, Service, Event, Announcement

#### File: `frontend/src/components/GenerationForm/BrandSettings.tsx`
**Props:**
- `values: BrandSettingsState`
- `onChange: (field, value) => void`
- `errors: Record<string, string>`

**Features:**
- Brand name text input (optional)
- Logo upload using `AssetUploader` from PR-F012
  - Single file mode
  - Preview thumbnail
  - Remove button
- Primary color picker
  - Input type="color"
  - Hex code text input
  - Visual preview swatch
- Secondary color picker (same as primary)
- CTA toggle switch
  - Checkbox "Include Call-to-Action"
  - Text input (appears when enabled)
  - Placeholder: "Shop Now", "Learn More", etc.

**Layout:**
- Two-column grid (desktop): logo left, colors right
- Single column (mobile)
- Color inputs side-by-side

#### File: `frontend/src/components/GenerationForm/VideoParameters.tsx`
**Props:**
- `values: VideoParamsState`
- `onChange: (field, value) => void`

**Features:**
- Duration selector:
  - Radio buttons for 15, 30, 45, 60 seconds
  - Visual cards with time display
  - Default: 30 seconds
- Aspect ratio selector:
  - Radio buttons with visual previews
  - 16:9 (Landscape), 9:16 (Portrait), 1:1 (Square)
  - Icon showing rectangle orientation
  - Default: 16:9
- Style dropdown:
  - Options: Professional, Casual, Modern, Vintage, Minimalist, Bold
  - Default: Professional
- Music style dropdown:
  - Options: Corporate, Upbeat, Cinematic, Ambient, Energetic, Calm
  - Default: Corporate

**Layout:**
- Duration and aspect ratio as large radio cards
- Style dropdowns below
- Grid layout on desktop

#### File: `frontend/src/components/GenerationForm/ReviewStep.tsx`
**Props:**
- `formState: GenerationFormState`
- `onEdit: (step: number) => void`
- `onSubmit: () => void`
- `isSubmitting: boolean`

**Features:**
- Summary sections for each step:
  1. **Prompt Section:**
     - Truncated prompt (first 200 chars... "Read more")
     - Edit button → goes to step 0
  2. **Brand Section:**
     - Brand name
     - Logo thumbnail
     - Color swatches with hex codes
     - CTA text (if enabled)
     - Edit button → goes to step 1
  3. **Parameters Section:**
     - Duration badge
     - Aspect ratio icon + label
     - Style and music style
     - Edit button → goes to step 2
- Estimated generation time:
  - Calculate based on duration: 15s → 2-3 min, 60s → 8-10 min
  - Display: "Estimated time: 5-7 minutes"
- Submit button (large, primary)
  - Disabled during submission
  - Shows spinner when submitting
  - Text: "Generate Video" or "Generating..." (when submitting)

**Layout:**
- Card-based sections
- Edit buttons in top-right of each card
- Submit button at bottom, centered, full-width on mobile

#### File: `frontend/src/pages/AdCreativeForm.tsx`
**Main Orchestration:**
- Use `useGenerationForm()` hook
- Render `StepIndicator`
- Conditional render based on `step`:
  - Step 0: `<PromptInput />`
  - Step 1: `<BrandSettings />`
  - Step 2: `<VideoParameters />`
  - Step 3: `<ReviewStep />`
- Navigation buttons:
  - "Back" button (disabled on step 0)
  - "Next" button (step 0-2) or "Review" button (step 2)
  - Hidden on step 3 (ReviewStep has Submit button)
- Page title: "Create Ad Creative Video"
- Breadcrumbs: Home > Ad Creative > New
- Auto-save indicator (small text: "Saved to draft")

**Error Handling:**
- Show toast notification on API errors
- Validation errors inline in each component
- Network errors: show retry button

**Success Flow:**
- On successful submission:
  - Clear localStorage draft
  - Show success toast: "Generation started!"
  - Navigate to `/generations/{id}/progress`

### Acceptance Criteria Checklist
- [ ] 4-step form with StepIndicator
- [ ] Step 1: Prompt input with 500-2000 char validation
- [ ] Step 2: Brand name, logo upload, color pickers, CTA toggle
- [ ] Step 3: Duration (15/30/45/60s), aspect ratio (16:9/9:16/1:1), style selectors
- [ ] Step 4: Review summary with edit buttons
- [ ] All validation rules enforced
- [ ] Error messages displayed inline
- [ ] Auto-save to localStorage (debounced)
- [ ] Form restoration on page load
- [ ] API integration: logo upload + generation creation
- [ ] Success redirect to progress page
- [ ] Loading states during submission
- [ ] Responsive design (mobile-friendly)

### Testing Checklist
- [ ] Validation: prompt too short (<500 chars) → error
- [ ] Validation: prompt too long (>2000 chars) → error
- [ ] Logo upload: valid file → preview shown
- [ ] Logo upload: invalid file (PDF) → error
- [ ] Logo upload: file too large (>50MB) → error
- [ ] Color picker: enter invalid hex → error
- [ ] Step navigation: Next/Back buttons work
- [ ] Step navigation: can't advance if current step invalid
- [ ] Review step: edit buttons navigate to correct step
- [ ] Submit: successful API call → navigate to progress
- [ ] Submit: API error → show error message
- [ ] LocalStorage: form saved on field change
- [ ] LocalStorage: form restored on page load
- [ ] Responsive: test all steps at 375px, 768px, 1280px

---

## PR-F009: Progress Tracking Component

### Status
- **Estimate:** 4 hours
- **Priority:** Critical (user feedback during generation)
- **Dependencies:** PR-F002 ✅, PR-F004 ✅
- **Can run in parallel with:** F006, F010, F011

### Description
Real-time progress display for video generation showing step-by-step status, clip previews, and estimated time remaining. Uses WebSocket for live updates with polling fallback.

### Files to Create (7 new files)
```
frontend/src/pages/GenerationProgress.tsx                    [NEW] ~350 lines
frontend/src/components/Progress/ProgressBar.tsx             [NEW] ~100 lines
frontend/src/components/Progress/StepIndicator.tsx           [NEW] ~150 lines
frontend/src/components/Progress/ClipPreview.tsx             [NEW] ~120 lines
frontend/src/components/Progress/index.ts                    [NEW] ~20 lines
frontend/src/hooks/useGenerationProgress.ts                  [NEW] ~250 lines
frontend/src/utils/timeEstimate.ts                           [NEW] ~50 lines
```

### Files to Modify (1 file)
```
frontend/src/App.tsx                                         [MODIFY] Add route
```

### Implementation Details

#### File: `frontend/src/utils/timeEstimate.ts`
**Functions:**
- `calculateRemainingTime(progress: number, elapsedMs: number)` → string
- `formatDuration(seconds: number)` → "5m 30s"
- `getEstimatedTotal(duration: number)` → total seconds estimate
  - 15s video → 2-3 minutes
  - 30s video → 5-7 minutes
  - 45s video → 7-9 minutes
  - 60s video → 8-10 minutes

**Algorithm:**
```typescript
// Linear interpolation based on current progress
const totalEstimateMs = elapsedMs / (progress / 100);
const remainingMs = totalEstimateMs - elapsedMs;
```

#### File: `frontend/src/hooks/useGenerationProgress.ts`
**State:**
```typescript
interface GenerationProgressState {
  generationId: string;
  status: GenerationStatus;
  progress: number; // 0-100
  currentStep: string;
  clips: ClipInfo[];
  startTime: number;
  error: string | null;
  isPolling: boolean; // true if WebSocket failed
}
```

**Features:**
- Subscribe to WebSocket events (from PR-F004 hook)
  - `generation_progress` → update progress %
  - `clip_completed` → add to clips array
  - `status_change` → update status
  - `generation_completed` → redirect to preview
  - `generation_failed` → show error
- Fallback to polling if WebSocket not connected:
  - Poll `GET /api/v1/generations/{id}` every 5 seconds
  - Update state from response
- Track elapsed time with `Date.now() - startTime`
- Calculate remaining time estimate
- Cancel functionality:
  - `cancelGeneration()` → POST `/api/v1/generations/{id}/cancel`
  - Show confirmation dialog first

**Cleanup:**
- Unsubscribe from WebSocket on unmount
- Clear polling interval on unmount

#### File: `frontend/src/components/Progress/ProgressBar.tsx`
**Props:**
- `progress: number` (0-100)
- `label?: string`
- `showPercentage?: boolean`

**Features:**
- Horizontal bar with filled portion
- Smooth animated transitions (CSS transition)
- Percentage text overlay (center of bar)
- Color gradient: blue → green as it progresses
- Rounded corners
- Height: 24px (desktop), 20px (mobile)

**Styling:**
- Background: light gray
- Fill: linear gradient (primary color → success color)
- Text: white, bold, centered

#### File: `frontend/src/components/Progress/StepIndicator.tsx`
**Props:**
- `currentStep: string`
- `steps: GenerationStep[]`

```typescript
interface GenerationStep {
  name: string;
  status: 'completed' | 'in-progress' | 'pending';
  detail?: string; // e.g., "5/10 clips"
}
```

**Steps:**
1. Input Validation ✓
2. Content Planning (analyzing prompt...)
3. Asset Generation (5/10 clips)
4. Video Composition (pending)
5. Final Rendering (pending)

**Features:**
- Vertical timeline (left side)
- Each step has:
  - Icon (✓ for completed, spinner for in-progress, ○ for pending)
  - Step name
  - Detail text (gray, smaller)
- Connecting line between steps
- Current step highlighted (bold, primary color)

**Layout:**
- Vertical list
- Fixed width: 300px (desktop), full-width (mobile)
- Icons aligned left, text indented

#### File: `frontend/src/components/Progress/ClipPreview.tsx`
**Props:**
- `clip: ClipInfo`

```typescript
interface ClipInfo {
  id: string;
  url: string;
  thumbnail: string;
  duration: number;
  clipNumber: number;
}
```

**Features:**
- Card with thumbnail image
- Clip number badge (top-left): "#3"
- Duration badge (bottom-right): "5.2s"
- Hover effect: slight scale, shadow
- Click to view full clip (optional enhancement)

**Styling:**
- Aspect ratio: 16:9 (or match video aspect ratio)
- Border radius: 8px
- Shadow on hover
- Thumbnail: object-fit: cover

#### File: `frontend/src/pages/GenerationProgress.tsx`
**Main Component:**
- Get `generationId` from URL params: `/generations/:id/progress`
- Use `useGenerationProgress(generationId)` hook
- Page sections:
  1. **Header:**
     - Page title: "Generating Your Video"
     - Status badge: "Processing", "Composing", etc.
     - Cancel button (top-right)
  2. **Progress Section:**
     - Large percentage: "45%"
     - ProgressBar component
     - Estimated time: "~3 minutes remaining"
  3. **Steps Section:**
     - StepIndicator component
     - Current step highlighted
  4. **Clips Section:**
     - Grid of completed clips (2-4 columns)
     - ClipPreview components
     - Empty state: "Generating clips..."
     - Fade-in animation as clips appear
  5. **Footer:**
     - Connection status: "Live updates" or "Polling for updates"
     - Generation ID (small text)

**Cancel Dialog:**
- Modal popup: "Are you sure you want to cancel this generation?"
- Buttons: "Cancel Generation" (destructive), "Keep Generating"
- On confirm: call API, show toast, redirect to history

**Error State:**
- If generation fails:
  - Red error banner
  - Error message from API
  - "Try Again" button → navigate to form
  - "View Details" button → show full error

**Completion:**
- When status === 'completed':
  - Show success animation (confetti or checkmark)
  - "Your video is ready!" message
  - Auto-redirect after 2 seconds OR "View Video" button

**Layout:**
- Two-column (desktop): steps left, progress/clips right
- Single-column (mobile): stacked
- Max width: 1400px, centered

### Acceptance Criteria Checklist
- [ ] Display overall progress percentage (0-100%)
- [ ] ProgressBar with smooth animations
- [ ] Step-by-step indicator showing current phase
- [ ] Estimated time remaining (calculated based on progress)
- [ ] Real-time updates via WebSocket:
  - [ ] Progress updates
  - [ ] Clip completion events
  - [ ] Status changes
- [ ] Fallback to polling if WebSocket fails (every 5s)
- [ ] Grid of completed clips with thumbnails
- [ ] Clip previews show number and duration
- [ ] Cancel button with confirmation dialog
- [ ] Cancel API integration
- [ ] Success redirect to preview page
- [ ] Error display for failed generations
- [ ] Connection status indicator
- [ ] Responsive design

### Testing Checklist
- [ ] WebSocket updates: progress increases in real-time
- [ ] WebSocket updates: clips appear as completed
- [ ] WebSocket failure: falls back to polling
- [ ] Polling: updates every 5 seconds
- [ ] Cancel: confirmation dialog appears
- [ ] Cancel: API called on confirm
- [ ] Cancel: redirect to history after cancel
- [ ] Completion: redirects to preview page
- [ ] Error: error message displayed
- [ ] Time estimate: updates as progress changes
- [ ] Responsive: test at 375px, 768px, 1280px
- [ ] Multiple clips: grid layout works with 1, 5, 10 clips

---

## PR-F010: Video Preview & Download Page

### Status
- **Estimate:** 3 hours
- **Priority:** High (completion of user journey)
- **Dependencies:** PR-F008 ✅, PR-F003 ✅
- **Can run in parallel with:** F006, F009, F011

### Description
Page to preview completed video with playback controls and download functionality. Shows video metadata and provides options to create another video or return to history.

### Files to Create (4 new files)
```
frontend/src/pages/VideoPreview.tsx                  [NEW] ~300 lines
frontend/src/components/VideoActions.tsx             [NEW] ~150 lines
frontend/src/components/VideoMetadata.tsx            [NEW] ~120 lines
frontend/src/hooks/useVideoDownload.ts               [NEW] ~100 lines
```

### Files to Modify (1 file)
```
frontend/src/App.tsx                                 [MODIFY] Add route
```

### Implementation Details

#### File: `frontend/src/hooks/useVideoDownload.ts`
**Features:**
- `downloadVideo(compositionId: string, filename: string)`
- Track download progress (0-100%)
- API call: `GET /api/v1/compositions/{id}/download`
- Use fetch with progress tracking:
  ```typescript
  const response = await fetch(url);
  const reader = response.body.getReader();
  const contentLength = +response.headers.get('Content-Length');

  let receivedLength = 0;
  const chunks = [];

  while (true) {
    const {done, value} = await reader.read();
    if (done) break;
    chunks.push(value);
    receivedLength += value.length;
    setProgress((receivedLength / contentLength) * 100);
  }
  ```
- Create Blob and download via `<a>` element
- Success toast notification
- Error handling

**State:**
```typescript
interface DownloadState {
  isDownloading: boolean;
  progress: number;
  error: string | null;
}
```

#### File: `frontend/src/components/VideoMetadata.tsx`
**Props:**
- `generation: GenerationResponse`
- `composition: CompositionResponse`

**Display:**
- Generation ID (truncated, with copy button)
- Duration (formatted: "0:45")
- Resolution (e.g., "1920x1080 (16:9)")
- File size (e.g., "24.5 MB")
- Created date (relative: "2 hours ago" + full timestamp)
- Status badge (should be "completed")

**Layout:**
- Grid of metadata items
- Each item: label (gray, small) + value (larger, bold)
- 2 columns (desktop), 1 column (mobile)

**Copy Generation ID:**
- Small copy icon next to ID
- Click → copy to clipboard
- Show toast: "Generation ID copied!"

#### File: `frontend/src/components/VideoActions.tsx`
**Props:**
- `compositionId: string`
- `generationId: string`
- `onDownload: () => void`
- `isDownloading: boolean`
- `downloadProgress: number`

**Buttons:**
1. **Download Button (Primary):**
   - Large, prominent
   - Icon: download arrow
   - Text: "Download Video" or "Downloading... 45%"
   - Disabled during download
   - Progress bar overlay when downloading

2. **Create Another Video:**
   - Secondary button
   - Navigate to pipeline selection or form

3. **Return to History:**
   - Secondary button
   - Navigate to `/history`

4. **Share (Optional):**
   - Copy link button
   - Copies current URL to clipboard
   - Toast: "Link copied!"

**Layout:**
- Horizontal row (desktop), stacked (mobile)
- Primary button full-width or prominent
- Secondary buttons side-by-side

#### File: `frontend/src/pages/VideoPreview.tsx`
**URL:** `/generations/:generationId/preview` or `/videos/:compositionId`

**Data Fetching:**
- Get `generationId` from URL params
- Fetch generation: `GET /api/v1/generations/{id}`
- Fetch assets: `GET /api/v1/generations/{id}/assets`
- Find composition from assets (final video)
- Extract video URL for player

**Page Structure:**
1. **Header:**
   - Breadcrumbs: Home > History > Video
   - Page title: "Your Video is Ready!"
   - Success icon/animation

2. **Video Player Section:**
   - Use `VideoPlayer` component from PR-F008
   - Video URL from composition assets
   - Full-width player (max-width: 1200px)
   - Centered

3. **Actions Section:**
   - `VideoActions` component
   - Download functionality
   - Navigation buttons

4. **Metadata Section:**
   - `VideoMetadata` component
   - Collapsible section (optional)

5. **Parameters Summary (Optional):**
   - Show original generation parameters
   - Collapsible section: "Generation Details"
   - Display: prompt, brand settings, video params
   - "Regenerate with same settings" button

**States:**
- Loading: show skeleton or spinner while fetching
- Error: if generation not found or not completed
- Success: show video player and actions

**Error Handling:**
- Generation not found → 404 message
- Generation not complete → redirect to progress page
- Video not available → error message with retry

**Layout:**
- Single column, centered
- Max width: 1200px
- Sections separated with spacing

### Acceptance Criteria Checklist
- [ ] Video player (from PR-F008) displays completed video
- [ ] Video metadata display:
  - [ ] Generation ID (with copy button)
  - [ ] Duration
  - [ ] Resolution
  - [ ] File size
  - [ ] Creation date
- [ ] Action buttons:
  - [ ] Download button (primary)
  - [ ] Create Another Video
  - [ ] Return to History
  - [ ] Share (copy link)
- [ ] Download functionality:
  - [ ] Progress indicator during download
  - [ ] Success toast notification
  - [ ] Error handling
- [ ] Generation parameters summary (optional)
- [ ] Re-run option (loads same params into form)
- [ ] Loading states while fetching data
- [ ] Error handling for missing/incomplete generations
- [ ] Responsive design

### Testing Checklist
- [ ] Fetch generation: successful → video player shown
- [ ] Fetch generation: not found → error message
- [ ] Fetch generation: still processing → redirect to progress
- [ ] Video player: playback works correctly
- [ ] Download: successful → file downloads
- [ ] Download: progress indicator shown
- [ ] Download: error → error message and retry
- [ ] Copy generation ID → clipboard + toast
- [ ] Copy share link → clipboard + toast
- [ ] Create Another Video → navigates correctly
- [ ] Return to History → navigates to /history
- [ ] Responsive: test at 375px, 768px, 1280px

---

## PR-F011: Generation History Page

### Status
- **Estimate:** 4 hours
- **Priority:** High (user management of generations)
- **Dependencies:** PR-F003 ✅, PR-F005 ✅
- **Can run in parallel with:** F006, F009, F010

### Description
Paginated list of user's video generation jobs with filtering by status, search by prompt text, and sorting options. Provides quick actions for each generation.

### Files to Create (7 new files)
```
frontend/src/components/History/GenerationCard.tsx           [NEW] ~200 lines
frontend/src/components/History/FilterSidebar.tsx            [NEW] ~180 lines
frontend/src/components/History/EmptyState.tsx               [NEW] ~80 lines
frontend/src/components/History/index.ts                     [NEW] ~20 lines
frontend/src/components/Pagination.tsx                       [NEW] ~120 lines
frontend/src/hooks/useGenerationHistory.ts                   [NEW] ~200 lines
frontend/src/utils/dateFormat.ts                             [NEW] ~60 lines
```

### Files to Modify (1 file)
```
frontend/src/pages/History.tsx                               [MODIFY] ~400 lines
```

### Implementation Details

#### File: `frontend/src/utils/dateFormat.ts`
**Functions:**
- `formatRelativeTime(date: Date)` → "2 hours ago", "3 days ago"
- `formatFullDate(date: Date)` → "Nov 15, 2025 at 3:45 PM"
- `formatShortDate(date: Date)` → "Nov 15"
- `getTimeAgo(timestamp: number)` → relative time string

**Use libraries:**
- Consider using `date-fns` or built-in `Intl.RelativeTimeFormat`

#### File: `frontend/src/hooks/useGenerationHistory.ts`
**State:**
```typescript
interface HistoryState {
  generations: GenerationResponse[];
  total: number;
  page: number;
  limit: number;
  status: GenerationStatus | 'all';
  sortBy: 'date' | 'duration' | 'status';
  sortOrder: 'asc' | 'desc';
  searchQuery: string;
  isLoading: boolean;
  error: string | null;
}
```

**Features:**
- Fetch generations: `GET /api/v1/generations?page={page}&limit={limit}&status={status}&sort={sortBy}`
- Pagination controls:
  - `nextPage()`
  - `prevPage()`
  - `goToPage(page: number)`
  - `setLimit(limit: number)`
- Filter controls:
  - `setStatusFilter(status: GenerationStatus | 'all')`
  - `setSortBy(field: string)`
  - `setSearchQuery(query: string)` - debounced (500ms)
- Delete generation:
  - `deleteGeneration(id: string)` → DELETE `/api/v1/generations/{id}`
  - Confirmation required (from parent)
  - Refresh list after delete
- Refresh/reload:
  - `refresh()` - re-fetch current page

**Query Parameters:**
- Build URL query string from state
- Update URL params in browser (for bookmarking)
- Parse URL params on mount (restore state)

**Debounced Search:**
- Use `useDebounce` hook or lodash debounce
- Wait 500ms after typing stops before searching

#### File: `frontend/src/components/Pagination.tsx`
**Props:**
- `currentPage: number`
- `totalPages: number`
- `totalItems: number`
- `itemsPerPage: number`
- `onPageChange: (page: number) => void`
- `onLimitChange: (limit: number) => void`

**Features:**
- Previous/Next buttons
- Page numbers (show 5 pages max, with ellipsis)
  - Example: "< 1 2 3 ... 10 >"
  - Current page highlighted
- Items per page selector:
  - Dropdown: 20, 50, 100
  - Label: "Show per page"
- Total count display: "Showing 21-40 of 156"

**Behavior:**
- Disable Previous on page 1
- Disable Next on last page
- Click page number → jump to page
- Change items per page → reset to page 1

**Styling:**
- Horizontal layout
- Buttons: small, secondary style
- Current page: primary color background
- Disabled buttons: gray, reduced opacity

#### File: `frontend/src/components/History/EmptyState.tsx`
**Props:**
- `hasFilters: boolean`

**Two States:**
1. **No Generations Ever:**
   - Icon: empty folder or video camera
   - Title: "No videos yet"
   - Message: "Create your first video to get started!"
   - Button: "Create Video" → navigate to pipeline selection

2. **No Results (with filters):**
   - Icon: search or filter
   - Title: "No videos found"
   - Message: "Try adjusting your filters or search query"
   - Button: "Clear Filters"

**Styling:**
- Centered content
- Large icon (80px)
- Gray text
- Primary button

#### File: `frontend/src/components/History/FilterSidebar.tsx`
**Props:**
- `filters: FilterState`
- `onChange: (filters: FilterState) => void`
- `onReset: () => void`

**Filters:**
1. **Status Filter:**
   - Radio buttons or checkbox list:
     - All
     - Completed
     - Processing (queued, processing, composing)
     - Failed
     - Cancelled
   - Count badges (optional): "Completed (45)"

2. **Date Range:**
   - Preset options:
     - Last 24 hours
     - Last 7 days
     - Last 30 days
     - All time (default)
   - Custom date picker (optional enhancement)

3. **Pipeline Type:**
   - Checkboxes:
     - Ad Creative
     - Music Video
   - (For post-MVP)

4. **Sort Options:**
   - Dropdown:
     - Newest first (default)
     - Oldest first
     - Longest duration
     - Shortest duration

**Actions:**
- "Reset Filters" button at bottom
- Apply filters immediately on change

**Layout:**
- Vertical sidebar (desktop): fixed width 280px
- Collapsible panel (mobile): slide from left
- Sections separated with dividers

#### File: `frontend/src/components/History/GenerationCard.tsx`
**Props:**
- `generation: GenerationResponse`
- `onView: () => void`
- `onDownload: () => void`
- `onDelete: () => void`

**Card Content:**
1. **Thumbnail:**
   - Video thumbnail (if completed)
   - Placeholder image (if processing/failed)
   - Status overlay (if processing/failed):
     - Spinner icon + "Processing..."
     - Error icon + "Failed"

2. **Metadata:**
   - Status badge (colored):
     - Completed: green
     - Processing: blue
     - Failed: red
     - Cancelled: gray
   - Generation ID (truncated): "#abc123..."
   - Created date: "2 hours ago"
   - Duration (if completed): "0:45"

3. **Prompt Preview:**
   - First 100 characters of prompt
   - "..." if truncated
   - Gray text, smaller font

4. **Quick Actions:**
   - Icon buttons:
     - View (eye icon) - navigate to preview page
     - Download (download icon) - only if completed
     - Delete (trash icon) - with confirmation
   - Tooltip on hover

**States:**
- Hover: slight shadow, scale
- Clicked: brief highlight
- Deleting: show spinner, disabled

**Layout:**
- Card with border
- Thumbnail on left (or top on mobile)
- Content on right (or below on mobile)
- Actions in bottom-right corner
- Responsive: stack vertically on mobile

#### File: `frontend/src/pages/History.tsx` (Major Update)
**Current State:**
- Exists from PR-F005 as basic placeholder
- Need to add full functionality

**Page Structure:**
1. **Header:**
   - Page title: "Generation History"
   - Search bar (top-right):
     - Input with search icon
     - Placeholder: "Search by prompt..."
     - Debounced search
   - "New Video" button (top-right)

2. **Layout:**
   - Two-column (desktop):
     - Left: FilterSidebar (280px)
     - Right: Results (flex grow)
   - Single-column (mobile):
     - Filter button opens drawer
     - Results full-width

3. **Results Section:**
   - Loading skeleton (while fetching)
   - EmptyState (if no results)
   - Grid of GenerationCards:
     - 1 column (mobile)
     - 2 columns (tablet)
     - 3 columns (desktop >1200px)
   - Gap between cards: 1.5rem

4. **Pagination:**
   - At bottom of results
   - Sticky on scroll (optional)

**Delete Confirmation:**
- Modal dialog:
  - Title: "Delete Generation?"
  - Message: "This will permanently delete the video and all associated data. This cannot be undone."
  - Buttons: "Cancel", "Delete" (destructive)
- On confirm: call delete API, show toast, refresh list

**URL State Management:**
- Update URL query params as filters change:
  - `?page=2&status=completed&sort=date&q=product`
- Parse URL on mount to restore state
- Enables bookmarking and back button

**Performance:**
- Use `React.memo` for GenerationCard
- Virtualize list if many items (optional, use react-window)

### Acceptance Criteria Checklist
- [ ] Paginated list of generations (20 per page default)
- [ ] GenerationCard shows:
  - [ ] Thumbnail or placeholder
  - [ ] Status badge with color
  - [ ] Generation ID
  - [ ] Created date (relative time)
  - [ ] Duration (if completed)
  - [ ] Prompt preview (truncated)
  - [ ] Quick action buttons
- [ ] FilterSidebar with:
  - [ ] Status filter (all, completed, processing, failed, cancelled)
  - [ ] Date range presets
  - [ ] Sort options
  - [ ] Reset button
- [ ] Search functionality:
  - [ ] Search by prompt text
  - [ ] Debounced input (500ms)
- [ ] Pagination controls:
  - [ ] Previous/Next buttons
  - [ ] Page numbers
  - [ ] Items per page selector (20, 50, 100)
  - [ ] Total count display
- [ ] Quick actions:
  - [ ] View → navigate to preview page
  - [ ] Download → download video (if completed)
  - [ ] Delete → confirmation dialog, then delete
- [ ] EmptyState for:
  - [ ] No generations ever
  - [ ] No results matching filters
- [ ] Loading skeleton during fetch
- [ ] Error handling for failed API calls
- [ ] URL state management (filters, page, search in URL)
- [ ] Responsive design

### Testing Checklist
- [ ] Initial load: fetch first page of generations
- [ ] Pagination: next/prev buttons work
- [ ] Pagination: page number click jumps to page
- [ ] Pagination: change items per page resets to page 1
- [ ] Filter by status: only shows matching items
- [ ] Filter by date: only shows recent items
- [ ] Sort: newest/oldest/duration works correctly
- [ ] Search: debounced, filters results by prompt
- [ ] Search: clear search restores all results
- [ ] View action: navigates to preview page
- [ ] Download action: downloads video file
- [ ] Delete action: shows confirmation dialog
- [ ] Delete action: removes from list on confirm
- [ ] Delete action: shows error if API fails
- [ ] Empty state: shows when no generations
- [ ] Empty state: shows when filters have no results
- [ ] URL params: filters reflected in URL
- [ ] URL params: page refresh restores state
- [ ] Responsive: sidebar collapses on mobile
- [ ] Responsive: cards stack on mobile
- [ ] Responsive: test at 375px, 768px, 1280px

---

## File Conflict Analysis

### No Conflicts (Can run fully in parallel):

**Group 1:**
- **PR-F006:** 3 new files, 1 modify (App.tsx route only)
- **PR-F009:** 7 new files, 1 modify (App.tsx route only)
- **PR-F010:** 4 new files, 1 modify (App.tsx route only)
- **PR-F011:** 7 new files, 1 modify (History.tsx major update, App.tsx route)

**Note:** All modify `App.tsx` but only to add routes. These can be done in parallel with merge conflict resolution, or sequentially with git pulls between PRs.

**PR-F007:** Should ideally run after others to benefit from any shared utilities (validation, formatting) that might be created.

### Recommended Parallel Execution Strategy

**Option A: Maximum Parallelism (4 simultaneous PRs)**
```
Wave 1 (Parallel):
├─ PR-F006: Pipeline Selection (2h)
├─ PR-F009: Progress Tracking (4h)
├─ PR-F010: Video Preview (3h)
└─ PR-F011: Generation History (4h)

Wave 2 (Solo):
└─ PR-F007: Generation Form (5h)
```

**Total Time:** ~9 hours (4h Wave 1 + 5h Wave 2)

**Option B: Conservative Parallelism (2-3 simultaneous PRs)**
```
Wave 1:
├─ PR-F006: Pipeline Selection (2h)
└─ PR-F011: Generation History (4h)

Wave 2:
├─ PR-F009: Progress Tracking (4h)
└─ PR-F010: Video Preview (3h)

Wave 3:
└─ PR-F007: Generation Form (5h)
```

**Total Time:** ~13 hours (4h + 4h + 5h)

---

## Integration Notes

### Shared Dependencies (Already Complete)
- **Design System (PR-F002):** Button, Input, Card, Toast, Spinner
- **API Client (PR-F003):** All service modules, error handling
- **WebSocket (PR-F004):** useWebSocket hook, event handling
- **Routing (PR-F005):** React Router, MainLayout, Navigation
- **Video Player (PR-F008):** VideoPlayer component with controls
- **Asset Upload (PR-F012):** AssetUploader component

### Cross-PR Utilities to Create
These utilities may be created in multiple PRs and should be consolidated:

1. **Validation (`utils/validation.ts`):**
   - Created in F007, may be used by others
   - Ensure consistent validation logic

2. **Date Formatting (`utils/dateFormat.ts`):**
   - Created in F011, may be useful for F009, F010
   - Standardize relative time formatting

3. **Time Estimates (`utils/timeEstimate.ts`):**
   - Created in F009, may be referenced in F007 review step

### API Integration Checklist
- [ ] All endpoints match `api-specification-edited.md`
- [ ] Error codes mapped to user-friendly messages
- [ ] Request IDs included in headers
- [ ] Loading states for all async operations
- [ ] Error handling with retry mechanisms
- [ ] Toast notifications for user feedback

### Testing Integration Points
1. **F006 → F007:** Pipeline selection navigates to generation form
2. **F007 → F009:** Form submission navigates to progress page
3. **F009 → F010:** Completion navigates to preview page
4. **F010 → F006:** "Create Another" navigates to pipeline selection
5. **F010 → F011:** "Return to History" navigates to history page
6. **F011 → F010:** View action navigates to preview page

---

## Success Metrics

After completing these 5 PRs, the MVP will support:
- ✅ Pipeline selection (Ad Creative vs Music Video)
- ✅ Full generation form with all parameters
- ✅ Real-time progress tracking with WebSocket
- ✅ Video preview and download
- ✅ Generation history management

**Remaining for MVP:**
- PR-F013: Timeline Editor (6 hours) - blocked by F009
- PR-F014: Error Handling (3 hours) - blocked by form components
- PR-F015: Mobile Responsive (4 hours) - blocked by all components

**MVP Completion:** After these 5 PRs + remaining 3 PRs = ~31 hours total

---

## Next Steps

1. **Review this plan** with team for accuracy
2. **Assign PRs** to available agents/developers
3. **Start Wave 1** (F006, F009, F010, F011 in parallel)
4. **Merge and test** Wave 1 PRs
5. **Start F007** (Generation Form)
6. **Integration testing** across all PRs
7. **Move to remaining PRs** (F013, F014, F015)

---

**Document Created:** 2025-11-15
**Last Updated:** 2025-11-15
**Status:** Ready for implementation
