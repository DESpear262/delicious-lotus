/**
 * PlaybackEngine - Core playback management for the timeline
 *
 * Manages playback state (play, pause, seek) and provides precise
 * frame-based timing using requestAnimationFrame
 */

import type { TimelineStoreInstance } from '../stores/timelineStore'
import type { EditorStoreInstance } from '../stores/editorStore'

export type PlaybackState = 'playing' | 'paused' | 'stopped'

export interface PlaybackEngineConfig {
  timelineStore: TimelineStoreInstance
  editorStore: EditorStoreInstance
  onFrameUpdate?: (frame: number) => void
  onStateChange?: (state: PlaybackState) => void
}

export class PlaybackEngine {
  private timelineStore: TimelineStoreInstance
  private editorStore: EditorStoreInstance
  private state: PlaybackState = 'stopped'
  private animationFrameId: number | null = null
  private lastFrameTime: number = 0
  private frameAccumulator: number = 0

  // Callbacks
  private onFrameUpdate?: (frame: number) => void
  private onStateChange?: (state: PlaybackState) => void

  constructor(config: PlaybackEngineConfig) {
    this.timelineStore = config.timelineStore
    this.editorStore = config.editorStore
    this.onFrameUpdate = config.onFrameUpdate
    this.onStateChange = config.onStateChange

    // Subscribe to editor store play/pause changes
    this.editorStore.subscribe((editorState) => {
      const wasPlaying = this.state === 'playing'
      const shouldPlay = editorState.isPlaying

      if (shouldPlay && !wasPlaying) {
        this.play()
      } else if (!shouldPlay && wasPlaying) {
        this.pause()
      }
    })
  }

  /**
   * Start playback from current playhead position
   */
  play(): void {
    if (this.state === 'playing') return

    this.state = 'playing'
    this.lastFrameTime = performance.now()
    this.frameAccumulator = 0
    this.tick()
    this.notifyStateChange()
  }

  /**
   * Pause playback at current position
   */
  pause(): void {
    if (this.state !== 'playing') return

    this.state = 'paused'
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId)
      this.animationFrameId = null
    }
    this.notifyStateChange()
  }

  /**
   * Stop playback and reset to beginning
   */
  stop(): void {
    this.pause()
    this.state = 'stopped'
    this.timelineStore.getState().setPlayhead(0)
    this.notifyStateChange()
  }

  /**
   * Seek to a specific frame
   */
  seek(frame: number): void {
    const timelineState = this.timelineStore.getState()
    timelineState.setPlayhead(frame)

    if (this.onFrameUpdate) {
      this.onFrameUpdate(frame)
    }
  }

  /**
   * Get current playback state
   */
  getState(): PlaybackState {
    return this.state
  }

  /**
   * Get current frame position
   */
  getCurrentFrame(): number {
    return this.timelineStore.getState().playhead
  }

  /**
   * Get total duration in frames
   */
  getDuration(): number {
    return this.timelineStore.getState().duration
  }

  /**
   * Get current time in seconds
   */
  getCurrentTime(): number {
    const { playhead, fps } = this.timelineStore.getState()
    return playhead / fps
  }

  /**
   * Get total duration in seconds
   */
  getDurationSeconds(): number {
    const { duration, fps } = this.timelineStore.getState()
    return duration / fps
  }

  /**
   * Set playback rate (0.25x - 2x)
   */
  setPlaybackRate(rate: number): void {
    this.editorStore.getState().setPlaybackRate(rate)
  }

  /**
   * Get current playback rate
   */
  getPlaybackRate(): number {
    return this.editorStore.getState().playbackRate
  }

  /**
   * Main animation loop using requestAnimationFrame
   */
  private tick = (): void => {
    if (this.state !== 'playing') return

    const now = performance.now()
    const deltaTime = now - this.lastFrameTime
    this.lastFrameTime = now

    const { fps } = this.timelineStore.getState()
    const playbackRate = this.getPlaybackRate()

    // Calculate how many milliseconds per frame at current FPS and playback rate
    const msPerFrame = (1000 / fps) / playbackRate

    // Accumulate time and advance frames when we've accumulated enough time
    this.frameAccumulator += deltaTime

    if (this.frameAccumulator >= msPerFrame) {
      // Consume accumulated time, but only advance a small number of frames per tick
      const maxFramesPerTick = 2
      let framesToAdvance = 0

      while (this.frameAccumulator >= msPerFrame && framesToAdvance < maxFramesPerTick) {
        this.frameAccumulator -= msPerFrame
        framesToAdvance++
      }

      const currentFrame = this.getCurrentFrame()
      const duration = this.getDuration()
      let nextFrame = currentFrame + framesToAdvance

      // Check if we've reached the end
      if (nextFrame >= duration) {
        nextFrame = duration
        this.pause()
        this.editorStore.getState().pause()
      }

      // Update playhead
      this.timelineStore.getState().setPlayhead(nextFrame)

      // Notify frame update
      if (this.onFrameUpdate) {
        this.onFrameUpdate(nextFrame)
      }
    }

    // Continue animation loop if still playing
    if (this.state === 'playing') {
      this.animationFrameId = requestAnimationFrame(this.tick)
    }
  }

  /**
   * Notify state change listeners
   */
  private notifyStateChange(): void {
    if (this.onStateChange) {
      this.onStateChange(this.state)
    }
  }

  /**
   * Clean up resources
   */
  dispose(): void {
    this.pause()
    this.onFrameUpdate = undefined
    this.onStateChange = undefined
  }
}
