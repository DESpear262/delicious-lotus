/**
 * Upload Hook
 * Provides upload functionality to components with UploadManager integration
 */

import { useEffect, useRef, useContext } from 'react'
import { UploadManager } from '../services/uploadManager'
import { MediaStoreContext } from '../contexts/StoreContext'
import { useMediaStore } from '../contexts/StoreContext'
import type { UploadItem } from '../types/stores'

export interface UseUploadReturn {
  /**
   * Add files to the upload queue
   */
  uploadFiles: (files: File[]) => Promise<void>

  /**
   * Cancel an in-progress upload
   */
  cancelUpload: (uploadId: string) => void

  /**
   * Retry a failed upload
   */
  retryUpload: (uploadId: string) => void

  /**
   * Remove an upload from the queue
   */
  removeUpload: (uploadId: string) => void

  /**
   * Clear all completed uploads from the queue
   */
  clearCompleted: () => void

  /**
   * Get current upload queue
   */
  uploads: UploadItem[]

  /**
   * Get upload speeds for active uploads
   */
  uploadSpeeds: Map<string, number>
}

/**
 * Hook to manage file uploads with concurrent upload support
 */
export function useUpload(): UseUploadReturn {
  const mediaStoreContext = useContext(MediaStoreContext)
  const uploadManagerRef = useRef<UploadManager | null>(null)

  // Subscribe to upload queue changes
  const uploads = useMediaStore((state) => state.uploadQueue)
  const clearCompletedUploads = useMediaStore((state) => state.clearCompletedUploads)
  const removeFromQueue = useMediaStore((state) => state.removeFromQueue)

  // Validate context exists
  if (!mediaStoreContext) {
    throw new Error('useUpload must be used within StoreProvider')
  }

  // Initialize UploadManager
  useEffect(() => {
    // mediaStoreContext is guaranteed to be non-null here
    const storeInstance = mediaStoreContext!

    if (!uploadManagerRef.current) {
      uploadManagerRef.current = new UploadManager(storeInstance, {
        maxConcurrent: 3,
        maxRetries: 3,
        retryDelay: 2000,
      })
    }

    // Cleanup on unmount
    return () => {
      if (uploadManagerRef.current) {
        uploadManagerRef.current.destroy()
        uploadManagerRef.current = null
      }
    }
  }, [mediaStoreContext])

  // Get upload speeds
  const uploadSpeeds = uploadManagerRef.current?.getUploadSpeeds() ?? new Map()

  return {
    uploadFiles: async (files: File[]) => {
      if (!uploadManagerRef.current) {
        throw new Error('UploadManager not initialized')
      }
      await uploadManagerRef.current.addFiles(files)
    },

    cancelUpload: (uploadId: string) => {
      if (!uploadManagerRef.current) return
      uploadManagerRef.current.cancelUpload(uploadId)
    },

    retryUpload: (uploadId: string) => {
      if (!uploadManagerRef.current) return
      uploadManagerRef.current.retryUpload(uploadId)
    },

    removeUpload: (uploadId: string) => {
      removeFromQueue(uploadId)
    },

    clearCompleted: () => {
      clearCompletedUploads()
    },

    uploads,
    uploadSpeeds,
  }
}
