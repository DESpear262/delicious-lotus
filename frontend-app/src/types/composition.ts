/**
 * TypeScript types for Composition API
 * Matches backend schema in ffmpeg-backend/src/app/api/schemas/composition.py
 */

export type VideoResolution = '480p' | '720p' | '1080p' | '4k';
export type VideoFormat = 'mp4' | 'mov' | 'avi';

/**
 * Output settings for the composition
 */
export interface OutputSettings {
  resolution: VideoResolution;
  format: VideoFormat;
  fps: number; // 24-60
  bitrate: string | null; // Optional, pattern: ^\d+[kKmM]$ (e.g., "2000k", "5M")
}

/**
 * Audio configuration for the composition
 */
export interface AudioConfig {
  music_url: string | null;
  voiceover_url: string | null;
  music_volume: number; // 0.0-1.0
  voiceover_volume: number; // 0.0-1.0
  original_audio_volume: number; // 0.0-1.0
}

/**
 * Clip configuration
 */
export interface ClipConfig {
  video_url: string;
  start_time: number; // >= 0
  end_time: number; // > start_time
  trim_start: number; // >= 0, default 0
  trim_end: number; // >= 0 and > trim_start, nullable
}

/**
 * Overlay configuration
 */
export interface OverlayConfig {
  text: string;
  start_time: number;
  end_time: number;
  position: {
    x: number;
    y: number;
  };
  style: {
    font_size: number;
    color: string;
    background_color: string | null;
  };
}

/**
 * Request payload for creating a composition
 */
export interface CompositionCreateRequest {
  title: string; // Required, 1-255 chars
  description: string | null;
  clips: ClipConfig[]; // Required, 1-20 items
  audio?: AudioConfig; // Optional, backend provides defaults
  overlays?: OverlayConfig[]; // Optional, defaults to []
  output?: OutputSettings; // Optional, backend provides defaults
}

/**
 * Form state for export dialog
 */
export interface ExportSettings {
  description: string | null;
  output: OutputSettings;
}

/**
 * Default output settings
 */
export const DEFAULT_OUTPUT_SETTINGS: OutputSettings = {
  resolution: '1080p',
  format: 'mp4',
  fps: 30,
  bitrate: null,
};
