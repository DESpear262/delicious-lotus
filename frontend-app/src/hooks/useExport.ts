import { useState, useCallback } from 'react'
import { useTimelineStore, useMediaStore, useWebSocketStore } from '@/contexts/StoreContext'
import {
  exportCompositionWithRetry,
  ExportError,
} from '@/services/exportService'
import {
  serializeComposition,
  validateCompositionData,
} from '@/lib/compositionSerializer'
import type { ExportSettings } from '@/types/export'

export interface UseExportResult {
  isExporting: boolean
  error: Error | null
  exportVideo: (settings: ExportSettings) => Promise<void>
  downloadVideo: (downloadUrl: string, fileName: string) => void
  clearError: () => void
}

/**
 * Custom hook for managing video export workflow
 */
export function useExport(): UseExportResult {
  const [isExporting, setIsExporting] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  // Get stores
  const clips = useTimelineStore((state) => state.clips)
  const tracks = useTimelineStore((state) => state.tracks)
  const duration = useTimelineStore((state) => state.duration)
  const fps = useTimelineStore((state) => state.fps)
  const assets = useMediaStore((state) => state.assets)
  const addJob = useWebSocketStore((state) => state.addJob)

  /**
   * Initiates video export
   */
  const exportVideo = useCallback(
    async (settings: ExportSettings) => {
      setIsExporting(true)
      setError(null)

      try {
        // Build asset URL map
        const assetUrlMap = new Map<string, string>()
        for (const [id, asset] of assets) {
          assetUrlMap.set(id, asset.url)
        }

        // Validate composition data
        const validation = validateCompositionData(clips, tracks, assetUrlMap)
        if (!validation.valid) {
          throw new Error(
            `Invalid composition data: ${validation.errors.join(', ')}`
          )
        }

        // Serialize composition
        const composition = serializeComposition(
          clips,
          tracks,
          assetUrlMap,
          settings,
          duration,
          fps
        )

        // Submit export job
        const response = await exportCompositionWithRetry(composition)

        // Add job to WebSocket store for progress tracking
        addJob({
          id: response.jobId,
          type: 'export',
          status: response.status,
          progress: 0,
          message: response.message,
          createdAt: new Date(response.createdAt),
          updatedAt: new Date(response.createdAt),
        })

        console.log(`Export job created: ${response.jobId}`)
      } catch (err) {
        const exportError =
          err instanceof ExportError
            ? err
            : new Error(err instanceof Error ? err.message : 'Export failed')
        setError(exportError)
        throw exportError
      } finally {
        setIsExporting(false)
      }
    },
    [clips, tracks, duration, fps, assets, addJob]
  )

  /**
   * Downloads the exported video
   */
  const downloadVideo = useCallback(
    (downloadUrl: string, fileName: string) => {
      try {
        // Create a temporary anchor element to trigger download
        const link = document.createElement('a')
        link.href = downloadUrl
        link.download = fileName
        link.style.display = 'none'
        document.body.appendChild(link)
        link.click()

        // Clean up
        setTimeout(() => {
          document.body.removeChild(link)
        }, 100)
      } catch (err) {
        console.error('Failed to download video:', err)
        setError(
          new Error(
            err instanceof Error ? err.message : 'Failed to download video'
          )
        )
      }
    },
    []
  )

  /**
   * Clears the current error
   */
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    isExporting,
    error,
    exportVideo,
    downloadVideo,
    clearError,
  }
}
