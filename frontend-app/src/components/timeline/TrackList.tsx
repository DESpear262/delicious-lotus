import type { Track, Clip, MediaAsset } from '../../types/stores'
import { TrackItem } from './TrackItem'
import { Plus } from 'lucide-react'
import { Button } from '../ui/button'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../ui/tooltip'

interface TrackListProps {
  tracks: Track[]
  clips: Map<string, Clip>
  selectedClipIds: string[]
  fps: number
  zoom: number
  duration: number
  playhead: number
  scrollLeft: number
  onClipSelect?: (clipId: string, addToSelection: boolean) => void
  onClipMove?: (clipId: string, trackId: string, startTime: number) => void
  onClipTrim?: (clipId: string, updates: Partial<Clip>) => void
  onTrackUpdate?: (trackId: string, updates: Partial<Track>) => void
  onAssetDrop?: (asset: MediaAsset, trackId: string, startFrame: number) => void
  onAddTrack?: () => void
  onDeleteTrack?: (trackId: string) => void
}

export function TrackList({
  tracks,
  clips,
  selectedClipIds,
  fps,
  zoom,
  duration,
  playhead,
  scrollLeft,
  onClipSelect,
  onClipMove,
  onClipTrim,
  onTrackUpdate,
  onAssetDrop,
  onAddTrack,
  onDeleteTrack,
}: TrackListProps) {
  // Get clips for a specific track
  const getClipsForTrack = (trackId: string): Clip[] => {
    const trackClips: Clip[] = []
    clips.forEach((clip) => {
      if (clip.trackId === trackId) {
        trackClips.push(clip)
      }
    })
    return trackClips.sort((a, b) => a.startTime - b.startTime)
  }

  if (tracks.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-zinc-500">
        No tracks yet. Add a track to get started.
      </div>
    )
  }

  return (
    <div className="flex flex-col relative">
      {tracks.map((track) => {
        const trackClips = getClipsForTrack(track.id)

        return (
          <TrackItem
            key={track.id}
            track={track}
            clips={trackClips}
            selectedClipIds={selectedClipIds}
            fps={fps}
            zoom={zoom}
            duration={duration}
            playhead={playhead}
            scrollLeft={scrollLeft}
            allClips={clips}
            onClipSelect={onClipSelect}
            onClipMove={onClipMove}
            onClipTrim={onClipTrim}
            onTrackUpdate={onTrackUpdate}
            onAssetDrop={onAssetDrop}
            onDeleteTrack={onDeleteTrack}
          />
        )
      })}

      {/* Floating Add Track Button */}
      {onAddTrack && (
        <div className="sticky bottom-4 right-4 flex justify-end pr-4 pb-4 pointer-events-none">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  onClick={onAddTrack}
                  size="sm"
                  className="h-10 w-10 rounded-full bg-blue-500 hover:bg-blue-600 text-white shadow-lg pointer-events-auto"
                >
                  <Plus className="w-5 h-5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="left">
                <p>Add Track</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      )}
    </div>
  )
}
