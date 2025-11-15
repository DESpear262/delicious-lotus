# PR-F008: Video Preview Component Implementation Plan

## Overview
Build a custom HTML5 video player with controls, fullscreen support, download functionality, and preview features for generated videos.

**Estimated Time:** 3 hours  
**Dependencies:** PR-F002 ✅  
**Priority:** HIGH - Blocks PR-F010 (Preview Page), PR-F013 (Timeline Editor)

## Goals
- Create a polished video player with custom controls
- Support fullscreen, playback speed, and volume control
- Implement download functionality with progress tracking
- Ensure keyboard accessibility and responsive design
- Provide smooth loading states and error handling

---

## Files to Create

### 1. `/home/user/delicious-lotus/frontend/src/components/VideoPlayer/VideoPlayer.tsx`
**Purpose:** Main video player component

**Component Interface:**
```typescript
export interface VideoPlayerProps {
  src: string;                    // Video URL
  poster?: string;                // Thumbnail/poster image
  title?: string;                 // Video title
  autoPlay?: boolean;             // Auto-play on mount
  muted?: boolean;                // Start muted
  loop?: boolean;                 // Loop playback
  className?: string;
  onEnded?: () => void;          // Callback when video ends
  onError?: (error: Error) => void;
  showDownload?: boolean;         // Show download button
  downloadFileName?: string;      // Custom download filename
}

export function VideoPlayer({
  src,
  poster,
  title,
  autoPlay = false,
  muted = false,
  loop = false,
  className,
  onEnded,
  onError,
  showDownload = true,
  downloadFileName
}: VideoPlayerProps): JSX.Element {
  // Video element ref
  const videoRef = useRef<HTMLVideoElement>(null);
  
  // Player state from custom hook
  const {
    isPlaying,
    currentTime,
    duration,
    volume,
    isMuted,
    isFullscreen,
    playbackRate,
    buffered,
    isLoading,
    error,
    play,
    pause,
    seek,
    setVolume,
    toggleMute,
    toggleFullscreen,
    setPlaybackRate,
  } = useVideoPlayer(videoRef);
  
  return (
    <div className={`video-player ${className}`}>
      {/* Video element */}
      <video
        ref={videoRef}
        src={src}
        poster={poster}
        className="video-player__video"
        onEnded={onEnded}
        onError={handleError}
        autoPlay={autoPlay}
        muted={muted}
        loop={loop}
        preload="metadata"
      />
      
      {/* Loading overlay */}
      {isLoading && (
        <div className="video-player__loading">
          <Spinner size="large" />
        </div>
      )}
      
      {/* Error overlay */}
      {error && (
        <div className="video-player__error">
          <p>Failed to load video</p>
          <Button onClick={() => videoRef.current?.load()}>
            Retry
          </Button>
        </div>
      )}
      
      {/* Custom controls */}
      <VideoControls
        isPlaying={isPlaying}
        currentTime={currentTime}
        duration={duration}
        volume={volume}
        isMuted={isMuted}
        isFullscreen={isFullscreen}
        playbackRate={playbackRate}
        buffered={buffered}
        onPlayPause={() => isPlaying ? pause() : play()}
        onSeek={seek}
        onVolumeChange={setVolume}
        onToggleMute={toggleMute}
        onToggleFullscreen={toggleFullscreen}
        onPlaybackRateChange={setPlaybackRate}
        showDownload={showDownload}
        onDownload={() => handleDownload(src, downloadFileName)}
      />
    </div>
  );
}
```

**Features:**
- Native HTML5 `<video>` element
- Custom controls (hide native controls)
- Thumbnail poster image while loading
- Loading spinner overlay
- Error state with retry
- Fullscreen support
- Download button integration

**Styling:**
```css
.video-player {
  position: relative;
  width: 100%;
  background: #000;
  border-radius: var(--radius-md);
  overflow: hidden;
}

.video-player__video {
  width: 100%;
  height: auto;
  display: block;
}

.video-player__loading,
.video-player__error {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.7);
  z-index: 10;
}

/* Hide native controls */
.video-player__video::-webkit-media-controls {
  display: none !important;
}
```

---

### 2. `/home/user/delicious-lotus/frontend/src/components/VideoPlayer/VideoControls.tsx`
**Purpose:** Custom video controls overlay

