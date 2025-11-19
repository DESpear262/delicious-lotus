import { useRef, useState, useCallback, useEffect } from 'react'
import { TimelineRuler } from './TimelineRuler'
import { TrackList } from './TrackList'
import { TimelineToolbar } from './TimelineToolbar'
import type { Track, Clip, MediaAsset } from '../../types/stores'

interface TimelineProps {
  tracks: Track[]
  clips: Map<string, Clip>
  selectedClipIds: string[]
  playhead: number
  zoom: number
  duration: number
  fps: number
  onPlayheadChange: (frame: number) => void
  onZoomChange: (zoom: number) => void
  onClipSelect?: (clipId: string, addToSelection: boolean) => void
  onClipMove?: (clipId: string, trackId: string, startTime: number) => void
  onClipTrim?: (clipId: string, updates: Partial<Clip>) => void
  onSplitClip?: (clipId: string, frame: number) => void
  onDuplicateClips?: (clipIds: string[]) => void
  onDeleteClips?: (clipIds: string[]) => void
  onTrackUpdate?: (trackId: string, updates: Partial<Track>) => void
  onAddTrack?: () => void
  onDeleteTrack?: (trackId: string) => void
  onAssetDrop?: (asset: MediaAsset, trackId: string, startFrame: number) => void
  onExport?: () => void
}

export function Timeline({
  tracks,
  clips,
  selectedClipIds,
  playhead,
  zoom,
  duration,
  fps,
  onPlayheadChange,
  onZoomChange,
  onClipSelect,
  onClipMove,
  onClipTrim,
  onSplitClip,
  onDuplicateClips,
  onDeleteClips,
  onTrackUpdate,
  onAddTrack,
  onDeleteTrack,
  onAssetDrop,
  onExport,
}: TimelineProps) {
  const rulerScrollRef = useRef<HTMLDivElement>(null)
  const tracksScrollRef = useRef<HTMLDivElement>(null)
  const [scrollLeft, setScrollLeft] = useState(0)
  const [viewportWidth, setViewportWidth] = useState(0)

  // Synchronize horizontal scrolling between ruler and tracks
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const target = e.target as HTMLDivElement
    const newScrollLeft = target.scrollLeft

    setScrollLeft(newScrollLeft)

    // Sync the other scroll container
    if (target === rulerScrollRef.current && tracksScrollRef.current) {
      tracksScrollRef.current.scrollLeft = newScrollLeft
    } else if (target === tracksScrollRef.current && rulerScrollRef.current) {
      rulerScrollRef.current.scrollLeft = newScrollLeft
    }
  }, [])

  // Update viewport width on resize
  useEffect(() => {
    const updateViewportWidth = () => {
      if (tracksScrollRef.current) {
        setViewportWidth(tracksScrollRef.current.clientWidth)
      }
    }

    updateViewportWidth()
    window.addEventListener('resize', updateViewportWidth)
    return () => window.removeEventListener('resize', updateViewportWidth)
  }, [])

  // Toolbar handlers
  const handleSplitAtPlayhead = useCallback(() => {
    if (selectedClipIds.length === 0) return

    // Split first selected clip at playhead position
    const clipId = selectedClipIds[0]
    const clip = clips.get(clipId)

    if (clip && playhead >= clip.startTime && playhead < clip.startTime + clip.duration) {
      onSplitClip?.(clipId, playhead)
    }
  }, [selectedClipIds, clips, playhead, onSplitClip])

  const handleDuplicateClips = useCallback(() => {
    if (selectedClipIds.length > 0) {
      onDuplicateClips?.(selectedClipIds)
    }
  }, [selectedClipIds, onDuplicateClips])

  const handleDeleteClips = useCallback(() => {
    if (selectedClipIds.length > 0) {
      onDeleteClips?.(selectedClipIds)
    }
  }, [selectedClipIds, onDeleteClips])

  return (
    <div className="flex flex-col h-full w-full bg-zinc-950 border-t border-zinc-700">
      {/* Timeline toolbar */}
      <TimelineToolbar
        hasSelection={selectedClipIds.length > 0}
        zoom={zoom}
        onZoomChange={onZoomChange}
        onSplitAtPlayhead={handleSplitAtPlayhead}
        onDuplicateClips={handleDuplicateClips}
        onDeleteClips={handleDeleteClips}
        onExport={onExport}
      />

      {/* Timeline ruler (scrollable horizontally) */}
      <div
        ref={rulerScrollRef}
        className="overflow-x-auto overflow-y-hidden scrollbar-thin"
        onScroll={handleScroll}
      >
        <TimelineRuler
          duration={duration}
          fps={fps}
          zoom={zoom}
          scrollLeft={scrollLeft}
          viewportWidth={viewportWidth}
          playhead={playhead}
          onSeek={onPlayheadChange}
        />
      </div>

      {/* Timeline tracks (scrollable both directions) */}
      <div
        ref={tracksScrollRef}
        className="flex-1 overflow-auto scrollbar-thin"
        onScroll={handleScroll}
      >
        <div className="min-h-full">
          <TrackList
            tracks={tracks}
            clips={clips}
            selectedClipIds={selectedClipIds}
            fps={fps}
            zoom={zoom}
            duration={duration}
            playhead={playhead}
            scrollLeft={scrollLeft}
            onClipSelect={onClipSelect}
            onClipMove={onClipMove}
            onClipTrim={onClipTrim}
            onTrackUpdate={onTrackUpdate}
            onAssetDrop={onAssetDrop}
            onAddTrack={onAddTrack}
            onDeleteTrack={onDeleteTrack}
          />
        </div>
      </div>

      {/* Custom scrollbar styles */}
      <style>{`
        .scrollbar-thin::-webkit-scrollbar {
          height: 8px;
          width: 8px;
        }
        .scrollbar-thin::-webkit-scrollbar-track {
          background: rgb(24 24 27); /* zinc-950 */
        }
        .scrollbar-thin::-webkit-scrollbar-thumb {
          background: rgb(63 63 70); /* zinc-700 */
          border-radius: 4px;
        }
        .scrollbar-thin::-webkit-scrollbar-thumb:hover {
          background: rgb(82 82 91); /* zinc-600 */
        }
      `}</style>
    </div>
  )
}
