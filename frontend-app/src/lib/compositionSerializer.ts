// Composition Data Serialization for Backend API
import type { Clip, Track, Transition } from '@/types/stores'
import type { ExportSettings } from '@/types/export'

// Backend API types
export interface CompositionPayload {
  name: string
  settings: ExportSettingsPayload
  timeline: TimelinePayload
}

export interface ExportSettingsPayload {
  aspectRatio: string
  width: number
  height: number
  format: string
  codec?: string
  quality: number // CRF value
  frameRate: number
  duration: number // in seconds
}

export interface TimelinePayload {
  fps: number
  duration: number // in frames
  tracks: TrackPayload[]
}

export interface TrackPayload {
  id: string
  type: 'video' | 'audio' | 'text'
  name: string
  order: number
  clips: ClipPayload[]
}

export interface ClipPayload {
  id: string
  assetId: string
  assetUrl: string // S3 URL
  startTime: number // in seconds
  duration: number // in seconds
  inPoint: number // trim start in seconds
  outPoint: number // trim end in seconds
  layer: number
  // Transform properties
  transforms: {
    opacity: number
    scale: { x: number; y: number }
    position: { x: number; y: number }
    rotation: number
  }
  // Transitions
  transitionIn?: TransitionPayload
  transitionOut?: TransitionPayload
}

export interface TransitionPayload {
  type: string
  duration: number // in seconds
}

/**
 * Serializes the timeline state and export settings into the backend API format
 */
export function serializeComposition(
  clips: Map<string, Clip>,
  tracks: Track[],
  assetUrlMap: Map<string, string>, // Maps assetId to S3 URL
  exportSettings: ExportSettings,
  timelineDuration: number, // in frames
  fps: number
): CompositionPayload {
  // Calculate output dimensions based on export settings
  const { width, height } = calculateDimensions(
    exportSettings.aspectRatio,
    exportSettings.resolution
  )

  // Build settings payload
  const settingsPayload: ExportSettingsPayload = {
    aspectRatio: exportSettings.aspectRatio,
    width,
    height,
    format: exportSettings.format,
    codec: getCodecForFormat(exportSettings.format),
    quality: exportSettings.quality,
    frameRate: exportSettings.frameRate,
    duration: framesToSeconds(timelineDuration, fps),
  }

  // Build timeline payload
  const timelinePayload: TimelinePayload = {
    fps: exportSettings.frameRate, // Use export fps, not timeline fps
    duration: timelineDuration,
    tracks: serializeTracks(clips, tracks, assetUrlMap, fps),
  }

  return {
    name: exportSettings.name,
    settings: settingsPayload,
    timeline: timelinePayload,
  }
}

/**
 * Serializes tracks and their clips
 */
function serializeTracks(
  clips: Map<string, Clip>,
  tracks: Track[],
  assetUrlMap: Map<string, string>,
  fps: number
): TrackPayload[] {
  return tracks
    .filter((track) => !track.hidden) // Skip hidden tracks
    .sort((a, b) => a.order - b.order) // Sort by order
    .map((track) => {
      // Get clips for this track
      const trackClips = Array.from(clips.values())
        .filter((clip) => clip.trackId === track.id)
        .sort((a, b) => a.startTime - b.startTime) // Sort by start time

      return {
        id: track.id,
        type: track.type,
        name: track.name,
        order: track.order,
        clips: trackClips.map((clip) =>
          serializeClip(clip, assetUrlMap, fps, track.muted)
        ),
      }
    })
}

/**
 * Serializes a single clip
 */