**Component Interface:**
```typescript
interface VideoControlsProps {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  isMuted: boolean;
  isFullscreen: boolean;
  playbackRate: number;
  buffered: TimeRanges | null;
  onPlayPause: () => void;
  onSeek: (time: number) => void;
  onVolumeChange: (volume: number) => void;
  onToggleMute: () => void;
  onToggleFullscreen: () => void;
  onPlaybackRateChange: (rate: number) => void;
  showDownload?: boolean;
  onDownload?: () => void;
}

export function VideoControls({
  isPlaying,
  currentTime,
  duration,
  volume,
  isMuted,
  isFullscreen,
  playbackRate,
  buffered,
  onPlayPause,
  onSeek,
  onVolumeChange,
  onToggleMute,
  onToggleFullscreen,
  onPlaybackRateChange,
  showDownload,
  onDownload,
}: VideoControlsProps): JSX.Element {
  const [showControls, setShowControls] = useState(true);
  const [showVolumeSlider, setShowVolumeSlider] = useState(false);
  const [showPlaybackMenu, setShowPlaybackMenu] = useState(false);
  const hideControlsTimer = useRef<NodeJS.Timeout>();
  
  // Auto-hide controls after 3 seconds of inactivity
  const handleMouseMove = () => {
    setShowControls(true);
    clearTimeout(hideControlsTimer.current);
    hideControlsTimer.current = setTimeout(() => {
      if (isPlaying) setShowControls(false);
    }, 3000);
  };
  
  return (
    <div
      className={`video-controls ${showControls ? 'video-controls--visible' : ''}`}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => isPlaying && setShowControls(false)}
    >
      {/* Timeline scrubber */}
      <Timeline
        currentTime={currentTime}
        duration={duration}
        buffered={buffered}
        onSeek={onSeek}
      />
      
      {/* Control buttons */}
      <div className="video-controls__bar">
        <div className="video-controls__left">
          {/* Play/Pause */}
          <button
            className="video-controls__button"
            onClick={onPlayPause}
            aria-label={isPlaying ? 'Pause' : 'Play'}
            title={isPlaying ? 'Pause (Space)' : 'Play (Space)'}
          >
            {isPlaying ? <PauseIcon /> : <PlayIcon />}
          </button>
          
          {/* Volume control */}
          <div className="video-controls__volume">
            <button
              className="video-controls__button"
              onClick={onToggleMute}
              onMouseEnter={() => setShowVolumeSlider(true)}
              aria-label={isMuted ? 'Unmute' : 'Mute'}
              title={isMuted ? 'Unmute (M)' : 'Mute (M)'}
            >
              {isMuted ? <VolumeOffIcon /> : <VolumeOnIcon />}
            </button>
            
            {showVolumeSlider && (
              <div
                className="video-controls__volume-slider"
                onMouseLeave={() => setShowVolumeSlider(false)}
              >
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={isMuted ? 0 : volume}
                  onChange={(e) => onVolumeChange(parseFloat(e.target.value))}
                  aria-label="Volume"
                />
              </div>
            )}
          </div>
          
          {/* Time display */}
          <span className="video-controls__time">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>
        </div>
        
        <div className="video-controls__right">
          {/* Playback speed */}
          <div className="video-controls__speed">
            <button
              className="video-controls__button"
              onClick={() => setShowPlaybackMenu(!showPlaybackMenu)}
              aria-label="Playback speed"
              title="Playback speed"
            >
              {playbackRate}x
            </button>
            
            {showPlaybackMenu && (
              <div className="video-controls__speed-menu">
                {[0.5, 0.75, 1, 1.25, 1.5, 2].map(rate => (
                  <button
                    key={rate}
                    className={`video-controls__speed-option ${
                      rate === playbackRate ? 'video-controls__speed-option--active' : ''
                    }`}
                    onClick={() => {
                      onPlaybackRateChange(rate);
                      setShowPlaybackMenu(false);
                    }}
                  >
                    {rate}x
                  </button>
                ))}
              </div>
            )}
          </div>
          
          {/* Download button */}
          {showDownload && onDownload && (
            <button
              className="video-controls__button"
              onClick={onDownload}
              aria-label="Download video"
              title="Download video"
            >
              <DownloadIcon />
            </button>
          )}
          
          {/* Fullscreen */}
          <button
            className="video-controls__button"
            onClick={onToggleFullscreen}
            aria-label={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
            title={isFullscreen ? 'Exit fullscreen (F)' : 'Fullscreen (F)'}
          >
            {isFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
          </button>
        </div>
      </div>
    </div>
  );
}
```

