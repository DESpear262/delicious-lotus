/**
 * Services - Centralized export for all service modules
 */

// Playback Engine
export { PlaybackEngine } from './PlaybackEngine'
export type { PlaybackState, PlaybackEngineConfig } from './PlaybackEngine'

// Clip Resolver
export { ClipResolver } from './ClipResolver'
export type { ActiveClip } from './ClipResolver'

// Video Element Pool
export { VideoElementPool } from './VideoElementPool'
export type { VideoElementOptions } from './VideoElementPool'

// DOM Compositor
export { DOMCompositor } from './DOMCompositor'
export type { LayerNode, CompositorOptions } from './DOMCompositor'

// Transform Engine
export { TransformEngine } from './TransformEngine'
export type { TransformState, Keyframe, EasingFunction } from './TransformEngine'

// Audio Engine
export { AudioEngine } from './AudioEngine'
export type { AudioEngineOptions } from './AudioEngine'

// Preview Renderer
export { PreviewRenderer } from './PreviewRenderer'
export type { PreviewRendererOptions, PerformanceMetrics } from './PreviewRenderer'

// Performance Monitor
export { PerformanceMonitor, performanceMonitor } from './PerformanceMonitor'
export { useDebouncedCallback, useThrottledCallback } from './PerformanceMonitor'
export type { PerformanceProfile, InteractionMetrics } from './PerformanceMonitor'

// Upload Services
export { uploadService } from './uploadService'
export { UploadManager } from './uploadManager'

// WebSocket Service
export { WebSocketService, getWebSocketService } from './WebSocketService'

// Export Service
export {
  exportComposition,
  exportCompositionWithRetry,
  getExportJobStatus,
  cancelExportJob,
} from './exportService'
export {
  ExportError,
  ValidationError,
  NetworkError,
} from './exportService'
export type { ExportJobResponse } from './exportService'
