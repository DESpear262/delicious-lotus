import { useEffect, useMemo, useState } from 'react'
// import { useTemporalStore } from 'zundo' // Removed: zundo v2 doesn't export useTemporalStore
import { Timeline } from '../components/timeline'
import { ClipPropertiesPanel } from '../components/timeline/ClipPropertiesPanel'
import { ExportDialog } from '../components/ExportDialog'
import { useTimelineStore, useMediaStore } from '../contexts/StoreContext'
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts'
import type { TrackType } from '../types/stores'
import { api } from '../lib/api'
import { toast } from '../lib/toast'

export function TimelinePage() {
  const timelineStore = useTimelineStore()
  const mediaStore = useMediaStore()
  const [isExportDialogOpen, setIsExportDialogOpen] = useState(false)
  const [exportPayload, setExportPayload] = useState<{
    clips: Array<{
      video_url: string
      start_time: number
      end_time: number
      trim_start: number
      trim_end: number
    }>
    overlays: unknown[]
  } | null>(null)

  // Get temporal store actions for undo/redo
  // TODO: Implement proper zundo v2 temporal store access
  // const { undo, redo, futureStates, pastStates } = useTemporalStore(timelineStore as any)
  const canUndo = false // Temporarily disabled
  const canRedo = false // Temporarily disabled
  const undo = () => {} // Temporarily disabled
  const redo = () => {} // Temporarily disabled

  // Initialize with a single default track for mixed media
  useEffect(() => {
    if (timelineStore.tracks.length === 0) {
      // Add default track that can handle all media types
      timelineStore.addTrack({
        type: 'video' as TrackType, // Type is now just cosmetic for color
        name: 'Track 1',
        height: 80,
        locked: false,
        hidden: false,
        muted: false,
        order: 0,
      })

      // Set initial timeline duration (5 minutes at 30fps)
      if (timelineStore.duration === 0) {
        // This will be set automatically when clips are added
        // For now, just initialize the timeline
      }
    }
  }, [])

  const handleAddTrack = () => {
    const trackNumber = timelineStore.tracks.length + 1
    timelineStore.addTrack({
      type: 'video' as TrackType, // Type is now just cosmetic for color
      name: `Track ${trackNumber}`,
      height: 80,
      locked: false,
      hidden: false,
      muted: false,
      order: timelineStore.tracks.length,
    })
  }

  const handleSplitClip = (clipId: string, frame: number) => {
    timelineStore.splitClip(clipId, frame)
  }

  const handleDuplicateClips = (clipIds: string[]) => {
    clipIds.forEach((clipId) => {
      timelineStore.duplicateClip(clipId)
    })
  }

  const handleDeleteClips = (clipIds: string[]) => {
    clipIds.forEach((clipId) => {
      timelineStore.removeClip(clipId)
    })
    // Clear selection after deletion
    timelineStore.clearSelection()
  }

  const handleExport = () => {
    try {
      // Get all clips from the timeline
      const clips = Array.from(timelineStore.clips.values())

      if (clips.length === 0) {
        toast.error('No clips to export', {
          description: 'Add some clips to the timeline before exporting.',
        })
        return
      }

      // Transform clips to the backend format
      const transformedClips = clips.map((clip) => {
        // Get the asset URL from the media store
        const asset = mediaStore.assets.get(clip.assetId)
        if (!asset) {
          throw new Error(`Asset not found for clip ${clip.id}`)
        }

        // Convert frames to seconds
        const fps = timelineStore.fps
        const startTime = clip.startTime / fps
        const duration = clip.duration / fps
        const endTime = startTime + duration
        const trimStart = clip.inPoint / fps

        // trim_end is how many seconds to trim from the END of the source
        // If we have the asset duration, calculate it as: duration - outPoint
        // Otherwise, default to 0 (no trimming from end)
        const trimEnd = asset.duration
          ? Math.max(0, asset.duration - (clip.outPoint / fps))
          : 0

        return {
          video_url: asset.url,
          start_time: startTime,
          end_time: endTime,
          trim_start: trimStart,
          trim_end: trimEnd,
        }
      })

      // Sort clips by start_time
      transformedClips.sort((a, b) => a.start_time - b.start_time)

      // Prepare the payload
      const payload = {
        clips: transformedClips,
        overlays: [],
      }

      // Set the payload and open the dialog
      setExportPayload(payload)
      setIsExportDialogOpen(true)
    } catch (error) {
      console.error('Failed to prepare export:', error)
      toast.error('Failed to prepare export', {
        description: error instanceof Error ? error.message : 'Unknown error occurred',
      })
    }
  }

  const handleConfirmExport = async () => {
    if (!exportPayload) return

    try {
      // Show loading toast
      toast.info('Exporting...', {
        description: 'Sending your composition to the backend.',
      })

      // Send to the backend API
      const response = await api.post('/compositions', exportPayload)

      toast.success('Export started successfully!', {
        description: 'Your video is being processed.',
      })

      console.log('Export response:', response)
    } catch (error) {
      console.error('Export failed:', error)
      toast.error('Export failed', {
        description: error instanceof Error ? error.message : 'Unknown error occurred',
      })
      throw error // Re-throw to let the dialog handle the error state
    }
  }

  // Calculate duration (use stored duration or default to 5 minutes)
  const duration = timelineStore.duration > 0 ? timelineStore.duration : timelineStore.fps * 300 // 5 minutes default

  // Get selected clip
  const selectedClip = timelineStore.selectedClipIds.length === 1
    ? timelineStore.clips.get(timelineStore.selectedClipIds[0])
    : undefined

  // Define keyboard shortcuts
  const shortcuts = useMemo(() => [
    {
      key: 's',
      action: () => {
        // Split clip at playhead
        if (timelineStore.selectedClipIds.length > 0) {
          const clipId = timelineStore.selectedClipIds[0]
          const clip = timelineStore.clips.get(clipId)
          if (clip && timelineStore.playhead >= clip.startTime && timelineStore.playhead < clip.startTime + clip.duration) {
            handleSplitClip(clipId, timelineStore.playhead)
          }
        }
      },
      description: 'Split clip at playhead',
      enabled: timelineStore.selectedClipIds.length > 0,
    },
    {
      key: 'Delete',
      action: () => handleDeleteClips(timelineStore.selectedClipIds),
      description: 'Delete selected clips',
      enabled: timelineStore.selectedClipIds.length > 0,
    },
    {
      key: 'Backspace',
      action: () => handleDeleteClips(timelineStore.selectedClipIds),
      description: 'Delete selected clips',
      enabled: timelineStore.selectedClipIds.length > 0,
    },
    {
      key: 'd',
      ctrl: true,
      action: () => handleDuplicateClips(timelineStore.selectedClipIds),
      description: 'Duplicate selected clips',
      enabled: timelineStore.selectedClipIds.length > 0,
    },
    {
      key: 'a',
      ctrl: true,
      action: () => {
        // Select all clips
        const allClipIds = Array.from(timelineStore.clips.keys())
        allClipIds.forEach((id, index) => {
          timelineStore.selectClip(id, index > 0)
        })
      },
      description: 'Select all clips',
      enabled: timelineStore.clips.size > 0,
    },
    {
      key: 'Escape',
      action: () => timelineStore.clearSelection(),
      description: 'Clear selection',
      enabled: timelineStore.selectedClipIds.length > 0,
    },
    {
      key: 'z',
      ctrl: true,
      action: () => undo(),
      description: 'Undo',
      enabled: canUndo,
    },
    {
      key: 'z',
      ctrl: true,
      shift: true,
      action: () => redo(),
      description: 'Redo',
      enabled: canRedo,
    },
    {
      key: 'y',
      ctrl: true,
      action: () => redo(),
      description: 'Redo',
      enabled: canRedo,
    },
  ], [timelineStore, handleSplitClip, handleDuplicateClips, handleDeleteClips, undo, redo, canUndo, canRedo])

  // Enable keyboard shortcuts
  useKeyboardShortcuts({ shortcuts, enabled: true })

  return (
    <>
      <div className="h-full flex">
        <div className="flex-1 flex flex-col">
          <Timeline
            tracks={timelineStore.tracks}
            clips={timelineStore.clips}
            selectedClipIds={timelineStore.selectedClipIds}
            playhead={timelineStore.playhead}
            zoom={timelineStore.zoom}
            duration={duration}
            fps={timelineStore.fps}
            onPlayheadChange={timelineStore.setPlayhead}
            onZoomChange={timelineStore.setZoom}
            onClipSelect={timelineStore.selectClip}
            onClipMove={timelineStore.moveClip}
            onClipTrim={timelineStore.updateClip}
            onSplitClip={handleSplitClip}
            onDuplicateClips={handleDuplicateClips}
            onDeleteClips={handleDeleteClips}
            onTrackUpdate={timelineStore.updateTrack}
            onAddTrack={handleAddTrack}
            onExport={handleExport}
          />
        </div>

        {/* Clip Properties Panel */}
        {selectedClip && (
          <div className="w-80 flex-shrink-0">
            <ClipPropertiesPanel
              clip={selectedClip}
              fps={timelineStore.fps}
              onUpdate={timelineStore.updateClip}
            />
          </div>
        )}
      </div>

      {/* Export Dialog */}
      <ExportDialog
        open={isExportDialogOpen}
        onOpenChange={setIsExportDialogOpen}
        payload={exportPayload}
        onConfirm={handleConfirmExport}
      />
    </>
  )
}