**Features:**
- Play/Pause button with icon toggle
- Volume slider (vertical, on hover)
- Mute button
- Time display (current / total)
- Playback speed selector (0.5x, 0.75x, 1x, 1.25x, 1.5x, 2x)
- Download button
- Fullscreen button
- Auto-hide after 3 seconds (during playback)
- Show on mouse move

---

### 3. `/home/user/delicious-lotus/frontend/src/components/VideoPlayer/Timeline.tsx`
**Purpose:** Scrubber timeline with progress and buffering indicators

**Component Interface:**
```typescript
interface TimelineProps {
  currentTime: number;
  duration: number;
  buffered: TimeRanges | null;
  onSeek: (time: number) => void;
}

export function Timeline({
  currentTime,
  duration,
  buffered,
  onSeek,
}: TimelineProps): JSX.Element {
  const [isDragging, setIsDragging] = useState(false);
  const [hoverTime, setHoverTime] = useState<number | null>(null);
  const timelineRef = useRef<HTMLDivElement>(null);
  
  const getTimeFromPosition = (clientX: number): number => {
    if (!timelineRef.current) return 0;
    const rect = timelineRef.current.getBoundingClientRect();
    const position = (clientX - rect.left) / rect.width;
    return Math.max(0, Math.min(duration, position * duration));
  };
  
  const handleClick = (e: React.MouseEvent) => {
    const time = getTimeFromPosition(e.clientX);
    onSeek(time);
  };
  
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    const time = getTimeFromPosition(e.clientX);
    onSeek(time);
  };
  
  const handleMouseMove = (e: React.MouseEvent) => {
    const time = getTimeFromPosition(e.clientX);
    setHoverTime(time);
    
    if (isDragging) {
      onSeek(time);
    }
  };
  
  const handleMouseUp = () => {
    setIsDragging(false);
  };
  
  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mouseup', handleMouseUp);
      return () => window.removeEventListener('mouseup', handleMouseUp);
    }
  }, [isDragging]);
  
  // Calculate buffered percentage
  const bufferedPercentage = useMemo(() => {
    if (!buffered || !duration) return 0;
    const bufferedEnd = buffered.length > 0 ? buffered.end(buffered.length - 1) : 0;
    return (bufferedEnd / duration) * 100;
  }, [buffered, duration]);
  
  const progressPercentage = (currentTime / duration) * 100 || 0;
  
  return (
    <div
      ref={timelineRef}
      className="timeline"
      onClick={handleClick}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setHoverTime(null)}
      role="slider"
      aria-label="Seek"
      aria-valuemin={0}
      aria-valuemax={duration}
      aria-valuenow={currentTime}
      tabIndex={0}
    >
      {/* Buffered indicator */}
      <div
        className="timeline__buffered"
        style={{ width: `${bufferedPercentage}%` }}
      />
      
      {/* Progress indicator */}
      <div
        className="timeline__progress"
        style={{ width: `${progressPercentage}%` }}
      />
      
      {/* Scrubber handle */}
      <div
        className="timeline__handle"
        style={{ left: `${progressPercentage}%` }}
      />
      
      {/* Hover time preview */}
      {hoverTime !== null && (
        <div
          className="timeline__preview"
          style={{ left: `${(hoverTime / duration) * 100}%` }}
        >
          {formatTime(hoverTime)}
        </div>
      )}
    </div>
  );
}
```

**Features:**
- Click to seek
- Drag scrubber to seek
- Hover to preview time
- Buffered progress indicator (lighter)
- Playback progress indicator (primary color)
- Scrubber handle
- Keyboard accessible (arrow keys)
- Smooth animations

