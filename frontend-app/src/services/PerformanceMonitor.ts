/**
 * PerformanceMonitor - Performance optimization and monitoring
 *
 * Ensures sub-100ms interaction response times through debouncing,
 * throttling, and performance profiling
 */

export interface PerformanceProfile {
  operation: string
  startTime: number
  endTime?: number
  duration?: number
}

export interface InteractionMetrics {
  operation: string
  responseTime: number
  timestamp: number
}

export class PerformanceMonitor {
  private profiles: Map<string, PerformanceProfile> = new Map()
  private interactionMetrics: InteractionMetrics[] = []
  private maxMetrics: number = 100

  // Performance thresholds (milliseconds)
  private readonly INTERACTION_THRESHOLD = 100
  private readonly WARNING_THRESHOLD = 80

  /**
   * Start profiling an operation
   */
  startProfile(operation: string): void {
    this.profiles.set(operation, {
      operation,
      startTime: performance.now(),
    })
  }

  /**
   * End profiling an operation and log metrics
   */
  endProfile(operation: string): number | null {
    const profile = this.profiles.get(operation)
    if (!profile) {
      console.warn(`No profile found for operation: ${operation}`)
      return null
    }

    const endTime = performance.now()
    const duration = endTime - profile.startTime

    profile.endTime = endTime
    profile.duration = duration

    // Store interaction metric
    this.recordInteraction(operation, duration)

    // Warn if exceeds threshold
    if (duration > this.INTERACTION_THRESHOLD) {
      console.warn(
        `⚠️ Performance warning: ${operation} took ${duration.toFixed(2)}ms (threshold: ${this.INTERACTION_THRESHOLD}ms)`
      )
    } else if (duration > this.WARNING_THRESHOLD) {
      console.log(
        `⚡ Performance notice: ${operation} took ${duration.toFixed(2)}ms (approaching threshold)`
      )
    }

    this.profiles.delete(operation)
    return duration
  }

  /**
   * Record an interaction metric
   */
  private recordInteraction(operation: string, responseTime: number): void {
    this.interactionMetrics.push({
      operation,
      responseTime,
      timestamp: Date.now(),
    })

    // Keep only recent metrics
    if (this.interactionMetrics.length > this.maxMetrics) {
      this.interactionMetrics.shift()
    }
  }

  /**
   * Get average response time for an operation
   */
  getAverageResponseTime(operation: string): number {
    const metrics = this.interactionMetrics.filter((m) => m.operation === operation)

    if (metrics.length === 0) return 0

    const sum = metrics.reduce((acc, m) => acc + m.responseTime, 0)
    return sum / metrics.length
  }

  /**
   * Get all metrics
   */
  getAllMetrics(): InteractionMetrics[] {
    return [...this.interactionMetrics]
  }

  /**
   * Check if response time is within threshold
   */
  isWithinThreshold(operation: string): boolean {
    const avgTime = this.getAverageResponseTime(operation)
    return avgTime < this.INTERACTION_THRESHOLD
  }

  /**
   * Debounce function - delays execution until after delay ms have passed
   * since the last call. Useful for expensive operations triggered by rapid events.
   */
  static debounce<T extends (...args: any[]) => any>(
    func: T,
    delay: number = 100
  ): (...args: Parameters<T>) => void {
    let timeoutId: ReturnType<typeof setTimeout> | null = null

    return function debounced(...args: Parameters<T>) {
      if (timeoutId !== null) {
        clearTimeout(timeoutId)
      }

      timeoutId = setTimeout(() => {
        func(...args)
        timeoutId = null
      }, delay)
    }
  }

  /**
   * Throttle function - ensures function is called at most once per interval.
   * Useful for high-frequency events like scroll or mousemove.
   */
  static throttle<T extends (...args: any[]) => any>(
    func: T,
    interval: number = 100
  ): (...args: Parameters<T>) => void {
    let lastCall = 0

    return function throttled(...args: Parameters<T>) {
      const now = Date.now()

      if (now - lastCall >= interval) {
        lastCall = now
        func(...args)
      }
    }
  }

  /**
   * RequestIdleCallback wrapper for non-critical updates
   */
  static runWhenIdle(callback: () => void, options?: IdleRequestOptions): number {
    const win = window as any
    if ('requestIdleCallback' in win) {
      return win.requestIdleCallback(callback, options)
    } else {
      // Fallback to setTimeout
      return win.setTimeout(callback, 1)
    }
  }

