/**
 * Debounce utility function
 * Creates a debounced function that delays invoking func until after wait milliseconds
 * have elapsed since the last time the debounced function was invoked
 */

export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout | null = null

  return function debounced(...args: Parameters<T>) {
    if (timeoutId) {
      clearTimeout(timeoutId)
    }

    timeoutId = setTimeout(() => {
      func(...args)
      timeoutId = null
    }, wait)
  }
}

/**
 * Cancel a debounced function
 */
export function cancelDebounce(timeoutId: NodeJS.Timeout | null): void {
  if (timeoutId) {
    clearTimeout(timeoutId)
  }
}
