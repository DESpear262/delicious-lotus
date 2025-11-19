/**
 * TransformEngine - CSS transform application system for clip animations
 *
 * Handles applying clip transform properties (position, scale, rotation, opacity)
 * to DOM elements with support for smooth interpolation and keyframe animations
 */

import type { Clip } from '../types/stores'

export interface TransformState {
  position: { x: number; y: number }
  scale: { x: number; y: number }
  rotation: number
  opacity: number
}

export interface Keyframe {
  frame: number
  transform: Partial<TransformState>
  easing?: EasingFunction
}

export type EasingFunction = 'linear' | 'easeIn' | 'easeOut' | 'easeInOut'

export class TransformEngine {
  /**
   * Apply transforms from clip properties to a DOM element
   */
  static applyTransforms(
    element: HTMLElement,
    clip: Clip,
    containerWidth: number,
    containerHeight: number,
    useWillChange: boolean = true
  ): void {
    const transforms: string[] = []

    // Position (translate)
    if (clip.position) {
      const x = clip.position.x * containerWidth
      const y = clip.position.y * containerHeight
      transforms.push(`translate(${x}px, ${y}px)`)
    }

    // Scale
    if (clip.scale) {
      transforms.push(`scale(${clip.scale.x}, ${clip.scale.y})`)
    }

    // Rotation
    if (clip.rotation !== undefined && clip.rotation !== 0) {
      transforms.push(`rotate(${clip.rotation}deg)`)
    }

    // Apply combined transform
    element.style.transform = transforms.join(' ')

    // Apply opacity
    element.style.opacity = clip.opacity.toString()

    // Performance optimization
    if (useWillChange) {
      element.style.willChange = 'transform, opacity'
    }

    // Set transform origin for proper rotation/scaling
    element.style.transformOrigin = 'center center'
  }

  /**
   * Calculate interpolated transform between two states
   */
  static interpolateTransforms(
    from: TransformState,
    to: TransformState,
    progress: number, // 0-1
    easing: EasingFunction = 'linear'
  ): TransformState {
    const t = this.applyEasing(progress, easing)

    return {
      position: {
        x: this.lerp(from.position.x, to.position.x, t),
        y: this.lerp(from.position.y, to.position.y, t),
      },
      scale: {
        x: this.lerp(from.scale.x, to.scale.x, t),
        y: this.lerp(from.scale.y, to.scale.y, t),
      },
      rotation: this.lerp(from.rotation, to.rotation, t),
      opacity: this.lerp(from.opacity, to.opacity, t),
    }
  }

  /**
   * Get transform state at a specific frame with keyframe support
   */
  static getTransformAtFrame(clip: Clip, frame: number, keyframes?: Keyframe[]): TransformState {
    // If no keyframes, return clip's base transform
    if (!keyframes || keyframes.length === 0) {
      return {
        position: clip.position || { x: 0, y: 0 },
        scale: clip.scale || { x: 1, y: 1 },
        rotation: clip.rotation || 0,
        opacity: clip.opacity,
      }
    }

    // Sort keyframes by frame
    const sortedKeyframes = [...keyframes].sort((a, b) => a.frame - b.frame)

    // Find surrounding keyframes
    let beforeKeyframe: Keyframe | null = null
    let afterKeyframe: Keyframe | null = null

    for (let i = 0; i < sortedKeyframes.length; i++) {
      const kf = sortedKeyframes[i]

      if (kf.frame <= frame) {
        beforeKeyframe = kf
      }

      if (kf.frame >= frame && !afterKeyframe) {
        afterKeyframe = kf
        break
      }
    }

    // Get base transform
    const baseTransform: TransformState = {
      position: clip.position || { x: 0, y: 0 },
      scale: clip.scale || { x: 1, y: 1 },
      rotation: clip.rotation || 0,
      opacity: clip.opacity,
    }

    // If frame is before first keyframe, use base transform
    if (!beforeKeyframe && !afterKeyframe) {
      return baseTransform
    }

    // If exactly on a keyframe, use that keyframe
    if (beforeKeyframe && beforeKeyframe.frame === frame) {
      return this.mergeTransforms(baseTransform, beforeKeyframe.transform)
    }

    // If between keyframes, interpolate
    if (beforeKeyframe && afterKeyframe && beforeKeyframe !== afterKeyframe) {
      const duration = afterKeyframe.frame - beforeKeyframe.frame
      const progress = (frame - beforeKeyframe.frame) / duration

      const fromTransform = this.mergeTransforms(baseTransform, beforeKeyframe.transform)
      const toTransform = this.mergeTransforms(baseTransform, afterKeyframe.transform)

      return this.interpolateTransforms(
        fromTransform,
        toTransform,
        progress,
        afterKeyframe.easing
      )
    }

    // Use the closest keyframe
    const closestKeyframe = beforeKeyframe || afterKeyframe
    return this.mergeTransforms(baseTransform, closestKeyframe!.transform)
  }