  /**
   * Cancel idle callback
   */
  static cancelIdle(id: number): void {
    const win = window as any
    if ('cancelIdleCallback' in win) {
      win.cancelIdleCallback(id)
    } else {
      win.clearTimeout(id)
    }
  }

  /**
   * Batch DOM reads to minimize layout thrashing
   */
  static batchDOMReads<T>(reads: Array<() => T>): T[] {
    return reads.map((read) => read())
  }

  /**
   * Batch DOM writes to minimize layout thrashing
   */
  static batchDOMWrites(writes: Array<() => void>): void {
    requestAnimationFrame(() => {
      writes.forEach((write) => write())
    })
  }

  /**
   * Measure layout shift (for debugging layout thrashing)
   */
  static measureLayout(element: HTMLElement): DOMRect {
    return element.getBoundingClientRect()
  }

  /**
   * Optimize heavy computations with memoization
   */
  static memoize<T extends (...args: any[]) => any>(
    func: T,
    maxCacheSize: number = 100
  ): T {
    const cache = new Map<string, ReturnType<T>>()

    return ((...args: Parameters<T>): ReturnType<T> => {
      const key = JSON.stringify(args)

      if (cache.has(key)) {
        return cache.get(key)!
      }

      const result = func(...args)

      // Implement LRU eviction
      if (cache.size >= maxCacheSize) {
        const firstKey = cache.keys().next().value
        cache.delete(firstKey)
      }

      cache.set(key, result)
      return result
    }) as T
  }

  /**
   * Create a performance-optimized event handler
   */
  static createOptimizedHandler<T extends Event>(
    handler: (event: T) => void,
    options: {
      debounce?: number
      throttle?: number
      passive?: boolean
    } = {}
  ): (event: T) => void {
    let optimizedHandler = handler

    if (options.debounce) {
      optimizedHandler = this.debounce(handler, options.debounce) as (event: T) => void
    } else if (options.throttle) {
      optimizedHandler = this.throttle(handler, options.throttle) as (event: T) => void
    }

    return optimizedHandler
  }

  /**
   * Profile an async operation
   */
  static async profileAsync<T>(
    operation: string,
    func: () => Promise<T>
  ): Promise<T> {
    const start = performance.now()

    try {
      const result = await func()
      const duration = performance.now() - start

      console.log(`✓ ${operation} completed in ${duration.toFixed(2)}ms`)

      return result
    } catch (error) {
      const duration = performance.now() - start
      console.error(`✗ ${operation} failed after ${duration.toFixed(2)}ms`, error)
      throw error
    }
  }

  /**
   * Get performance report
   */
  getReport(): {
    averageResponseTime: number
    slowOperations: InteractionMetrics[]
    withinThreshold: boolean
  } {
    const metrics = this.getAllMetrics()

    if (metrics.length === 0) {
      return {
        averageResponseTime: 0,
        slowOperations: [],
        withinThreshold: true,
      }
    }

    const totalTime = metrics.reduce((sum, m) => sum + m.responseTime, 0)
    const averageResponseTime = totalTime / metrics.length

    const slowOperations = metrics
      .filter((m) => m.responseTime > this.INTERACTION_THRESHOLD)
      .sort((a, b) => b.responseTime - a.responseTime)

    return {
      averageResponseTime,
      slowOperations,
      withinThreshold: averageResponseTime < this.INTERACTION_THRESHOLD,
    }
  }

  /**
   * Clear all metrics
   */
  clear(): void {
    this.profiles.clear()
    this.interactionMetrics = []
  }
}

// Global performance monitor instance
export const performanceMonitor = new PerformanceMonitor()

/**
 * Performance optimization hooks for React components
 */

/**
 * Debounced callback hook
 */
export function useDebouncedCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number = 100
): (...args: Parameters<T>) => void {
  const debounced = PerformanceMonitor.debounce(callback, delay)
  return debounced
}

/**
 * Throttled callback hook
 */
export function useThrottledCallback<T extends (...args: any[]) => any>(
  callback: T,
  interval: number = 100
): (...args: Parameters<T>) => void {
  const throttled = PerformanceMonitor.throttle(callback, interval)
  return throttled
}
