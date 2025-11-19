// Export Configuration Types

export type AspectRatio = '16:9' | '9:16' | '1:1' | '4:3'
export type Resolution = '1080p' | '720p' | '480p' | '4k'
export type ExportFormat = 'mp4' | 'webm'
export type Codec = 'h264' | 'vp8' | 'vp9'
export type FrameRate = 24 | 30 | 60

export interface ExportSettings {
  name: string
  aspectRatio: AspectRatio
  resolution: Resolution
  format: ExportFormat
  codec?: Codec
  quality: number // CRF value (18-28, lower is better quality)
  frameRate: FrameRate
}

export interface ExportDimensions {
  width: number
  height: number
}

export interface ExportJob {
  id: string
  settings: ExportSettings
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'canceled'
  progress: number // 0-100
  createdAt: Date
  updatedAt: Date
  downloadUrl?: string
  error?: string
}

// Resolution mappings
export const RESOLUTION_DIMENSIONS: Record<Resolution, Record<AspectRatio, ExportDimensions>> = {
  '480p': {
    '16:9': { width: 854, height: 480 },
    '9:16': { width: 480, height: 854 },
    '1:1': { width: 480, height: 480 },
    '4:3': { width: 640, height: 480 },
  },
  '720p': {
    '16:9': { width: 1280, height: 720 },
    '9:16': { width: 720, height: 1280 },
    '1:1': { width: 720, height: 720 },
    '4:3': { width: 960, height: 720 },
  },
  '1080p': {
    '16:9': { width: 1920, height: 1080 },
    '9:16': { width: 1080, height: 1920 },
    '1:1': { width: 1080, height: 1080 },
    '4:3': { width: 1440, height: 1080 },
  },
  '4k': {
    '16:9': { width: 3840, height: 2160 },
    '9:16': { width: 2160, height: 3840 },
    '1:1': { width: 2160, height: 2160 },
    '4:3': { width: 2880, height: 2160 },
  },
}

// Format/Codec compatibility
export const FORMAT_CODEC_MAP: Record<ExportFormat, Codec[]> = {
  mp4: ['h264'],
  webm: ['vp8', 'vp9'],
}

// Quality presets (CRF values)
export const QUALITY_PRESETS = {
  draft: 28,
  good: 23,
  high: 20,
  best: 18,
} as const

export type QualityPreset = keyof typeof QUALITY_PRESETS