  /**
   * Apply transition effect (fade, etc.)
   */
  static applyTransition(
    element: HTMLElement,
    clip: Clip,
    currentFrame: number
  ): void {
    let additionalOpacity = 1

    // Fade in transition
    if (clip.transitionIn) {
      const transitionStart = clip.startTime
      const transitionEnd = transitionStart + clip.transitionIn.duration

      if (currentFrame >= transitionStart && currentFrame < transitionEnd) {
        const progress = (currentFrame - transitionStart) / clip.transitionIn.duration
        additionalOpacity *= this.calculateTransitionOpacity(clip.transitionIn.type, progress)
      }
    }

    // Fade out transition
    if (clip.transitionOut) {
      const clipEnd = clip.startTime + clip.duration
      const transitionStart = clipEnd - clip.transitionOut.duration

      if (currentFrame >= transitionStart && currentFrame < clipEnd) {
        const progress = (currentFrame - transitionStart) / clip.transitionOut.duration
        additionalOpacity *= this.calculateTransitionOpacity(
          clip.transitionOut.type,
          1 - progress // Reverse for fade out
        )
      }
    }

    // Apply combined opacity
    const finalOpacity = clip.opacity * additionalOpacity
    element.style.opacity = finalOpacity.toString()
  }

  /**
   * Calculate opacity for transition effects
   */
  private static calculateTransitionOpacity(type: string, progress: number): number {
    switch (type) {
      case 'fade':
        return progress

      case 'crossDissolve':
        return progress

      case 'wipeLeft':
      case 'wipeRight':
      case 'wipeUp':
      case 'wipeDown':
        // For wipes, opacity is binary based on progress
        return progress > 0.5 ? 1 : 0

      default:
        return progress
    }
  }

  /**
   * Linear interpolation helper
   */
  private static lerp(start: number, end: number, t: number): number {
    return start + (end - start) * t
  }

  /**
   * Apply easing function to progress value
   */
  private static applyEasing(t: number, easing: EasingFunction): number {
    switch (easing) {
      case 'linear':
        return t

      case 'easeIn':
        return t * t

      case 'easeOut':
        return t * (2 - t)

      case 'easeInOut':
        return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t

      default:
        return t
    }
  }

  /**
   * Merge partial transform with base transform
   */
  private static mergeTransforms(
    base: TransformState,
    partial: Partial<TransformState>
  ): TransformState {
    return {
      position: partial.position || base.position,
      scale: partial.scale || base.scale,
      rotation: partial.rotation !== undefined ? partial.rotation : base.rotation,
      opacity: partial.opacity !== undefined ? partial.opacity : base.opacity,
    }
  }

  /**
   * Create transform matrix for advanced animations
   */
  static createTransformMatrix(transform: TransformState): string {
    // For now, use simple transforms
    // Can be enhanced with matrix3d for complex animations
    const transforms: string[] = []

    transforms.push(`translate(${transform.position.x}px, ${transform.position.y}px)`)
    transforms.push(`scale(${transform.scale.x}, ${transform.scale.y})`)
    transforms.push(`rotate(${transform.rotation}deg)`)

    return transforms.join(' ')
  }

  /**
   * Batch update multiple elements (optimization)
   */
  static batchApplyTransforms(
    updates: Array<{ element: HTMLElement; clip: Clip }>,
    containerWidth: number,
    containerHeight: number
  ): void {
    // Use requestAnimationFrame for batched updates
    requestAnimationFrame(() => {
      updates.forEach(({ element, clip }) => {
        this.applyTransforms(element, clip, containerWidth, containerHeight)
      })
    })
  }

  /**
   * Remove will-change optimization (call when animation is done)
   */
  static removeOptimizations(element: HTMLElement): void {
    element.style.willChange = 'auto'
  }
}
