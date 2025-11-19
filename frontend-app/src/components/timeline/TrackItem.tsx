import { Lock, LockOpen, Eye, EyeOff, Volume2, VolumeX, Trash2 } from 'lucide-react'
import type { Track, Clip, MediaAsset } from '../../types/stores'
import { framesToPixels, pixelsToFrames } from '../../lib/timebase'
import { ClipRenderer } from './ClipRenderer'
import { memo, useState, useCallback } from 'react'
import { useMediaStore } from '../../contexts/StoreContext'

interface TrackItemProps {
  track: Track
  clips: Clip[]
  selectedClipIds: string[]
  fps: number
  zoom: number
  duration: number
  playhead: number
  scrollLeft: number
  allClips?: Map<string, Clip>
  onClipSelect?: (clipId: string, addToSelection: boolean) => void
  onClipMove?: (clipId: string, trackId: string, startTime: number) => void
  onClipTrim?: (clipId: string, updates: Partial<Clip>) => void
  onTrackUpdate?: (trackId: string, updates: Partial<Track>) => void
  onAssetDrop?: (asset: MediaAsset, trackId: string, startFrame: number) => void
  onDeleteTrack?: (trackId: string) => void
}

export const TrackItem = memo(function TrackItem({
  track,
  clips,
  selectedClipIds,
  fps,
  zoom,
  duration,
  playhead,
  allClips,
  scrollLeft,
  onClipSelect,
  onClipMove,
  onClipTrim,
  onTrackUpdate,
  onAssetDrop,
  onDeleteTrack,
}: TrackItemProps) {
  const mediaAssets = useMediaStore((state) => state.assets)
  const totalWidth = framesToPixels(duration, fps, zoom)
  const [isDragOver, setIsDragOver] = useState(false)

  const handleToggleLock = () => {
    onTrackUpdate?.(track.id, { locked: !track.locked })
  }

  const handleToggleHidden = () => {
    onTrackUpdate?.(track.id, { hidden: !track.hidden })
  }

  const handleToggleMuted = () => {
    if (track.type === 'audio') {
      onTrackUpdate?.(track.id, { muted: !track.muted })
    }
  }

  const handleDeleteTrack = () => {
    if (window.confirm(`Are you sure you want to delete "${track.name}"? This will also delete all clips on this track.`)) {
      onDeleteTrack?.(track.id)
    }
  }

  // Drag and drop handlers for media assets
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    e.dataTransfer.dropEffect = 'copy'
    setIsDragOver(true)
    console.log('Drag over track:', track.id)
  }, [track.id])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)

    console.log('Drop event triggered on track:', track.id)

    const rawJson = e.dataTransfer.getData('application/json')
    const rawText = e.dataTransfer.getData('text/plain')

    try {
      const assetData = rawJson || rawText
      console.log('Asset data from dataTransfer:', assetData)

      let asset: MediaAsset | undefined
      let assetId: string | undefined

      if (assetData) {
        try {
          const parsedAsset = JSON.parse(assetData)
          assetId = parsedAsset.id
          console.log('Parsed asset ID from dataTransfer:', assetId)
        } catch (parseError) {
          console.warn('Failed to parse dropped asset JSON:', parseError)
          // Try using rawText as asset ID directly
          assetId = rawText
        }
      }

      // ALWAYS look up asset from store to get latest metadata (including client-extracted duration)
      if (assetId) {
        const storeAsset = mediaAssets.get(assetId)
        if (storeAsset) {
          console.log('Retrieved asset from store with latest metadata:', {
            id: storeAsset.id,
            name: storeAsset.name,
            duration: storeAsset.duration,
            metadata: storeAsset.metadata,
          })
          asset = storeAsset
        } else {
          console.warn('Asset not found in store:', assetId)
        }
      }

      if (!asset) {
        console.log('No asset data found')
        return
      }

      // Calculate drop position in frames
      const rect = e.currentTarget.getBoundingClientRect()
      const x = e.clientX - rect.left + scrollLeft
      const startFrame = pixelsToFrames(x, fps, zoom)

      console.log('Drop position:', { x, startFrame, rect })

      onAssetDrop?.(asset, track.id, Math.max(0, Math.round(startFrame)))
    } catch (error) {
      console.error('Failed to parse dropped asset:', error)
    }
  }, [track.id, fps, zoom, scrollLeft, onAssetDrop, mediaAssets])

  // Track type icon color
  const trackColor = track.color || (
    track.type === 'video' ? 'bg-purple-600' :
    track.type === 'audio' ? 'bg-green-600' :
    'bg-blue-600'
  )

  return (
    <div
      className="flex border-b border-zinc-700"
      style={{ height: `${track.height}px` }}
    >
      {/* Track header */}
      <div className="w-48 flex-shrink-0 bg-zinc-900 border-r border-zinc-700 p-2 flex flex-col justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-1 h-full ${trackColor} rounded-full`} />
          <div className="flex-1 min-w-0">
            <div className="text-xs font-medium text-zinc-200 truncate">
              {track.name}
            </div>
            <div className="text-[10px] text-zinc-500 uppercase">
              Mixed Media
            </div>
          </div>
        </div>

        {/* Track controls */}
        <div className="flex items-center justify-between gap-1 mt-2">
          <div className="flex items-center gap-1">
            <button
              onClick={handleToggleLock}
              className="p-1 hover:bg-zinc-800 rounded transition-colors"
              title={track.locked ? 'Unlock track' : 'Lock track'}
            >
              {track.locked ? (
                <Lock className="w-3 h-3 text-zinc-400" />
              ) : (
                <LockOpen className="w-3 h-3 text-zinc-500" />
              )}
            </button>

            <button
              onClick={handleToggleHidden}
              className="p-1 hover:bg-zinc-800 rounded transition-colors"
              title={track.hidden ? 'Show track' : 'Hide track'}
            >
              {track.hidden ? (
                <EyeOff className="w-3 h-3 text-zinc-400" />
              ) : (
                <Eye className="w-3 h-3 text-zinc-500" />
              )}
            </button>

            {track.type === 'audio' && (
              <button
                onClick={handleToggleMuted}
                className="p-1 hover:bg-zinc-800 rounded transition-colors"
                title={track.muted ? 'Unmute track' : 'Mute track'}
              >
                {track.muted ? (
                  <VolumeX className="w-3 h-3 text-zinc-400" />
                ) : (
                  <Volume2 className="w-3 h-3 text-zinc-500" />
                )}
              </button>
            )}
          </div>

          {/* Delete button in bottom right corner */}
          {onDeleteTrack && (
            <button
              onClick={handleDeleteTrack}
              className="p-1 hover:bg-red-900/50 rounded transition-colors"
              title="Delete track"
            >
              <Trash2 className="w-3 h-3 text-red-400 hover:text-red-300" />
            </button>
          )}
        </div>
      </div>

      {/* Track content area */}
      <div
        className={`flex-1 relative bg-zinc-950 overflow-hidden transition-colors ${
          isDragOver ? 'bg-blue-950/30 ring-2 ring-blue-500 ring-inset' : ''
        }`}
        onDragOver={handleDragOver}
        onDragEnter={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        style={{ minHeight: '60px' }}
      >
        <div
          className="absolute inset-0"
          style={{ width: `${totalWidth}px` }}
        >
          {/* Render clips */}
          {clips.map((clip) => (
            <ClipRenderer
              key={clip.id}
              clip={clip}
              isSelected={selectedClipIds.includes(clip.id)}
              fps={fps}
              zoom={zoom}
              trackHeight={track.height}
              trackType={track.type}
              isLocked={track.locked}
              trackId={track.id}
              allClips={allClips}
              playhead={playhead}
              onSelect={onClipSelect}
              onMove={onClipMove}
              onTrim={onClipTrim}
            />
          ))}

          {/* Playhead line */}
          <div
            className="absolute top-0 bottom-0 w-px bg-blue-500 pointer-events-none"
            style={{ left: `${framesToPixels(playhead, fps, zoom)}px` }}
          />
        </div>
      </div>
    </div>
  )
})
