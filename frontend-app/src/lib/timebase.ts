/**
 * Timebase Calculation Utilities
 * Handles conversion between frames, time, and pixels for timeline rendering
 */

export interface TimebaseConfig {
  fps: number
  pixelsPerSecond: number
}

/**
 * Converts frames to seconds
 */
export function framesToSeconds(frames: number, fps: number): number {
  return frames / fps
}

/**
 * Converts seconds to frames
 */
export function secondsToFrames(seconds: number, fps: number): number {
  return Math.floor(seconds * fps)
}

/**
 * Converts frames to SMPTE timecode string (HH:MM:SS:FF)
 */
export function framesToTimecode(frames: number, fps: number): string {
  const totalSeconds = Math.floor(frames / fps)
  const frameRemainder = frames % fps

  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60

  const pad = (num: number, length: number = 2) =>
    num.toString().padStart(length, '0')

  return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}:${pad(frameRemainder)}`
}

/**
 * Converts timecode string to frames
 */
export function timecodeToFrames(timecode: string, fps: number): number {
  const parts = timecode.split(':').map(Number)
  if (parts.length !== 4) return 0

  const [hours, minutes, seconds, frames] = parts
  return (hours * 3600 + minutes * 60 + seconds) * fps + frames
}

/**
 * Converts frames to pixels based on zoom level
 */
export function framesToPixels(
  frames: number,
  fps: number,
  zoom: number
): number {
  const basePixelsPerSecond = 100 // base scale at 1x zoom
  const pixelsPerSecond = basePixelsPerSecond * zoom
  const seconds = framesToSeconds(frames, fps)
  return seconds * pixelsPerSecond
}

/**
 * Converts pixels to frames based on zoom level
 */
export function pixelsToFrames(
  pixels: number,
  fps: number,
  zoom: number
): number {
  const basePixelsPerSecond = 100
  const pixelsPerSecond = basePixelsPerSecond * zoom
  const seconds = pixels / pixelsPerSecond
  return secondsToFrames(seconds, fps)
}

/**
 * Calculates the interval between time markers based on zoom level
 * Returns interval in frames
 */
export function getMarkerInterval(zoom: number, fps: number): number {
  // Adjust marker density based on zoom
  if (zoom >= 4) {
    return fps / 2 // Every half second at high zoom
  } else if (zoom >= 2) {
    return fps // Every second
  } else if (zoom >= 1) {
    return fps * 5 // Every 5 seconds
  } else if (zoom >= 0.5) {
    return fps * 10 // Every 10 seconds
  } else {
    return fps * 30 // Every 30 seconds
  }
}

/**
 * Snaps a frame value to the nearest frame boundary
 */
export function snapToFrame(frame: number): number {
  return Math.round(frame)
}

/**
 * Snaps a pixel value to the nearest frame based on zoom
 */
export function snapPixelToFrame(
  pixels: number,
  fps: number,
  zoom: number
): number {
  const frame = pixelsToFrames(pixels, fps, zoom)
  return snapToFrame(frame)
}

/**
 * Calculates visible time range based on scroll position and viewport width
 */
export function getVisibleTimeRange(
  scrollLeft: number,
  viewportWidth: number,
  fps: number,
  zoom: number
): { startFrame: number; endFrame: number } {
  const startFrame = pixelsToFrames(scrollLeft, fps, zoom)
  const endFrame = pixelsToFrames(scrollLeft + viewportWidth, fps, zoom)

  return {
    startFrame: Math.floor(startFrame),
    endFrame: Math.ceil(endFrame),
  }
}

/**
 * Formats duration in a human-readable format
 */
export function formatDuration(frames: number, fps: number): string {
  const totalSeconds = Math.floor(frames / fps)

  if (totalSeconds < 60) {
    return `${totalSeconds}s`
  }

  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60

  if (totalSeconds < 3600) {
    return seconds > 0 ? `${minutes}m ${seconds}s` : `${minutes}m`
  }

  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60

  return `${hours}h ${remainingMinutes}m`
}
