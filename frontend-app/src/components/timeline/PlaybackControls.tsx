/**
 * PlaybackControls - Comprehensive playback control component
 *
 * Provides play/pause, scrubbing, frame stepping, speed control, and volume
 * with keyboard shortcuts integration
 */

import React, { useCallback, useEffect, useRef } from 'react'
import { Button } from '../ui/button'
import { useTimelineStore } from '../../contexts/StoreContext'
import { useEditorStore } from '../../contexts/StoreContext'

// Icons (using Unicode symbols for now - can be replaced with icon library)
const PlayIcon = () => <span>▶️</span>
const PauseIcon = () => <span>⏸️</span>
const StepBackIcon = () => <span>⏮️</span>
const StepForwardIcon = () => <span>⏭️</span>
const VolumeIcon = () => <span>🔊</span>
const MuteIcon = () => <span>🔇</span>

export const PlaybackControls: React.FC = () => {
  const { playhead, fps, duration, setPlayhead } = useTimelineStore()
  const { isPlaying, playbackRate, volume, togglePlayback, pause, play, setPlaybackRate, setVolume } = useEditorStore()

  const scrubberRef = useRef<HTMLDivElement>(null)
  const isDraggingRef = useRef(false)

  /**
   * Toggle play/pause
   */
  const handlePlayPause = useCallback(() => {
    togglePlayback()
  }, [togglePlayback])

  /**
   * Step backward one frame
   */
  const handleStepBack = useCallback(() => {
    setPlayhead(Math.max(0, playhead - 1))
  }, [playhead, setPlayhead])

  /**
   * Step forward one frame
   */
  const handleStepForward = useCallback(() => {
    setPlayhead(Math.min(duration, playhead + 1))
  }, [playhead, duration, setPlayhead])

  /**
   * Handle scrubber click/drag
   */
  const handleScrubberMouseDown = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!scrubberRef.current) return

      isDraggingRef.current = true

      // Pause playback while scrubbing
      const wasPlaying = isPlaying
      if (wasPlaying) {
        pause()
      }

      const updatePlayhead = (clientX: number) => {
        if (!scrubberRef.current) return

        const rect = scrubberRef.current.getBoundingClientRect()
        const percent = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width))
        const frame = Math.floor(percent * duration)

        setPlayhead(frame)
      }

      updatePlayhead(e.clientX)

      const handleMouseMove = (moveEvent: MouseEvent) => {
        if (!isDraggingRef.current) return
        updatePlayhead(moveEvent.clientX)
      }

      const handleMouseUp = () => {
        isDraggingRef.current = false
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)

        // Resume playback if it was playing
        if (wasPlaying) {
          play()
        }
      }

      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    },
    [duration, isPlaying, pause, play, setPlayhead]
  )

  /**
   * Handle playback speed change
   */
  const handleSpeedChange = useCallback(
    (speed: number) => {
      setPlaybackRate(speed)
    },
    [setPlaybackRate]
  )

  /**
   * Handle volume change
   */
  const handleVolumeChange = useCallback(
    (newVolume: number) => {
      setVolume(newVolume)
    },
    [setVolume]
  )

  /**
   * Format time display
   */
  const formatTime = (frame: number, fps: number): string => {
    const totalSeconds = frame / fps
    const hours = Math.floor(totalSeconds / 3600)
    const minutes = Math.floor((totalSeconds % 3600) / 60)
    const seconds = Math.floor(totalSeconds % 60)
    const frames = frame % fps

    return `${hours.toString().padStart(2, '0')}:${minutes
      .toString()
      .padStart(2, '0')}:${seconds.toString().padStart(2, '0')}:${frames
      .toString()
      .padStart(2, '0')}`
  }

  /**
   * Keyboard shortcuts
   */
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Only handle if not in input field
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return
      }

      switch (e.key) {
        case ' ':
          e.preventDefault()
          handlePlayPause()
          break

        case 'ArrowLeft':
          e.preventDefault()
          handleStepBack()
          break

        case 'ArrowRight':
          e.preventDefault()
          handleStepForward()
          break

        default:
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handlePlayPause, handleStepBack, handleStepForward])

  const currentTime = formatTime(playhead, fps)
  const totalTime = formatTime(duration, fps)
  const progress = duration > 0 ? (playhead / duration) * 100 : 0

  return (
    <div className="flex items-center gap-3 p-3 bg-zinc-900 border-t border-zinc-800">
      {/* Transport Controls */}
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleStepBack}
          title="Previous Frame (←)"
          className="w-8 h-8 p-0"
        >
          <StepBackIcon />
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={handlePlayPause}
          title="Play/Pause (Space)"
          className="w-10 h-10 p-0"
        >
          {isPlaying ? <PauseIcon /> : <PlayIcon />}
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={handleStepForward}
          title="Next Frame (→)"
          className="w-8 h-8 p-0"
        >
          <StepForwardIcon />
        </Button>
      </div>

      {/* Time Display */}
      <div className="flex items-center gap-2 text-sm font-mono text-zinc-400 min-w-[200px]">
        <span>{currentTime}</span>
        <span>/</span>
        <span>{totalTime}</span>
      </div>

      {/* Scrubber */}
      <div className="flex-1 min-w-[200px]">
        <div
          ref={scrubberRef}
          className="relative h-6 bg-zinc-800 rounded cursor-pointer hover:bg-zinc-750 transition-colors"
          onMouseDown={handleScrubberMouseDown}
        >
          {/* Progress bar */}
          <div
            className="absolute top-0 left-0 h-full bg-blue-500 rounded transition-all"
            style={{ width: `${progress}%` }}
          />

          {/* Playhead indicator */}
          <div
            className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-lg"
            style={{ left: `calc(${progress}% - 6px)` }}
          />
        </div>
      </div>

      {/* Playback Speed */}
      <div className="flex items-center gap-1">
        <span className="text-xs text-zinc-500">Speed:</span>
        <select
          value={playbackRate}
          onChange={(e) => handleSpeedChange(Number(e.target.value))}
          className="bg-zinc-800 text-zinc-300 text-xs px-2 py-1 rounded border border-zinc-700 focus:border-blue-500 outline-none"
        >
          <option value={0.25}>0.25x</option>
          <option value={0.5}>0.5x</option>
          <option value={1}>1x</option>
          <option value={1.5}>1.5x</option>
          <option value={2}>2x</option>
        </select>
      </div>

      {/* Volume Control */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => handleVolumeChange(volume > 0 ? 0 : 0.8)}
          className="text-lg hover:opacity-75 transition-opacity"
        >
          {volume > 0 ? <VolumeIcon /> : <MuteIcon />}
        </button>

        <input
          type="range"
          min="0"
          max="1"
          step="0.01"
          value={volume}
          onChange={(e) => handleVolumeChange(Number(e.target.value))}
          className="w-20 h-1 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
        />
      </div>
    </div>
  )
}
