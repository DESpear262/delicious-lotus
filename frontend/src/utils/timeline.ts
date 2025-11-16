/**
 * Timeline Utility Functions
 * Calculations and helpers for timeline editor
 */

import type { ClipInfo } from '@/api/types';

export interface TimelineClip {
  id: string;
  clipId: string;
  url: string;
  thumbnailUrl?: string;
  startTime: number;
  endTime: number;
  duration: number;
  originalDuration: number;
  transitionIn?: TransitionType;
  transitionOut?: TransitionType;
  order: number;
}

export type TransitionType = 'cut' | 'fade' | 'dissolve' | 'wipe';

export const TRANSITION_DURATIONS: Record<TransitionType, number> = {
  cut: 0,
  fade: 0.5,
  dissolve: 0.75,
  wipe: 0.5,
};

/**
 * Convert ClipInfo from API to TimelineClip
 */
export function clipInfoToTimelineClip(
  clip: ClipInfo,
  order: number,
  previousClipEndTime: number = 0
): TimelineClip {
  return {
    id: `timeline-clip-${clip.clip_id}-${order}`,
    clipId: clip.clip_id,
    url: clip.url || '',
    thumbnailUrl: clip.thumbnail_url,
    startTime: previousClipEndTime,
    endTime: previousClipEndTime + clip.duration,
    duration: clip.duration,
    originalDuration: clip.duration,
    transitionIn: order === 0 ? undefined : 'cut',
    transitionOut: 'cut',
    order,
  };
}

/**
 * Calculate total timeline duration
 */
export function calculateTotalDuration(clips: TimelineClip[]): number {
  if (clips.length === 0) return 0;

  const lastClip = clips.reduce((max, clip) =>
    clip.endTime > max.endTime ? clip : max
  , clips[0]);

  return lastClip.endTime;
}

/**
 * Recalculate timeline positions after reordering
 */
export function recalculateTimelinePositions(clips: TimelineClip[]): TimelineClip[] {
  let currentTime = 0;

  return clips.map((clip, index) => {
    const startTime = currentTime;
    const endTime = startTime + clip.duration;
    currentTime = endTime;

    return {
      ...clip,
      order: index,
      startTime,
      endTime,
    };
  });
}

/**
 * Trim clip duration
 */
export function trimClip(
  clip: TimelineClip,
  newDuration: number,
  allClips: TimelineClip[]
): TimelineClip[] {
  // Ensure duration is within bounds
  const clampedDuration = Math.max(0.1, Math.min(newDuration, clip.originalDuration));

  // Update the clip
  const updatedClip = {
    ...clip,
    duration: clampedDuration,
    endTime: clip.startTime + clampedDuration,
  };

  // Replace the clip and recalculate positions
  const updatedClips = allClips.map(c => c.id === clip.id ? updatedClip : c);
  return recalculateTimelinePositions(updatedClips);
}

/**
 * Reorder clips by drag and drop
 */
export function reorderClips(
  clips: TimelineClip[],
  fromIndex: number,
  toIndex: number
): TimelineClip[] {
  const result = Array.from(clips);
  const [removed] = result.splice(fromIndex, 1);
  result.splice(toIndex, 0, removed);

  return recalculateTimelinePositions(result);
}

/**
 * Delete a clip from timeline
 */
export function deleteClip(clips: TimelineClip[], clipId: string): TimelineClip[] {
  const filtered = clips.filter(c => c.id !== clipId);
  return recalculateTimelinePositions(filtered);
}

/**
 * Set transition for a clip
 */
export function setTransition(
  clips: TimelineClip[],
  clipId: string,
  position: 'in' | 'out',
  transition: TransitionType
): TimelineClip[] {
  return clips.map(clip => {
    if (clip.id === clipId) {
      if (position === 'in') {
        return { ...clip, transitionIn: transition };
      } else {
        return { ...clip, transitionOut: transition };
      }
    }
    return clip;
  });
}

/**
 * Get clip at specific time position
 */
export function getClipAtTime(clips: TimelineClip[], time: number): TimelineClip | null {
  return clips.find(clip => time >= clip.startTime && time < clip.endTime) || null;
}

/**
 * Convert timeline clips to API ClipConfig format
 */
export function timelineClipsToClipConfig(clips: TimelineClip[]) {
  return clips.map(clip => ({
    clip_id: clip.clipId,
    url: clip.url,
    start_time: 0, // Start from beginning of source clip
    end_time: clip.duration, // Use trimmed duration
    transition_in: clip.transitionIn,
    transition_out: clip.transitionOut,
  }));
}

/**
 * Format time in seconds to MM:SS format
 */
export function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Format time with milliseconds MM:SS.mmm
 */
export function formatTimeDetailed(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 1000);
  return `${mins}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
}

/**
 * Convert pixel position to time based on zoom level
 */
export function pixelToTime(pixel: number, pixelsPerSecond: number): number {
  return pixel / pixelsPerSecond;
}

/**
 * Convert time to pixel position based on zoom level
 */
export function timeToPixel(time: number, pixelsPerSecond: number): number {
  return time * pixelsPerSecond;
}

/**
 * Validate timeline - check for gaps, overlaps, etc.
 */
export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export function validateTimeline(clips: TimelineClip[]): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (clips.length === 0) {
    errors.push('Timeline must contain at least one clip');
  }

  // Check for gaps or overlaps
  for (let i = 1; i < clips.length; i++) {
    const prevClip = clips[i - 1];
    const currentClip = clips[i];

    const gap = currentClip.startTime - prevClip.endTime;

    if (gap > 0.01) {
      warnings.push(`Gap of ${gap.toFixed(2)}s between clip ${i} and ${i + 1}`);
    } else if (gap < -0.01) {
      errors.push(`Overlap of ${Math.abs(gap).toFixed(2)}s between clip ${i} and ${i + 1}`);
    }
  }

  // Check clip durations
  clips.forEach((clip, index) => {
    if (clip.duration <= 0) {
      errors.push(`Clip ${index + 1} has invalid duration: ${clip.duration}`);
    }
    if (clip.duration > clip.originalDuration) {
      errors.push(`Clip ${index + 1} duration exceeds original: ${clip.duration} > ${clip.originalDuration}`);
    }
  });

  return {
    valid: errors.length === 0,
    errors,
    warnings,
  };
}

/**
 * Calculate zoom levels for timeline
 */
export const ZOOM_LEVELS = [
  { label: '25%', pixelsPerSecond: 10 },
  { label: '50%', pixelsPerSecond: 20 },
  { label: '75%', pixelsPerSecond: 30 },
  { label: '100%', pixelsPerSecond: 40 },
  { label: '150%', pixelsPerSecond: 60 },
  { label: '200%', pixelsPerSecond: 80 },
  { label: '300%', pixelsPerSecond: 120 },
  { label: '400%', pixelsPerSecond: 160 },
];

export const DEFAULT_ZOOM_LEVEL = 3; // 100%
