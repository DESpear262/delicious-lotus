import { useMemo } from 'react'
import {
  framesToPixels,
  framesToTimecode,
  getMarkerInterval,
} from '../../lib/timebase'

interface TimelineRulerProps {
  duration: number // in frames
  fps: number
  zoom: number
  scrollLeft: number
  viewportWidth: number
  playhead: number
  onSeek?: (frame: number) => void
}

export function TimelineRuler({
  duration,
  fps,
  zoom,
  scrollLeft,
  viewportWidth,
  playhead,
  onSeek,
}: TimelineRulerProps) {
  // Track label container width (must match TrackItem header width)
  const TRACK_LABEL_WIDTH = 192 // w-48 in Tailwind = 192px

  // Calculate total width of the timeline in pixels
  const totalWidth = framesToPixels(duration, fps, zoom)

  // Calculate marker interval and positions
  const markers = useMemo(() => {
    const interval = getMarkerInterval(zoom, fps)
    const markerList: Array<{
      frame: number
      position: number
      timecode: string
      isMajor: boolean
    }> = []

    // Determine visible range with some padding
    const startFrame = Math.floor((scrollLeft / (framesToPixels(fps, fps, zoom))) * fps)
    const endFrame = Math.ceil(((scrollLeft + viewportWidth) / (framesToPixels(fps, fps, zoom))) * fps)

    // Calculate the first marker position
    const firstMarker = Math.floor(startFrame / interval) * interval

    for (let frame = firstMarker; frame <= Math.min(endFrame + interval, duration); frame += interval) {
      const position = framesToPixels(frame, fps, zoom)

      // Major markers every 5 intervals or at significant time boundaries
      const isMajor = frame % (interval * 5) === 0 || frame === 0

      markerList.push({
        frame,
        position,
        timecode: framesToTimecode(frame, fps),
        isMajor,
      })
    }

    return markerList
  }, [duration, fps, zoom, scrollLeft, viewportWidth])

  const playheadPosition = framesToPixels(playhead, fps, zoom)

  const handleClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (!onSeek) return

    const rect = event.currentTarget.getBoundingClientRect()
    const clickX = event.clientX - rect.left + scrollLeft - TRACK_LABEL_WIDTH
    const clickedFrame = Math.floor((clickX / totalWidth) * duration)
    onSeek(Math.max(0, Math.min(clickedFrame, duration)))
  }

  return (
    <div className="relative h-12 bg-zinc-900 border-b border-zinc-700 select-none overflow-hidden flex">
      {/* Track label spacer - matches the track header width */}
      <div
        className="flex-shrink-0 h-full bg-zinc-900 border-r border-zinc-700"
        style={{ width: `${TRACK_LABEL_WIDTH}px` }}
      />

      {/* Timeline ruler content */}
      <div
        className="relative flex-1 cursor-pointer"
        onClick={handleClick}
        style={{ width: `${totalWidth}px` }}
      >
        {/* Time markers */}
        {markers.map(({ frame, position, timecode, isMajor }) => (
          <div
            key={`marker-${frame}`}
            className="absolute top-0 bottom-0 flex flex-col items-start"
            style={{ left: `${position}px` }}
          >
            {/* Tick mark */}
            <div
              className={`w-px ${
                isMajor ? 'h-6 bg-zinc-500' : 'h-4 bg-zinc-600'
              }`}
            />

            {/* Timecode label for major markers */}
            {isMajor && (
              <span className="text-[10px] text-zinc-400 ml-1 mt-0.5 font-mono whitespace-nowrap">
                {timecode}
              </span>
            )}
          </div>
        ))}

        {/* Playhead indicator */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-blue-500 pointer-events-none z-10"
          style={{ left: `${playheadPosition}px` }}
        >
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3 h-3 bg-blue-500 rounded-sm" />
        </div>
      </div>
    </div>
  )
}
