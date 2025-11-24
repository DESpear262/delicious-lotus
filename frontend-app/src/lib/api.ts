/**
 * API client utility for making backend API calls
 */

const API_BASE = '/api/v1'

export class APIError extends Error {
  public status: number
  public statusText: string
  public data?: unknown

  constructor(
    status: number,
    statusText: string,
    data?: unknown
  ) {
    super(`API Error: ${status} ${statusText}`)
    this.name = 'APIError'
    this.status = status
    this.statusText = statusText
    this.data = data
  }
}

export interface FetchOptions extends RequestInit {
  params?: Record<string, string | number | boolean>
}

/**
 * Make an API request with automatic error handling
 */
export async function apiRequest<T>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> {
  const { params, ...fetchOptions } = options

  // Build URL with query parameters
  let url = `${API_BASE}${endpoint}`
  if (params) {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      searchParams.append(key, String(value))
    })
    url += `?${searchParams.toString()}`
  }

  // Default headers
  const headers = {
    'Content-Type': 'application/json',
    ...fetchOptions.headers,
  }

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers,
    })

    // Handle non-2xx responses
    if (!response.ok) {
      let errorData: unknown
      try {
        errorData = await response.json()
      } catch {
        errorData = await response.text()
      }
      throw new APIError(response.status, response.statusText, errorData)
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return undefined as T
    }

    // Parse JSON response
    return await response.json()
  } catch (error) {
    if (error instanceof APIError) {
      throw error
    }
    // Network or other errors
    throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

/**
 * API helper methods
 */
export const api = {
  get: <T>(endpoint: string, options?: FetchOptions) =>
    apiRequest<T>(endpoint, { ...options, method: 'GET' }),

  post: <T>(endpoint: string, data?: unknown, options?: FetchOptions) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }),

  put: <T>(endpoint: string, data?: unknown, options?: FetchOptions) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }),

  patch: <T>(endpoint: string, data?: unknown, options?: FetchOptions) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    }),

  delete: <T>(endpoint: string, options?: FetchOptions) =>
    apiRequest<T>(endpoint, { ...options, method: 'DELETE' }),
}

/**
 * Update media asset attributes
 */
export async function updateMediaAsset(id: string, data: { name?: string }): Promise<any> {
  return api.patch(`/media/${id}/attributes`, data)
}

/**
 * Get single media asset with full metadata
 */
export async function getMediaAsset(id: string): Promise<any> {
  return api.get(`/media/${id}`)
}
