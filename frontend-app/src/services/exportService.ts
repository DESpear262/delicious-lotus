// Export API Service
import type { CompositionPayload } from '@/lib/compositionSerializer'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api/v1'
const API_TIMEOUT = 30000 // 30 seconds

// Custom error types
export class ExportError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: unknown
  ) {
    super(message)
    this.name = 'ExportError'
  }
}

export class ValidationError extends ExportError {
  constructor(message: string, details?: unknown) {
    super(message, 400, details)
    this.name = 'ValidationError'
  }
}

export class NetworkError extends ExportError {
  constructor(message: string) {
    super(message, 0)
    this.name = 'NetworkError'
  }
}

// API Response types
export interface ExportJobResponse {
  jobId: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  message?: string
  createdAt: string
}

/**
 * Submits a composition for export to the backend
 */
export async function exportComposition(
  composition: CompositionPayload
): Promise<ExportJobResponse> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT)

  try {
    const response = await fetch(`${API_BASE_URL}/compositions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Add authentication header if needed
        // 'Authorization': `Bearer ${getAuthToken()}`,
      },
      body: JSON.stringify(composition),
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    // Handle different response status codes
    if (!response.ok) {
      await handleErrorResponse(response)
    }

    const data = await response.json()
    return data as ExportJobResponse
  } catch (error) {
    clearTimeout(timeoutId)

    if (error instanceof ExportError) {
      throw error
    }

    // Handle abort/timeout
    if (error instanceof Error && error.name === 'AbortError') {
      throw new NetworkError('Request timeout: Server took too long to respond')
    }

    // Handle network errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new NetworkError('Network error: Unable to connect to the server')
    }

    // Re-throw unknown errors
    throw new ExportError(
      error instanceof Error ? error.message : 'Unknown export error',
      undefined,
      error
    )
  }
}

/**
 * Handles error responses from the API
 */
async function handleErrorResponse(response: Response): Promise<never> {
  let errorData: any
  try {
    errorData = await response.json()
  } catch {
    errorData = { message: response.statusText }
  }

  const message = errorData.message || errorData.error || 'Export failed'

  switch (response.status) {
    case 400:
      throw new ValidationError(message, errorData.details)
    case 401:
      throw new ExportError('Unauthorized: Please login again', 401)
    case 403:
      throw new ExportError('Forbidden: You do not have permission to export', 403)
    case 413:
      throw new ExportError(
        'Payload too large: Composition exceeds maximum allowed size',
        413
      )
    case 429:
      throw new ExportError(
        'Too many requests: Please wait before exporting again',
        429
      )
    case 500:
      throw new ExportError('Server error: Please try again later', 500, errorData)
    case 503:
      throw new ExportError('Service unavailable: Server is temporarily offline', 503)
    default:
      throw new ExportError(message, response.status, errorData)
  }
}

/**
 * Checks the status of an export job
 */
export async function getExportJobStatus(jobId: string): Promise<ExportJobResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/compositions/${jobId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        // Add authentication header if needed
        // 'Authorization': `Bearer ${getAuthToken()}`,
      },
    })

    if (!response.ok) {
      await handleErrorResponse(response)
    }

    const data = await response.json()
    return data as ExportJobResponse
  } catch (error) {
    if (error instanceof ExportError) {
      throw error
    }
    throw new ExportError(
      error instanceof Error ? error.message : 'Failed to get job status'
    )
  }
}

/**
 * Cancels an export job
 */
export async function cancelExportJob(jobId: string): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/compositions/${jobId}/cancel`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Add authentication header if needed
        // 'Authorization': `Bearer ${getAuthToken()}`,
      },
    })

    if (!response.ok) {
      await handleErrorResponse(response)
    }
  } catch (error) {
    if (error instanceof ExportError) {
      throw error
    }
    throw new ExportError(
      error instanceof Error ? error.message : 'Failed to cancel export job'
    )
  }
}

/**
 * Retry logic for export submission
 */
export async function exportCompositionWithRetry(
  composition: CompositionPayload,
  maxRetries = 3,
  retryDelay = 2000
): Promise<ExportJobResponse> {
  let lastError: Error | null = null

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await exportComposition(composition)
    } catch (error) {
      lastError = error as Error

      // Don't retry on validation errors or client errors
      if (
        error instanceof ValidationError ||
        (error instanceof ExportError && error.statusCode && error.statusCode < 500)
      ) {
        throw error
      }

      // Don't retry on last attempt
      if (attempt === maxRetries) {
        break
      }

      // Wait before retrying with exponential backoff
      const delay = retryDelay * Math.pow(2, attempt)
      await new Promise((resolve) => setTimeout(resolve, delay))

      console.log(`Retrying export (attempt ${attempt + 2}/${maxRetries + 1})...`)
    }
  }

  // All retries exhausted
  throw lastError || new ExportError('Export failed after maximum retries')
}
