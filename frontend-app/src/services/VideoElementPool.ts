/**
 * VideoElementPool - Efficient video element management with source switching
 *
 * Manages a pool of reusable HTML5 video elements for optimal playback performance
 * Handles preloading, source switching, and synchronization with playback position
 */

import type { MediaAsset } from '../types/stores'

export interface VideoElementOptions {
  preloadCount?: number // Number of upcoming clips to preload
  poolSize?: number // Maximum video elements in pool
  muted?: boolean // Mute video elements by default
}

interface VideoElementState {
  element: HTMLVideoElement
  currentAssetId: string | null
  isLoading: boolean
  isPrepared: boolean
  lastUsedTime: number
}

export class VideoElementPool {
  private pool: VideoElementState[] = []
  private poolSize: number
  private preloadCount: number
  private muted: boolean
  private assetCache: Map<string, MediaAsset> = new Map()

  constructor(options: VideoElementOptions = {}) {
    this.poolSize = options.poolSize ?? 3
    this.preloadCount = options.preloadCount ?? 2
    this.muted = options.muted ?? true

    this.initializePool()
  }

  /**
   * Initialize the video element pool
   */
  private initializePool(): void {
    for (let i = 0; i < this.poolSize; i++) {
      const videoElement = this.createVideoElement()
      this.pool.push({
        element: videoElement,
        currentAssetId: null,
        isLoading: false,
        isPrepared: false,
        lastUsedTime: 0,
      })
    }
  }

  /**
   * Create a new video element with proper configuration
   */
  private createVideoElement(): HTMLVideoElement {
    const video = document.createElement('video')

    // Configure video element
    video.muted = this.muted
    video.playsInline = true
    video.preload = 'auto'
    video.crossOrigin = 'anonymous'

    // Styling for preview rendering
    video.style.position = 'absolute'
    video.style.width = '100%'
    video.style.height = '100%'
    video.style.objectFit = 'contain'
    video.style.pointerEvents = 'none'

    return video
  }

  /**
   * Get or create a video element for the specified asset
   * Returns a prepared video element at the correct time position
   */
  async getVideoElement(
    assetId: string,
    asset: MediaAsset,
    targetTime: number,
    isPlaying: boolean = false
  ): Promise<HTMLVideoElement> {
    // Check if we already have this asset loaded
    let videoState = this.pool.find((vs) => vs.currentAssetId === assetId)

    if (videoState) {
      // Update last used time
      videoState.lastUsedTime = Date.now()
      const video = videoState.element

      // During playback, allow small drift but resync if too far off
      // When paused, seek to exact position for scrubbing
      const timeDiff = Math.abs(video.currentTime - targetTime)

      if (!isPlaying) {
        // Paused/scrubbing - seek to exact position if > 1 frame
        if (timeDiff > 0.033) {  // ~1 frame at 30fps
          await this.seekVideo(video, targetTime)
        }
      } else {
        // Playing - only seek if drift is significant (> 3 frames to avoid choppiness)
        if (timeDiff > 0.1) {  // ~3 frames at 30fps
          await this.seekVideo(video, targetTime)
        }
      }

      return video
    }

    // Get least recently used video element
    videoState = this.getLRUVideoState()

    // Load new source
    await this.loadVideoSource(videoState, assetId, asset)

    // Seek to target time
    await this.seekVideo(videoState.element, targetTime)

    return videoState.element
  }

  /**
   * Load a video source into a video element
   */
  private async loadVideoSource(
    videoState: VideoElementState,
    assetId: string,
    asset: MediaAsset
  ): Promise<void> {
    const video = videoState.element

    // Validate URL
    if (!asset.url) {
      throw new Error(`Video asset ${asset.name} has no URL`)
    }

    // Update state
    videoState.isLoading = true
    videoState.isPrepared = false
    videoState.currentAssetId = assetId
    videoState.lastUsedTime = Date.now()

    // Cache asset info
    this.assetCache.set(assetId, asset)

    console.log(`[VideoPool] Loading video: ${asset.name} from ${asset.url}`)

    return new Promise((resolve, reject) => {
      const handleCanPlay = () => {
        videoState.isLoading = false
        videoState.isPrepared = true
        video.removeEventListener('canplay', handleCanPlay)
        video.removeEventListener('error', handleError)
        console.log(`[VideoPool] Video loaded successfully: ${asset.name}`)
        resolve()
      }

      const handleError = (e: ErrorEvent | Event) => {
        videoState.isLoading = false
        videoState.isPrepared = false
        videoState.currentAssetId = null
        video.removeEventListener('canplay', handleCanPlay)
        video.removeEventListener('error', handleError)
        console.error(`[VideoPool] Failed to load video: ${asset.name}`, e)
        reject(new Error(`Failed to load video: ${asset.name}`))
      }

      video.addEventListener('canplay', handleCanPlay, { once: true })
      video.addEventListener('error', handleError, { once: true })

      // Set source
      video.src = asset.url
      video.load()
    })
  }

