/**
 * Retry Utilities
 * Exponential backoff retry logic for API requests
 */

export interface RetryOptions {
  maxRetries?: number;
  baseDelay?: number;
  maxDelay?: number;
  retryableErrors?: string[];
  retryableStatusCodes?: number[];
  onRetry?: (attempt: number, error: Error) => void;
}

export interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  retryableErrors: string[];
  retryableStatusCodes: number[];
  onRetry?: (attempt: number, error: Error) => void;
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000, // 1 second
  maxDelay: 8000, // 8 seconds
  retryableErrors: [
    'ECONNREFUSED',
    'ENOTFOUND',
    'ETIMEDOUT',
    'ECONNRESET',
    'NETWORK_ERROR',
  ],
  retryableStatusCodes: [408, 429, 500, 502, 503, 504],
};

/**
 * Calculate exponential backoff delay
 * Formula: min(baseDelay * 2^attempt, maxDelay)
 */
export const calculateBackoffDelay = (
  attempt: number,
  baseDelay: number,
  maxDelay: number
): number => {
  const delay = baseDelay * Math.pow(2, attempt);
  return Math.min(delay, maxDelay);
};

/**
 * Sleep for specified milliseconds
 */
export const sleep = (ms: number): Promise<void> => {
  return new Promise((resolve) => setTimeout(resolve, ms));
};

/**
 * Check if error is retryable based on config
 */
export const isRetryableError = (
  error: Error & { code?: string; response?: { status?: number } },
  config: RetryConfig
): boolean => {
  // Check error code
  if (error.code && config.retryableErrors.includes(error.code)) {
    return true;
  }

  // Check HTTP status code
  if (
    error.response?.status &&
    config.retryableStatusCodes.includes(error.response.status)
  ) {
    return true;
  }

  // Network errors
  if (error.message?.toLowerCase().includes('network')) {
    return true;
  }

  return false;
};

/**
 * Execute function with exponential backoff retry
 * @param fn Function to execute
 * @param options Retry configuration options
 * @returns Promise with function result
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const config: RetryConfig = {
    ...DEFAULT_RETRY_CONFIG,
    ...options,
  };

  let lastError: Error;
  let attempt = 0;

  while (attempt <= config.maxRetries) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      // If this was the last attempt, throw the error
      if (attempt === config.maxRetries) {
        throw lastError;
      }

      // Check if error is retryable
      if (!isRetryableError(lastError as Error & { code?: string; response?: { status?: number } }, config)) {
        throw lastError;
      }

      // Call onRetry callback if provided
      if (config.onRetry) {
        config.onRetry(attempt + 1, lastError);
      }

      // Calculate delay and wait
      const delay = calculateBackoffDelay(
        attempt,
        config.baseDelay,
        config.maxDelay
      );
      await sleep(delay);

      attempt++;
    }
  }

  // This should never be reached, but TypeScript needs it
  throw lastError!;
}

/**
 * Create a retry wrapper for a function
 * @param fn Function to wrap
 * @param options Retry configuration options
 * @returns Wrapped function with retry logic
 */
export const createRetryWrapper = <T extends unknown[], R>(
  fn: (...args: T) => Promise<R>,
  options: RetryOptions = {}
): ((...args: T) => Promise<R>) => {
  return async (...args: T): Promise<R> => {
    return withRetry(() => fn(...args), options);
  };
};

/**
 * Circuit breaker state
 */
interface CircuitBreakerState {
  failures: number;
  lastFailureTime: number;
  isOpen: boolean;
}

/**
 * Simple circuit breaker implementation
 */
export class CircuitBreaker {
  private state: CircuitBreakerState = {
    failures: 0,
    lastFailureTime: 0,
    isOpen: false,
  };

  constructor(
    private maxFailures: number = 5,
    private resetTimeout: number = 60000
  ) {}

  /**
   * Check if circuit breaker is open (blocking requests)
   */
  public isOpen(): boolean {
    // Check if enough time has passed to reset
    if (
      this.state.isOpen &&
      Date.now() - this.state.lastFailureTime > this.resetTimeout
    ) {
      this.reset();
      return false;
    }

    return this.state.isOpen;
  }

  /**
   * Record a successful request
   */
  public recordSuccess(): void {
    this.reset();
  }

  /**
   * Record a failed request
   */
  public recordFailure(): void {
    this.state.failures++;
    this.state.lastFailureTime = Date.now();

    if (this.state.failures >= this.maxFailures) {
      this.state.isOpen = true;
    }
  }

  /**
   * Reset circuit breaker to initial state
   */
  public reset(): void {
    this.state.failures = 0;
    this.state.lastFailureTime = 0;
    this.state.isOpen = false;
  }

  /**
   * Get current failure count
   */
  public getFailureCount(): number {
    return this.state.failures;
  }
}

/**
 * Global circuit breaker instance for API calls
 */
export const apiCircuitBreaker = new CircuitBreaker(5, 60000);
