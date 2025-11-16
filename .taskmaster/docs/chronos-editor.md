
# Chronos Editor — Product Requirements Document (PRD)
## Version 2.1 — Updated with Engineering-Ready Details  
Target Launch: Q4 2025  
Primary Stakeholder: Product Manager  
Product Manager: Gemini (AI Assistant)  
Project Name: Chronos Editor  

---

# 1. Introduction & Goals

## 1.1 Project Overview
Chronos Editor is a modern, browser-based, non-destructive media editor built around a track-based timeline UI that supports image, video, audio, and text editing. The application focuses on speed, responsiveness, real-time preview, and seamless asset ingestion (manual upload + AI generation).

## 1.2 Audience
- Content creators  
- Social media managers  
- Small businesses  
- Users needing quick professional-grade clip editing without desktop software

## 1.3 Success Metrics
- 90% of users complete a 3‑clip edit in under 5 minutes  
- All timeline interactions respond <100ms  
- 500 MAU within 6 months of launch  

---

# 2. Environment Variables & Global Constants

All tunable system-wide constants MUST be configurable via environment variables.

| Constant | Env Var | Default | Description |
|---------|---------|---------|-------------|
| Max Output Duration | `MAX_DURATION_SECONDS` | `600` | Maximum project length in seconds (10 minutes). |
| Default FPS (timebase) | `DEFAULT_TIMEBASE_FPS` | `30` | Internal timeline timebase FPS. |
| Max Concurrent Generations | `MAX_GENERATIONS` | `5` | Max simultaneous image/video AI generations. |
| Thumbnail Cache Limit | `THUMBNAIL_CACHE_MAX_BYTES` | `200000000` | IndexedDB cache limit for thumbnails (200MB). |
| Thumbnail Cache LRU Enabled | `THUMBNAIL_CACHE_ENABLE_LRU` | `true` | Evict least recently used thumbnails first. |

---

# 3. Technical Architecture

## 3.1 Frontend Stack
- **Vite + React** (FC + hooks)
- **TailwindCSS**
- **shadcn/ui** components
- **Zustand** for real-time global state
- **react-window** / **react-virtuoso** for timeline virtualization
- **IndexedDB** for caching thumbnails
- **WebSocket** for job status updates

## 3.2 Composition-Wide Timebase
Chronos uses a **composition-level frame-based timebase**.

```ts
timebase_fps: 24 | 30 | 60 // default 30
```

Timeline internal units = **frames**, not seconds.

Conversions:
```
frame = Math.round(seconds * timebase_fps)
seconds = frame / timebase_fps
```

---

# 4. Playback Engine Specification

## 4.1 Hybrid DOM + Timeline Engine (Recommended Implementation)
A high-performance but simplified preview system that approximates final export:

### What the preview engine does:
- Calculates active clips at given frame
- Applies CSS transforms:
  - opacity
  - scale
  - X/Y position
- Renders video tracks using a single `<video>` element
- Renders text/image overlays as DOM layers
- Approximates transitions using CSS animations

### What it does NOT do:
- Multi-video-layer compositing  
- High-fidelity ffmpeg-grade transitions  
- Perfect audio pitch correction during speed changes  

**Final export becomes authoritative.**

---

# 5. Media Types & Ingestion

## 5.1 Manual Ingestion
Sources:
- File picker  
- Copy/paste  
- URL ingestion  
- Dropbox link integration  

Backend endpoint required:
```
POST /api/v1/media/upload
```

## 5.2 AI Generation
Supports multiple generations concurrently up to:

```
MAX_GENERATIONS (default 5)
```

| Type | Endpoint | Schema |
|------|----------|--------|
| Image | POST /api/v1/replicate/nano-banana | NanoBananaRequest |
| Video | POST /api/v1/replicate/wan-video-i2v | WanVideoI2VRequest |

Aspect ratio MUST be included in requests.

---

# 6. Media Library Panel

- Virtualized grid  
- Lazy-loaded thumbnails  
- Real-time job status  
- Tagging, folders, filters, sorting  
- Bulk actions  
- Metadata modal (edit tags, folder, filename)  
- WebSocket updates when new media arrives  

---

# 7. Timeline & Editing Functionality

## 7.1 Tracks
- Unlimited tracks  
- Track types: video, audio, text  
- Editable label  
- Lock/mute toggles  
- Track reordering  

## 7.2 Clips
Each clip supports:
- trimming  
- move & drag  
- cross-track dragging  
- rename  
- transitions  
- speed  
- opacity  
- scale  
- X/Y position  
- volume / mute  
- splitting  

## 7.3 Clip Splitting
Split by:
- Right‑click → “Split at Playhead”
- Clicking Split button in control bar

Splitting creates two new clips with inherited properties.

Undo/redo supported.

---

# 8. Timeline Zoom

## 8.1 Controls
- **+ / – buttons**  
- **Ctrl + Scroll**  
- Zoom anchored at:
  - playhead (default)
  - or mouse position  

## 8.2 Behavior
Zoom changes:
```
pixelsPerSecond = base * zoomLevel
zoomLevel ranges 0.25 → 8.0
```

Horizontal scrolling:
- trackpad
- shift + scroll

---

# 9. Real-Time Updates (WebSocket Protocol)

## 9.1 Message Shape
```ts
type JobUpdateMessage = {
  type: "job.update";
  job_id: string;
  job_kind: "image_generation" | "video_generation" | "export";
  status: "queued" | "running" | "succeeded" | "failed" | "canceled";
  progress?: number;
  media_asset_id?: string;
  composition_id?: string;
  download_url?: string;
  error_code?: string;
  error_message?: string;
};
```

