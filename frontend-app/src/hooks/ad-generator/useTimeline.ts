/**
 * Timeline State Management Hook
 * Manages timeline editor state and operations
 */

import { useState, useCallback, useEffect } from 'react';
import type { ClipInfo } from '@/services/ad-generator/types';
import {
  type TimelineClip,
  type TransitionType,
  clipInfoToTimelineClip,
  calculateTotalDuration,
  reorderClips,
  deleteClip,
  trimClip,
  setTransition,
  validateTimeline,
  DEFAULT_ZOOM_LEVEL,
  ZOOM_LEVELS,
} from '@/utils/ad-generator/timeline';

export interface UseTimelineOptions {
  initialClips?: ClipInfo[];
  autoPlay?: boolean;
  onTimeUpdate?: (time: number) => void;
}

export interface UseTimelineReturn {
  // Timeline state
  clips: TimelineClip[];
  selectedClipId: string | null;
  currentTime: number;
  totalDuration: number;
  isPlaying: boolean;

  // Zoom state
  zoomLevel: number;
  pixelsPerSecond: number;

  // Clip operations
  addClips: (newClips: ClipInfo[]) => void;
  removeClip: (clipId: string) => void;
  reorderClip: (fromIndex: number, toIndex: number) => void;
  trimClipDuration: (clipId: string, newDuration: number) => void;
  selectClip: (clipId: string | null) => void;

  // Transition operations
  setClipTransition: (clipId: string, position: 'in' | 'out', transition: TransitionType) => void;

  // Playback operations
  play: () => void;
  pause: () => void;
  stop: () => void;
  seek: (time: number) => void;

  // Zoom operations
  zoomIn: () => void;
  zoomOut: () => void;
  setZoom: (level: number) => void;

  // Validation
  validate: () => { valid: boolean; errors: string[]; warnings: string[] };

  // Reset
  reset: () => void;
}

/**
 * Custom hook for managing timeline editor state
 */
export function useTimeline(options: UseTimelineOptions = {}): UseTimelineReturn {
  const { initialClips = [], autoPlay = false, onTimeUpdate } = options;

  // Timeline state
  const [clips, setClips] = useState<TimelineClip[]>([]);
  const [selectedClipId, setSelectedClipId] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  // Zoom state
  const [zoomLevel, setZoomLevel] = useState(DEFAULT_ZOOM_LEVEL);
  const pixelsPerSecond = ZOOM_LEVELS[zoomLevel].pixelsPerSecond;

  // Calculate total duration
  const totalDuration = calculateTotalDuration(clips);

  // Initialize clips from ClipInfo array
  useEffect(() => {
    if (initialClips.length > 0 && clips.length === 0) {
      const timelineClips = initialClips.map((clip, index) => {
        const previousEndTime = index === 0
          ? 0
          : timelineClips[index - 1].endTime;
        return clipInfoToTimelineClip(clip, index, previousEndTime);
      });
      setClips(timelineClips);
    }
  }, [initialClips]);

  // Playback interval
  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      setCurrentTime(prev => {
        const next = prev + 0.1; // Update every 100ms
        if (next >= totalDuration) {
          setIsPlaying(false);
          return totalDuration;
        }
        onTimeUpdate?.(next);
        return next;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [isPlaying, totalDuration, onTimeUpdate]);

  // Clip operations
  const addClips = useCallback((newClips: ClipInfo[]) => {
    setClips(currentClips => {
      const startOrder = currentClips.length;
      const lastEndTime = currentClips.length > 0
        ? currentClips[currentClips.length - 1].endTime
        : 0;

      const newTimelineClips = newClips.map((clip, index) => {
        const previousEndTime = index === 0
          ? lastEndTime
          : newTimelineClips[index - 1].endTime;
        return clipInfoToTimelineClip(clip, startOrder + index, previousEndTime);
      });

      return [...currentClips, ...newTimelineClips];
    });
  }, []);

  const removeClip = useCallback((clipId: string) => {
    setClips(currentClips => deleteClip(currentClips, clipId));
    if (selectedClipId === clipId) {
      setSelectedClipId(null);
    }
  }, [selectedClipId]);

  const reorderClip = useCallback((fromIndex: number, toIndex: number) => {
    setClips(currentClips => reorderClips(currentClips, fromIndex, toIndex));
  }, []);

  const trimClipDuration = useCallback((clipId: string, newDuration: number) => {
    setClips(currentClips => {
      const clip = currentClips.find(c => c.id === clipId);
      if (!clip) return currentClips;
      return trimClip(clip, newDuration, currentClips);
    });
  }, []);

  const selectClip = useCallback((clipId: string | null) => {
    setSelectedClipId(clipId);
  }, []);

  // Transition operations
  const setClipTransition = useCallback(
    (clipId: string, position: 'in' | 'out', transition: TransitionType) => {
      setClips(currentClips => setTransition(currentClips, clipId, position, transition));
    },
    []
  );

  // Playback operations
  const play = useCallback(() => {
    if (totalDuration === 0) return;
    setIsPlaying(true);
  }, [totalDuration]);

  const pause = useCallback(() => {
    setIsPlaying(false);
  }, []);

  const stop = useCallback(() => {
    setIsPlaying(false);
    setCurrentTime(0);
  }, []);

  const seek = useCallback((time: number) => {
    const clampedTime = Math.max(0, Math.min(time, totalDuration));
    setCurrentTime(clampedTime);
    onTimeUpdate?.(clampedTime);
  }, [totalDuration, onTimeUpdate]);

  // Zoom operations
  const zoomIn = useCallback(() => {
    setZoomLevel(current => Math.min(ZOOM_LEVELS.length - 1, current + 1));
  }, []);

  const zoomOut = useCallback(() => {
    setZoomLevel(current => Math.max(0, current - 1));
  }, []);

  const setZoom = useCallback((level: number) => {
    const clampedLevel = Math.max(0, Math.min(ZOOM_LEVELS.length - 1, level));
    setZoomLevel(clampedLevel);
  }, []);

  // Validation
  const validate = useCallback(() => {
    return validateTimeline(clips);
  }, [clips]);

  // Reset
  const reset = useCallback(() => {
    setClips([]);
    setSelectedClipId(null);
    setCurrentTime(0);
    setIsPlaying(false);
    setZoomLevel(DEFAULT_ZOOM_LEVEL);
  }, []);

  // Auto-play on mount if enabled
  useEffect(() => {
    if (autoPlay && clips.length > 0) {
      play();
    }
  }, [autoPlay, clips.length]);

  return {
    // Timeline state
    clips,
    selectedClipId,
    currentTime,
    totalDuration,
    isPlaying,

    // Zoom state
    zoomLevel,
    pixelsPerSecond,

    // Clip operations
    addClips,
    removeClip,
    reorderClip,
    trimClipDuration,
    selectClip,

    // Transition operations
    setClipTransition,

    // Playback operations
    play,
    pause,
    stop,
    seek,

    // Zoom operations
    zoomIn,
    zoomOut,
    setZoom,

    // Validation
    validate,

    // Reset
    reset,
  };
}