**Styling:**
```css
.timeline {
  position: relative;
  height: 6px;
  background: rgba(255, 255, 255, 0.2);
  cursor: pointer;
  border-radius: 3px;
  margin-bottom: var(--spacing-sm);
}

.timeline:hover {
  height: 8px;
}

.timeline__buffered {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: rgba(255, 255, 255, 0.4);
  border-radius: 3px;
  transition: width 0.2s;
}

.timeline__progress {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: var(--color-primary);
  border-radius: 3px;
  transition: width 0.1s linear;
}

.timeline__handle {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 14px;
  height: 14px;
  background: var(--color-primary);
  border-radius: 50%;
  opacity: 0;
  transition: opacity 0.2s;
}

.timeline:hover .timeline__handle {
  opacity: 1;
}

.timeline__preview {
  position: absolute;
  bottom: 100%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-bottom: 8px;
  pointer-events: none;
}
```

---

### 4. `/home/user/delicious-lotus/frontend/src/hooks/useVideoPlayer.ts`
**Purpose:** Video player state management hook

**Hook Interface:**
```typescript
export interface UseVideoPlayerReturn {
  // Playback state
  isPlaying: boolean;
  isPaused: boolean;
  currentTime: number;
  duration: number;
  buffered: TimeRanges | null;
  
  // Audio state
  volume: number;
  isMuted: boolean;
  
  // Display state
  isFullscreen: boolean;
  playbackRate: number;
  
  // Loading state
  isLoading: boolean;
  canPlay: boolean;
  error: Error | null;
  
  // Actions
  play: () => Promise<void>;
  pause: () => void;
  seek: (time: number) => void;
  setVolume: (volume: number) => void;
  toggleMute: () => void;
  toggleFullscreen: () => void;
  setPlaybackRate: (rate: number) => void;
}

export function useVideoPlayer(
  videoRef: RefObject<HTMLVideoElement>
): UseVideoPlayerReturn {
  // Playback state
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [buffered, setBuffered] = useState<TimeRanges | null>(null);
  
  // Audio state
  const [volume, setVolumeState] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  
  // Display state
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [playbackRate, setPlaybackRateState] = useState(1);
  
  // Loading state
  const [isLoading, setIsLoading] = useState(true);
  const [canPlay, setCanPlay] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!videoRef.current) return;
      
      switch (e.key) {
        case ' ':
        case 'k':
          e.preventDefault();
          isPlaying ? pause() : play();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          seek(Math.max(0, currentTime - 5));
          break;
        case 'ArrowRight':
          e.preventDefault();
          seek(Math.min(duration, currentTime + 5));
          break;
        case 'f':
          e.preventDefault();
          toggleFullscreen();
          break;
        case 'm':
          e.preventDefault();
          toggleMute();
          break;
        case 'ArrowUp':
          e.preventDefault();
          setVolume(Math.min(1, volume + 0.1));
          break;
        case 'ArrowDown':
          e.preventDefault();
          setVolume(Math.max(0, volume - 0.1));
          break;
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isPlaying, currentTime, duration, volume]);
  
  // Event listeners
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    
    const handleTimeUpdate = () => setCurrentTime(video.currentTime);
    const handleDurationChange = () => setDuration(video.duration);
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleProgress = () => setBuffered(video.buffered);
    const handleLoadStart = () => setIsLoading(true);
    const handleCanPlay = () => {
      setIsLoading(false);
      setCanPlay(true);
    };
    const handleError = () => {
      setError(new Error('Failed to load video'));
      setIsLoading(false);
    };
    
    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('durationchange', handleDurationChange);
    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);
    video.addEventListener('progress', handleProgress);
    video.addEventListener('loadstart', handleLoadStart);
    video.addEventListener('canplay', handleCanPlay);
    video.addEventListener('error', handleError);
    
    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('durationchange', handleDurationChange);
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
      video.removeEventListener('progress', handleProgress);
      video.removeEventListener('loadstart', handleLoadStart);
      video.removeEventListener('canplay', handleCanPlay);
      video.removeEventListener('error', handleError);
    };
  }, [videoRef]);
  
  // Fullscreen change listener
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);
  
  // Actions
  const play = async () => {
    try {
      await videoRef.current?.play();
    } catch (err) {
      setError(err as Error);
    }
  };
  
  const pause = () => {
    videoRef.current?.pause();
  };
  
  const seek = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
    }
  };
  
  const setVolume = (vol: number) => {
    const clampedVolume = Math.max(0, Math.min(1, vol));
    setVolumeState(clampedVolume);
    if (videoRef.current) {
      videoRef.current.volume = clampedVolume;
      if (clampedVolume > 0) {
        setIsMuted(false);
        videoRef.current.muted = false;
      }
    }
  };
  
  const toggleMute = () => {
    if (videoRef.current) {
      const newMuted = !isMuted;
      videoRef.current.muted = newMuted;
      setIsMuted(newMuted);
    }
  };
  
  const toggleFullscreen = async () => {
    if (!videoRef.current) return;
    
    try {
      if (!document.fullscreenElement) {
        await videoRef.current.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    } catch (err) {
      console.error('Fullscreen error:', err);
    }
  };
  
  const setPlaybackRate = (rate: number) => {
    if (videoRef.current) {
      videoRef.current.playbackRate = rate;
      setPlaybackRateState(rate);
    }
  };
  
  return {
    isPlaying,
    isPaused: !isPlaying,
    currentTime,
    duration,
    buffered,
    volume,
    isMuted,
    isFullscreen,
    playbackRate,
    isLoading,
    canPlay,
    error,
    play,
    pause,
    seek,
    setVolume,
    toggleMute,
    toggleFullscreen,
    setPlaybackRate,
  };
}
```