## 9.2 Events
- Media generation progress  
- Export progress  
- Completion → send download URL  
- Failure → send error details  

---

# 10. Media Details Panel

Supports:
- Clip label  
- Start / end time  
- Duration (derived)  
- Speed  
- Volume / mute  
- Scale  
- X/Y position  
- Opacity  
- Transitions in/out  
- Text content for text clips  

All fields are bidirectionally synced.

---

# 11. Export System

## 11.1 Export Settings
- Name  
- Aspect ratio  
- Resolution  
- Format  
- Quality  
- Frame rate  

## 11.2 API Flow
```
POST /api/v1/compositions/
```

WebSocket notifies on export completion.

Download via signed S3 URL.

---

# 12. Mobile Layout

Mobile is supported with a simplified UI:
- Stacked layout  
- Smaller “Timeline Lite”  
- Full playback controls  
- Asset browsing  
- Clip detail editing  
- Light trimming  

Full multi-track editing is desktop‑only.

---

# 13. Thumbnail Cache (IndexedDB LRU)

## 13.1 Maximum Cache Size
```
THUMBNAIL_CACHE_MAX_BYTES (default 200MB)
```

## 13.2 LRU Eviction Strategy
Each entry:
```ts
{
 id: string,
 size_bytes: number,
 last_accessed_at: number,
 blob: Blob
}
```

When the cache exceeds max:
- Sort by `last_accessed_at`
- Delete oldest items
- Repeat until under cap

---

# 14. Dirty State Indicator (Unsaved Changes)

When the project has unsaved changes:

- Display: `● My Project`  
- Tooltip: “Unsaved changes”  
- Prevent accidental closing  
- Cleared only after successful backend save  

---

# 15. Error Taxonomy

## 15.1 Network Errors
Connectivity or server unreachable  
UI: toast + retry

## 15.2 Asset Ingestion Errors
File too large, unsupported format, failed upload

## 15.3 Export/Rendering Errors
ffmpeg failures, invalid settings  
Show detailed error in Export modal

## 15.4 Timeline Manipulation Errors
Edge case invalid edits  
User-facing toast + internal logging

## 15.5 Schema Validation Errors
Backend rejects invalid payload  
Surface human-readable messages  
Detailed logs for debugging  

---

# 16. Testing Strategy

## 16.1 Unit Tests
- reducers/state logic  
- snapping  
- ripple edits  
- splitting  
- undo/redo  
- zooming  
- time/frame conversions  

## 16.2 Integration Tests
- User edits a 3-clip timeline  
- AI generation asset lifecycle  
- Export lifecycle  
- WebSocket reliability  

---

# 17. JSON Schemas (Engineering Ready)

## 17.1 MediaAsset

```ts
interface MediaAsset {
  id: UUID;
  owner_user_id: UUID;
  type: "image" | "video" | "audio" | "text";
  url: string;
  thumbnail_url?: string;
  filename: string;
  size_bytes?: number;
  duration_seconds?: number;
  width?: number;
  height?: number;
  frame_rate?: number;
  codec?: string;
  tags?: string[];
  folder_id?: UUID | null;
  created_at: string;
  updated_at: string;
}
```

## 17.2 TransitionConfig

```ts
interface TransitionConfig {
  id: UUID;
  type: "fade" | "wipe_left" | "wipe_right" |
        "wipe_up" | "wipe_down" | "zoom_in" | "zoom_out";
  duration_seconds: number;
  easing?: string;
}
```

## 17.3 Clip

```ts
interface Clip {
  id: UUID;
  media_asset_id: UUID;
  track_id: UUID;

  start_frame: number;
  end_frame: number;
  trim_in_frame: number;
  trim_out_frame: number;

  label?: string;
  speed?: number;
  volume?: number;
  mute?: boolean;

  opacity?: number;
  scale?: number;
  position_x?: number;
  position_y?: number;

  text_content?: string;

  transition_in_id?: UUID | null;
  transition_out_id?: UUID | null;
}
```

## 17.4 Track

```ts
interface Track {
  id: UUID;
  type: "video" | "audio" | "text";
  label: string;
  muted: boolean;
  locked: boolean;
  order_index: number;
}
```

## 17.5 Composition

```ts
interface Composition {
  id: UUID;
  project_id: UUID;
  name: string;
  aspect_ratio: "16:9" | "9:16" | "1:1";
  timebase_fps: 24 | 30 | 60;

  tracks: Track[];
  clips: Clip[];
  transitions: TransitionConfig[];

  created_at: string;
  updated_at: string;
}
```

## 17.6 Project

```ts
interface Project {
  id: UUID;
  owner_user_id: UUID;
  name: string;
  thumbnail_url?: string;
  last_modified_at: string;
  composition: Composition;
}
```

---

# 18. Backend API Gaps & Required Additions

The backend must add:

- `POST /api/v1/media/upload`  
- `GET /api/v1/media`  
- `PATCH /api/v1/media/{id}`  
- `DELETE /api/v1/media/{id}`  
- Folder endpoints  
- Project save/load endpoints  
- WebSocket `/ws/v1/connect`  

Schemas must grow to support:
- transitions  
- scale  
- x/y position  
- opacity  
- speed  
- volume/mute  

---

# 19. Future Enhancements

- Multi-user real-time collaboration  
- Keyframe animation  
- LUTs, color grading  
- Audio waveform visualization  
- Chroma key  
- Plugin system  

---

# Change Log
| Version | Date | Changes |
|---------|------|---------|
| 2.1 | Current | Added timebase, zoom, mobile layout, thumbnail LRU, dirty state, schemas, playback engine, splitting, env vars, AI concurrency, error taxonomy |