function serializeClip(
  clip: Clip,
  assetUrlMap: Map<string, string>,
  fps: number,
  trackMuted: boolean
): ClipPayload {
  const assetUrl = assetUrlMap.get(clip.assetId)
  if (!assetUrl) {
    throw new Error(`Asset URL not found for assetId: ${clip.assetId}`)
  }

  return {
    id: clip.id,
    assetId: clip.assetId,
    assetUrl,
    startTime: framesToSeconds(clip.startTime, fps),
    duration: framesToSeconds(clip.duration, fps),
    inPoint: framesToSeconds(clip.inPoint, fps),
    outPoint: framesToSeconds(clip.outPoint, fps),
    layer: clip.layer,
    transforms: {
      opacity: trackMuted ? 0 : clip.opacity, // Respect track mute
      scale: clip.scale,
      position: clip.position,
      rotation: clip.rotation,
    },
    transitionIn: clip.transitionIn
      ? serializeTransition(clip.transitionIn, fps)
      : undefined,
    transitionOut: clip.transitionOut
      ? serializeTransition(clip.transitionOut, fps)
      : undefined,
  }
}

/**
 * Serializes a transition
 */
function serializeTransition(transition: Transition, fps: number): TransitionPayload {
  return {
    type: transition.type,
    duration: framesToSeconds(transition.duration, fps),
  }
}

/**
 * Converts frames to seconds
 */
function framesToSeconds(frames: number, fps: number): number {
  return parseFloat((frames / fps).toFixed(3))
}

/**
 * Calculate output dimensions based on aspect ratio and resolution
 */
function calculateDimensions(
  aspectRatio: string,
  resolution: string
): { width: number; height: number } {
  // Resolution height mappings
  const resolutionHeights: Record<string, number> = {
    '480p': 480,
    '720p': 720,
    '1080p': 1080,
    '4k': 2160,
  }

  const height = resolutionHeights[resolution]
  if (!height) {
    throw new Error(`Unknown resolution: ${resolution}`)
  }

  // Calculate width based on aspect ratio
  const aspectRatios: Record<string, number> = {
    '16:9': 16 / 9,
    '9:16': 9 / 16,
    '1:1': 1,
    '4:3': 4 / 3,
  }

  const ratio = aspectRatios[aspectRatio]
  if (!ratio) {
    throw new Error(`Unknown aspect ratio: ${aspectRatio}`)
  }

  // For portrait orientations, swap width/height logic
  if (aspectRatio === '9:16') {
    return {
      width: height,
      height: Math.round(height / (9 / 16)),
    }
  }

  return {
    width: Math.round(height * ratio),
    height,
  }
}

/**
 * Get codec for export format
 */
function getCodecForFormat(format: string): string {
  const codecMap: Record<string, string> = {
    mp4: 'h264',
    webm: 'vp9',
  }
  return codecMap[format] || 'h264'
}

/**
 * Validates composition data before serialization
 */
export function validateCompositionData(
  clips: Map<string, Clip>,
  tracks: Track[],
  assetUrlMap: Map<string, string>
): { valid: boolean; errors: string[] } {
  const errors: string[] = []

  // Check if there are any clips
  if (clips.size === 0) {
    errors.push('Timeline is empty. Add at least one clip to export.')
  }

  // Check if there are any tracks
  if (tracks.length === 0) {
    errors.push('No tracks found. Add at least one track to export.')
  }

  // Validate all clips have valid asset URLs
  for (const clip of clips.values()) {
    if (!assetUrlMap.has(clip.assetId)) {
      errors.push(`Missing asset URL for clip ${clip.id} (assetId: ${clip.assetId})`)
    }
  }

  // Check for overlapping clips on the same track (optional validation)
  const trackClipMap = new Map<string, Clip[]>()
  for (const clip of clips.values()) {
    if (!trackClipMap.has(clip.trackId)) {
      trackClipMap.set(clip.trackId, [])
    }
    trackClipMap.get(clip.trackId)!.push(clip)
  }

  // Check each track for overlaps
  for (const [trackId, trackClips] of trackClipMap) {
    const sortedClips = trackClips.sort((a, b) => a.startTime - b.startTime)
    for (let i = 0; i < sortedClips.length - 1; i++) {
      const current = sortedClips[i]
      const next = sortedClips[i + 1]
      const currentEnd = current.startTime + current.duration

      if (currentEnd > next.startTime) {
        errors.push(
          `Overlapping clips detected on track ${trackId}: clip ${current.id} and ${next.id}`
        )
      }
    }
  }

  return {
    valid: errors.length === 0,
    errors,
  }
}
