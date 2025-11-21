/**
 * Upload Manager
 * Orchestrates concurrent file uploads with queue management, error recovery, and retry logic
 */

import { uploadFile, UploadError, type UploadProgressCallback } from './uploadService'
import { validateFile } from '../lib/fileValidation'
import type { MediaStoreInstance } from '../stores/mediaStore'

interface UploadTask {
  uploadId: string
  file: File
  abortController: AbortController
  retryCount: number
  startTime: number
}

interface UploadStats {
  uploadId: string
  bytesPerSecond: number
  lastUpdate: number
}

export interface UploadManagerConfig {
  maxConcurrent: number // Maximum number of simultaneous uploads
  maxRetries: number // Maximum retry attempts per file
  retryDelay: number // Base delay for exponential backoff (ms)
}

const DEFAULT_CONFIG: UploadManagerConfig = {
  maxConcurrent: 3,
  maxRetries: 3,
  retryDelay: 2000, // 2 seconds
}

export class UploadManager {
  private config: UploadManagerConfig
  private mediaStore: MediaStoreInstance
  private activeUploads: Map<string, UploadTask> = new Map()
  private uploadStats: Map<string, UploadStats> = new Map()
  private queue: string[] = [] // Queue of upload IDs waiting to start
  private stuckUploadCheckInterval: number | null = null