  /**
   * Seek video element to specific time
   */
  private async seekVideo(video: HTMLVideoElement, time: number): Promise<void> {
    if (Math.abs(video.currentTime - time) < 0.016) {
      // Already at target time (within one frame at 60fps)
      return
    }

    return new Promise((resolve, reject) => {
      const handleSeeked = () => {
        video.removeEventListener('seeked', handleSeeked)
        video.removeEventListener('error', handleError)
        resolve()
      }

      const handleError = () => {
        video.removeEventListener('seeked', handleSeeked)
        video.removeEventListener('error', handleError)
        reject(new Error('Seek failed'))
      }

      // Timeout to prevent infinite waiting
      const timeout = setTimeout(() => {
        video.removeEventListener('seeked', handleSeeked)
        video.removeEventListener('error', handleError)
        resolve() // Resolve anyway to not block playback
      }, 1000)

      video.addEventListener('seeked', () => {
        clearTimeout(timeout)
        handleSeeked()
      }, { once: true })

      video.addEventListener('error', () => {
        clearTimeout(timeout)
        handleError()
      }, { once: true })

      video.currentTime = time
    })
  }

  /**
   * Preload upcoming video assets
   */
  async preloadAssets(assetIds: string[], assets: Map<string, MediaAsset>): Promise<void> {
    const toPreload = assetIds.slice(0, this.preloadCount)

    const preloadPromises = toPreload.map(async (assetId) => {
      // Skip if already loaded
      if (this.pool.some((vs) => vs.currentAssetId === assetId)) {
        return
      }

      const asset = assets.get(assetId)
      if (!asset || asset.type !== 'video') {
        return
      }

      // Get available video state for preloading
      const availableState = this.pool.find(
        (vs) => !vs.isLoading && vs.lastUsedTime === 0
      )

      if (availableState) {
        try {
          await this.loadVideoSource(availableState, assetId, asset)
        } catch (error) {
          console.warn(`Failed to preload video ${assetId}:`, error)
        }
      }
    })

    await Promise.allSettled(preloadPromises)
  }

  /**
   * Get the least recently used video state
   */
  private getLRUVideoState(): VideoElementState {
    return this.pool.reduce((lru, current) =>
      current.lastUsedTime < lru.lastUsedTime ? current : lru
    )
  }

  /**
   * Synchronize video playback with timeline
   */
  syncToTimeline(video: HTMLVideoElement, isPlaying: boolean, playbackRate: number): void {
    if (isPlaying && video.paused) {
      video.playbackRate = playbackRate
      video.play().catch((e) => {
        console.warn('Video play failed:', e)
      })
    } else if (!isPlaying && !video.paused) {
      video.pause()
    } else if (isPlaying && video.playbackRate !== playbackRate) {
      video.playbackRate = playbackRate
    }
  }

  /**
   * Set mute state for all videos
   */
  setMuted(muted: boolean): void {
    this.muted = muted
    this.pool.forEach((vs) => {
      vs.element.muted = muted
    })
  }

  /**
   * Get all video elements (for attaching to DOM)
   */
  getAllVideoElements(): HTMLVideoElement[] {
    return this.pool.map((vs) => vs.element)
  }

  /**
   * Clear a specific video from the pool
   */
  clearVideo(assetId: string): void {
    const videoState = this.pool.find((vs) => vs.currentAssetId === assetId)
    if (videoState) {
      videoState.element.pause()
      videoState.element.src = ''
      videoState.currentAssetId = null
      videoState.isLoading = false
      videoState.isPrepared = false
      videoState.lastUsedTime = 0
    }
  }

  /**
   * Clear all videos and reset pool
   */
  reset(): void {
    this.pool.forEach((vs) => {
      vs.element.pause()
      vs.element.src = ''
      vs.currentAssetId = null
      vs.isLoading = false
      vs.isPrepared = false
      vs.lastUsedTime = 0
    })
    this.assetCache.clear()
  }

  /**
   * Clean up resources and remove video elements
   */
  dispose(): void {
    this.pool.forEach((vs) => {
      vs.element.pause()
      vs.element.src = ''
      vs.element.remove()
    })
    this.pool = []
    this.assetCache.clear()
  }
}
