/**
 * AI Generation Service
 * Handles API calls to Replicate for image and video generation
 */

import type { GenerationType, QualityTier } from '../types/stores'

// API base URL - should be configured from environment
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface GenerateImageRequest {
  prompt: string
  qualityTier: QualityTier
  aspectRatio: string
}

export interface GenerateVideoRequest {
  prompt: string
  size?: string
  duration?: number
}

export interface GenerationResponse {
  job_id: string
  status: string
  message?: string
}

/**
 * Generate an image using Replicate's Nano-Banana model
 * @param request - Image generation request parameters
 * @returns Response containing job ID for tracking
 */
export async function generateImage(request: GenerateImageRequest): Promise<GenerationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/replicate/nano-banana`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      prompt: request.prompt,
      quality_tier: request.qualityTier,
      aspect_ratio: request.aspectRatio,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }))
    throw new Error(error.message || `HTTP error! status: ${response.status}`)
  }

  return response.json()
}

/**
 * Generate a video using Replicate's Wan Video 2.5 T2V model (text-to-video)
 * @param request - Video generation request parameters
 * @returns Response containing job ID for tracking
 */
export async function generateVideo(request: GenerateVideoRequest): Promise<GenerationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/replicate/wan-video-t2v`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      prompt: request.prompt,
      size: request.size || '1280*720',
      duration: request.duration || 5,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }))
    throw new Error(error.message || `HTTP error! status: ${response.status}`)
  }

  return response.json()
}

/**
 * Cancel a generation job
 * @param jobId - Job ID to cancel
 */
export async function cancelGeneration(jobId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}/cancel`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }))
    throw new Error(error.message || `Failed to cancel generation: ${response.status}`)
  }
}

/**
 * Get generation job status (backup for WebSocket)
 * @param jobId - Job ID to check status for
 * @returns Job status information
 */
export async function getGenerationStatus(jobId: string): Promise<{
  status: string
  progress?: number
  result_url?: string
  error?: string
}> {
  const response = await fetch(`${API_BASE_URL}/api/v1/replicate/jobs/${jobId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }))
    throw new Error(error.message || `Failed to get job status: ${response.status}`)
  }

  return response.json()
}