**Features:**
- Manages all video element state
- Keyboard shortcuts
- Event listener setup/cleanup
- Fullscreen API integration
- Error handling
- Loading states

---

### 5. `/home/user/delicious-lotus/frontend/src/utils/video.ts`
**Purpose:** Video utility functions

**Functions:**
```typescript
/**
 * Format time in seconds to MM:SS or HH:MM:SS
 */
export function formatTime(seconds: number): string {
  if (!isFinite(seconds)) return '0:00';
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
  
  return `${minutes}:${String(secs).padStart(2, '0')}`;
}

/**
 * Format file size in bytes to human-readable string
 */
export function formatFileSize(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`;
}

/**
 * Download video file
 */
export async function downloadVideo(
  url: string,
  filename?: string,
  onProgress?: (progress: number) => void
): Promise<void> {
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error('Download failed');
    
    const contentLength = response.headers.get('content-length');
    const total = contentLength ? parseInt(contentLength, 10) : 0;
    
    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');
    
    const chunks: Uint8Array[] = [];
    let received = 0;
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      chunks.push(value);
      received += value.length;
      
      if (onProgress && total > 0) {
        onProgress((received / total) * 100);
      }
    }
    
    const blob = new Blob(chunks, { type: 'video/mp4' });
    const blobUrl = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = filename || 'video.mp4';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(blobUrl);
    
  } catch (error) {
    console.error('Download error:', error);
    throw error;
  }
}

/**
 * Generate video thumbnail from video element
 */
export function generateThumbnail(
  videoElement: HTMLVideoElement,
  time: number = 0
): Promise<string> {
  return new Promise((resolve, reject) => {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    
    if (!context) {
      reject(new Error('Canvas context not available'));
      return;
    }
    
    const seekHandler = () => {
      canvas.width = videoElement.videoWidth;
      canvas.height = videoElement.videoHeight;
      context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
      
      const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
      resolve(dataUrl);
      
      videoElement.removeEventListener('seeked', seekHandler);
    };
    
    videoElement.addEventListener('seeked', seekHandler);
    videoElement.currentTime = time;
  });
}

/**
 * Check if video can play
 */
export function canPlayType(mimeType: string): boolean {
  const video = document.createElement('video');
  return video.canPlayType(mimeType) !== '';
}

/**
 * Get video metadata
 */