  constructor(mediaStore: MediaStoreInstance, config: Partial<UploadManagerConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config }
    this.mediaStore = mediaStore
    this.startStuckUploadMonitoring()
  }

  /**
   * Add files to the upload queue
   */
  async addFiles(files: File[]): Promise<void> {
    // Validate all files first
    const validFiles: File[] = []

    for (const file of files) {
      const result = validateFile(file)

      if (result.valid) {
        validFiles.push(file)
      } else {
        // Show validation error to user (could emit event or use toast)
        // Type guard: result.valid === false means error exists
        console.error(`Validation failed for ${file.name}:`, (result as { valid: false; error: { message: string } }).error.message)
      }
    }

    if (validFiles.length === 0) {
      return
    }

    // Add to upload queue in the store
    const uploadIds: string[] = []
    for (const file of validFiles) {
      const uploadId = this.mediaStore.getState().queueUpload(file)
      uploadIds.push(uploadId)
      this.queue.push(uploadId)
    }

    // Process the queue
    this.processQueue()
  }

  /**
   * Process queued uploads
   */
  private processQueue(): void {
    // Start uploads up to the concurrent limit
    while (
      this.activeUploads.size < this.config.maxConcurrent &&
      this.queue.length > 0
    ) {
      const uploadId = this.queue.shift()
      if (uploadId) {
        this.startUpload(uploadId)
      }
    }
  }

  /**
   * Start an individual upload
   */
  private async startUpload(uploadId: string): Promise<void> {
    const state = this.mediaStore.getState()
    const uploadItem = state.uploadQueue.find((u) => u.id === uploadId)

    if (!uploadItem) {
      console.error(`Upload ${uploadId} not found in queue`)
      return
    }

    const abortController = new AbortController()
    const task: UploadTask = {
      uploadId,
      file: uploadItem.file,
      abortController,
      retryCount: uploadItem.retryCount,
      startTime: Date.now(),
    }

    this.activeUploads.set(uploadId, task)
    state.setUploadStatus(uploadId, 'uploading')

    // Create progress callback
    const onProgress: UploadProgressCallback = (progress) => {
      state.updateUploadProgress(uploadId, progress.percentage)

      // Track upload speed
      this.uploadStats.set(uploadId, {
        uploadId,
        bytesPerSecond: progress.bytesPerSecond || 0,
        lastUpdate: Date.now(),
      })
    }

    try {
      // Perform the upload
      const result = await uploadFile(uploadItem.file, onProgress, abortController.signal)

      // Add the asset to the media library
      state.addAsset({
        id: result.id,
        name: result.name,
        type: this.getAssetType(result.file_type),
        url: result.url, // Use URL from upload result
        thumbnailUrl: result.thumbnail_url,
        size: result.file_size,
        createdAt: new Date(),
        metadata: {},
      })

      // Mark as completed and store the asset ID
      state.setUploadStatus(uploadId, 'completed')
      state.updateUploadProgress(uploadId, 100)
      state.updateUpload(uploadId, { uploadedAssetId: result.id })
    } catch (error) {
      await this.handleUploadError(uploadId, error, task)
    } finally {
      // Clean up
      this.activeUploads.delete(uploadId)
      this.uploadStats.delete(uploadId)

      // Process next item in queue
      this.processQueue()
    }
  }

  /**
   * Handle upload errors with retry logic
   */
  private async handleUploadError(
    uploadId: string,
    error: unknown,
    task: UploadTask
  ): Promise<void> {
    const state = this.mediaStore.getState()
    const isRetryable = error instanceof UploadError && error.retryable
    const canRetry = task.retryCount < this.config.maxRetries

    if (isRetryable && canRetry) {
      // Calculate exponential backoff delay
      const delay = this.config.retryDelay * Math.pow(2, task.retryCount)

      console.log(
        `Upload ${uploadId} failed, retrying in ${delay}ms (attempt ${task.retryCount + 1}/${this.config.maxRetries})`
      )

      // Update retry count in store
      const upload = state.uploadQueue.find((u) => u.id === uploadId)
      if (upload) {
        state.updateUpload(uploadId, { retryCount: upload.retryCount + 1 })
      }

      // Wait before retrying
      await new Promise((resolve) => setTimeout(resolve, delay))

      // Re-queue the upload
      this.queue.unshift(uploadId) // Add to front of queue for priority
      this.processQueue()
    } else {
      // Permanent failure
      const errorMessage =
        error instanceof Error ? error.message : 'Unknown error occurred'

      console.error(`Upload ${uploadId} failed permanently:`, errorMessage)

      state.setUploadStatus(uploadId, 'failed', errorMessage)
    }
  }

  /**
   * Cancel an upload
   */
  cancelUpload(uploadId: string): void {
    const task = this.activeUploads.get(uploadId)

    if (task) {
      // Abort the upload
      task.abortController.abort()
      this.activeUploads.delete(uploadId)
      this.uploadStats.delete(uploadId)
    } else {
      // Remove from queue if not started yet
      const queueIndex = this.queue.indexOf(uploadId)
      if (queueIndex !== -1) {
        this.queue.splice(queueIndex, 1)
      }
    }

    // Update store status
    this.mediaStore.getState().setUploadStatus(uploadId, 'cancelled')
  }

  /**
   * Retry a failed upload
   */
  retryUpload(uploadId: string): void {
    const state = this.mediaStore.getState()
    const upload = state.uploadQueue.find((u) => u.id === uploadId)

    if (upload && upload.status === 'failed') {
      // Reset status and add to queue
      state.updateUpload(uploadId, { retryCount: 0, error: undefined })
      state.setUploadStatus(uploadId, 'queued')
      this.queue.push(uploadId)
      this.processQueue()
    }
  }

  /**
   * Get current upload speeds for display
   */
  getUploadSpeeds(): Map<string, number> {
    const speeds = new Map<string, number>()
    this.uploadStats.forEach((stats) => {
      speeds.set(stats.uploadId, stats.bytesPerSecond)
    })
    return speeds
  }

  /**
   * Monitor for stuck uploads (no progress for >60 seconds)
   */
  private startStuckUploadMonitoring(): void {
    this.stuckUploadCheckInterval = window.setInterval(() => {
      const now = Date.now()
      const stuckTimeout = 60000 // 60 seconds

      this.uploadStats.forEach((stats, uploadId) => {
        const timeSinceUpdate = now - stats.lastUpdate

        if (timeSinceUpdate > stuckTimeout && stats.bytesPerSecond === 0) {
          console.warn(`Upload ${uploadId} appears stuck, cancelling...`)
          this.cancelUpload(uploadId)

          // Mark as failed so it can be retried
          const task = this.activeUploads.get(uploadId)
          if (task) {
            this.handleUploadError(
              uploadId,
              new UploadError('Upload stuck - no progress', undefined, true),
              task
            )
          }
        }
      })
    }, 30000) // Check every 30 seconds
  }

  /**
   * Clean up resources
   */
  destroy(): void {
    // Cancel all active uploads
    this.activeUploads.forEach((task) => {
      task.abortController.abort()
    })

    // Clear monitoring
    if (this.stuckUploadCheckInterval !== null) {
      clearInterval(this.stuckUploadCheckInterval)
    }

    // Clear state
    this.activeUploads.clear()
    this.uploadStats.clear()
    this.queue = []
  }

  /**
   * Helper to determine asset type from MIME type or simple type string
   */
  private getAssetType(fileType: string): 'image' | 'video' | 'audio' {
    const lowerType = fileType.toLowerCase()

    // Handle simple type strings from backend (e.g., "image", "video", "audio")
    if (lowerType === 'image' || lowerType.startsWith('image/')) return 'image'
    if (lowerType === 'video' || lowerType.startsWith('video/')) return 'video'
    if (lowerType === 'audio' || lowerType.startsWith('audio/')) return 'audio'

    // Fallback to image for unknown types
    console.warn(`Unknown file type: ${fileType}, defaulting to image`)
    return 'image'
  }
}
