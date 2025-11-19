/**
 * Snapping Utilities
 * Handles magnetic snapping for timeline clips
 */

import type { Clip } from '../types/stores'

export interface SnapTarget {
  frame: number
  type: 'clip-start' | 'clip-end' | 'playhead' | 'marker'
  clipId?: string
}

export interface SnapResult {
  snapped: boolean
  snapFrame: number
  originalFrame: number
  snapTarget?: SnapTarget
}

/**
 * Default snap threshold in frames (about 5-10 pixels at 1x zoom)
 */
export const DEFAULT_SNAP_THRESHOLD = 5

/**
 * Finds all potential snap targets from clips, playhead, and markers
 */
export function getSnapTargets(
  clips: Map<string, Clip>,
  playhead: number,
  excludeClipIds: string[] = [],
  markers: number[] = []
): SnapTarget[] {
  const targets: SnapTarget[] = []

  // Add playhead as snap target
  targets.push({
    frame: playhead,
    type: 'playhead',
  })

  // Add markers as snap targets
  markers.forEach((markerFrame) => {
    targets.push({
      frame: markerFrame,
      type: 'marker',
    })
  })

  // Add clip boundaries as snap targets
  clips.forEach((clip) => {
    if (!excludeClipIds.includes(clip.id)) {
      // Clip start
      targets.push({
        frame: clip.startTime,
        type: 'clip-start',
        clipId: clip.id,
      })

      // Clip end
      targets.push({
        frame: clip.startTime + clip.duration,
        type: 'clip-end',
        clipId: clip.id,
      })
    }
  })

  return targets
}

/**
 * Snaps a frame value to the nearest snap target within threshold
 */
export function snapToTarget(
  frame: number,
  targets: SnapTarget[],
  threshold: number = DEFAULT_SNAP_THRESHOLD
): SnapResult {
  let closestTarget: SnapTarget | undefined
  let closestDistance = Infinity

  // Find the closest snap target within threshold
  for (const target of targets) {
    const distance = Math.abs(target.frame - frame)

    if (distance < closestDistance && distance <= threshold) {
      closestDistance = distance
      closestTarget = target
    }
  }

  // Return snap result
  if (closestTarget) {
    return {
      snapped: true,
      snapFrame: closestTarget.frame,
      originalFrame: frame,
      snapTarget: closestTarget,
    }
  }

  return {
    snapped: false,
    snapFrame: frame,
    originalFrame: frame,
  }
}

/**
 * Snaps a clip's position considering both start and end points
 */
export function snapClipPosition(
  clipStartFrame: number,
  clipDuration: number,
  targets: SnapTarget[],
  threshold: number = DEFAULT_SNAP_THRESHOLD
): SnapResult {
  const clipEndFrame = clipStartFrame + clipDuration

  // Try snapping the start point
  const startSnap = snapToTarget(clipStartFrame, targets, threshold)

  // Try snapping the end point
  const endSnap = snapToTarget(clipEndFrame, targets, threshold)

  // Prefer the snap with the smallest distance
  if (startSnap.snapped && endSnap.snapped) {
    const startDistance = Math.abs(startSnap.snapFrame - clipStartFrame)
    const endDistance = Math.abs(endSnap.snapFrame - clipEndFrame)

    if (startDistance <= endDistance) {
      return startSnap
    } else {
      // Adjust the snap frame to account for end point snapping
      return {
        ...endSnap,
        snapFrame: endSnap.snapFrame - clipDuration,
      }
    }
  } else if (startSnap.snapped) {
    return startSnap
  } else if (endSnap.snapped) {
    return {
      ...endSnap,
      snapFrame: endSnap.snapFrame - clipDuration,
    }
  }

  return {
    snapped: false,
    snapFrame: clipStartFrame,
    originalFrame: clipStartFrame,
  }
}