export async function getVideoMetadata(url: string): Promise<{
  duration: number;
  width: number;
  height: number;
}> {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video');
    
    video.onloadedmetadata = () => {
      resolve({
        duration: video.duration,
        width: video.videoWidth,
        height: video.videoHeight,
      });
    };
    
    video.onerror = () => {
      reject(new Error('Failed to load video metadata'));
    };
    
    video.src = url;
  });
}
```

---

## Files to Modify

None - all new files.

---

## Dependencies

### NPM Packages
None - using native HTML5 video APIs

### Internal Dependencies
- `/frontend/src/components/ui/Button.tsx` - Design system button
- `/frontend/src/components/ui/Spinner.tsx` - Design system spinner
- `/frontend/src/styles/variables.css` - CSS variables

### Icons
Create or import icons for:
- Play (▶)
- Pause (⏸)
- Volume On (🔊)
- Volume Off (🔇)
- Fullscreen (⛶)
- Fullscreen Exit (⤓)
- Download (⬇)

---

## API Integration

No direct API integration in this PR. The VideoPlayer component will be used in:
- PR-F010: Video Preview & Download Page
- PR-F013: Timeline Editor Component

Video URLs will come from:
- `GET /api/v1/generations/{id}/assets` - Clip URLs
- `GET /api/v1/compositions/{id}/download` - Final video URL

---

## Implementation Details

### Step 1: Create Utilities (20 minutes)
1. Create `utils/video.ts`
2. Implement formatTime()
3. Implement formatFileSize()
4. Implement downloadVideo()
5. Implement generateThumbnail()
6. Add tests for utilities

### Step 2: Build Video Hook (40 minutes)
1. Create `hooks/useVideoPlayer.ts`
2. Set up state management
3. Add event listeners
4. Implement keyboard shortcuts
5. Add fullscreen support
6. Handle loading states
7. Add error handling

### Step 3: Create Timeline Component (30 minutes)
1. Create `components/VideoPlayer/Timeline.tsx`
2. Build progress bar
3. Add buffered indicator
4. Implement scrubber drag
5. Add hover preview
6. Style with animations

### Step 4: Build Controls Component (40 minutes)
1. Create `components/VideoPlayer/VideoControls.tsx`
2. Add play/pause button
3. Add volume control
4. Add time display
5. Add playback speed selector
6. Add download button
7. Add fullscreen button
8. Implement auto-hide logic

### Step 5: Create Main Player Component (30 minutes)
1. Create `components/VideoPlayer/VideoPlayer.tsx`
2. Integrate video element
3. Add loading overlay
4. Add error overlay
5. Wire up controls
6. Test all functionality

### Step 6: Polish and Test (20 minutes)
1. Refine animations
2. Test keyboard shortcuts
3. Test fullscreen
4. Test on mobile
5. Fix any bugs

---

## State Management Approach

### Local Component State
- All state managed in useVideoPlayer hook
- No global state needed
- Props passed down to child components

### State Persistence
- Volume level saved to localStorage
- Playback rate saved to localStorage
- Restore on component mount

---

## Error Handling Strategy

### Video Loading Errors
1. **Network Error:**
   - Show error overlay
   - Display "Failed to load video"
   - Provide retry button

2. **Unsupported Format:**
   - Show error message
   - Suggest alternative browser

3. **Corrupted File:**
   - Show error overlay
   - Provide option to report issue

### Playback Errors
1. **Stalled Playback:**
   - Show buffering indicator
   - Auto-resume when buffer fills

2. **Decoding Error:**
   - Log error
   - Show error message

### Download Errors
1. **Network Failure:**
   - Catch error
   - Show error toast
   - Allow retry

2. **Large File Warning:**
   - Show file size
   - Confirm before download

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space / K | Play/Pause |
| ← | Seek backward 5s |
| → | Seek forward 5s |
| ↑ | Increase volume |
| ↓ | Decrease volume |
| F | Toggle fullscreen |
| M | Toggle mute |
| 0-9 | Seek to percentage (0% - 90%) |

---

## Acceptance Criteria

- [ ] HTML5 video player with custom controls:
  - [ ] Play/Pause toggle
  - [ ] Volume control with slider
  - [ ] Mute button
  - [ ] Seek timeline with scrubber
  - [ ] Current time / Duration display (MM:SS format)
  - [ ] Fullscreen toggle
  - [ ] Playback speed selector (0.5x, 0.75x, 1x, 1.25x, 1.5x, 2x)
- [ ] Video loading states:
  - [ ] Thumbnail preview while loading (poster image)
  - [ ] Loading spinner overlay
  - [ ] Progress bar for buffering
- [ ] Download functionality:
  - [ ] Download button in controls
  - [ ] Download with custom filename
  - [ ] Progress indicator during download
  - [ ] Success confirmation
- [ ] Keyboard shortcuts:
  - [ ] Space - Play/Pause
  - [ ] Arrow Left/Right - Seek backward/forward 5s
  - [ ] Arrow Up/Down - Volume control
  - [ ] F - Fullscreen
  - [ ] M - Mute
- [ ] Responsive design:
  - [ ] Full-width on mobile
  - [ ] Touch-friendly controls
  - [ ] Mobile-optimized scrubber
- [ ] Accessibility:
  - [ ] ARIA labels on all controls
  - [ ] Keyboard navigation
  - [ ] Focus indicators
  - [ ] Screen reader support

---

## Testing Approach

### Unit Tests
1. **formatTime():**
   - Test with 0, 30, 65, 3665 seconds
   - Verify MM:SS and HH:MM:SS formats

2. **useVideoPlayer:**
   - Test play/pause
   - Test seek
   - Test volume control
   - Test keyboard shortcuts

### Component Tests
1. **VideoPlayer:**
   - Renders video element
   - Shows loading state
   - Shows error state
   - Controls respond to interaction

2. **Timeline:**
   - Click to seek
   - Drag to seek
   - Shows buffered progress
   - Shows playback progress

3. **VideoControls:**
   - All buttons render
   - Play/pause toggles icon
   - Volume slider works
   - Playback speed menu works

### Integration Tests
1. **Full Player:**
   - Load video and play
   - Seek to different positions
   - Change volume
   - Toggle fullscreen
   - Download video

### Manual Testing
1. **Video Formats:**
   - Test with MP4 (H.264)
   - Test with WebM (if supported)
   - Test with different resolutions

2. **Browser Testing:**
   - Chrome, Firefox, Safari, Edge
   - Mobile browsers (iOS, Android)

3. **Performance:**
   - Test with long videos (60s)
   - Test with high-resolution (1080p)
   - Monitor memory usage

4. **Accessibility:**
   - Test with keyboard only
   - Test with screen reader
   - Test focus indicators

---

## Responsive Design

### Desktop (≥ 1024px)
- Full controls visible
- Hover interactions
- Large scrubber handle

### Tablet (768px - 1023px)
- Slightly larger controls
- Touch-friendly buttons
- Medium scrubber

### Mobile (< 768px)
- Large touch targets (44x44px)
- Simplified controls
- Tap to play/pause
- Swipe for seek (optional)
- Fullscreen recommended

---

## Performance Considerations

1. **Video Loading:**
   - Use `preload="metadata"` for faster initial load
   - Show poster image immediately
   - Lazy load video on scroll (if needed)

2. **Scrubbing:**
   - Debounce seek operations
   - Use requestAnimationFrame for smooth updates
   - Limit update frequency (60fps max)

3. **Memory:**
   - Clean up event listeners on unmount
   - Revoke blob URLs after download
   - Pause video when not visible

4. **Network:**
   - Use adaptive bitrate if available
   - Show buffering indicator
   - Handle slow connections gracefully

---

## Security Considerations

1. **Video Sources:**
   - Validate video URLs
   - Use HTTPS only
   - Sanitize download filenames

2. **Download:**
   - Verify file type before download
   - Check file size limits
   - Use Content-Security-Policy headers

---

## Styling Details

### Color Scheme
- Background: Black (#000)
- Controls background: Gradient fade (transparent to black)
- Primary color: var(--color-primary)
- Text: White (#fff)

### Animations
- Controls fade in/out: 0.3s
- Scrubber hover: 0.2s
- Button hover: 0.2s
- Drawer slide: 0.3s ease

### Shadows
- Controls: 0 -20px 40px rgba(0,0,0,0.8)
- Buttons: 0 2px 8px rgba(0,0,0,0.2)

---

## Follow-up Tasks

1. **PR-F010:** Use VideoPlayer in Preview Page
2. **PR-F013:** Integrate with Timeline Editor
3. **Enhancement:** Add Picture-in-Picture support
4. **Enhancement:** Add captions/subtitles support
5. **Enhancement:** Add quality selector (if multiple sources)

---

## Success Criteria

This PR is successful when:
1. Video player renders correctly with all controls
2. All keyboard shortcuts work
3. Fullscreen mode works on all browsers
4. Download functionality works
5. Mobile responsive with touch controls
6. Accessibility features work (keyboard, screen reader)
7. No memory leaks in long sessions
8. Smooth performance with 1080p video
9. All acceptance criteria met
10. Code passes TypeScript strict mode
