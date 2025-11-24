/**
 * AI Generation Service
 * Handles API calls to Replicate for image, video, and audio generation
 */

import type { GenerationType, QualityTier } from '../types/stores'

// API base URL - should be configured from environment
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface GenerateImageRequest {
  prompt: string
  qualityTier: QualityTier
  aspectRatio: string
  model?: string
  // Advanced params
  image_input?: string | string[]
  output_format?: string
  output_quality?: number
  seed?: number
  disable_safety_checker?: boolean
}

export interface GenerateVideoRequest {
  prompt: string
  size?: string // Deprecated but kept for compatibility
  duration?: number
  aspectRatio?: string
  style?: string
  quality?: string
}

export interface GenerationResponse {
  job_id: string
  generation_id?: string
  status: string
  message?: string
  websocket_url?: string
}

/**
 * Generate an image using Replicate models
 * @param request - Image generation request parameters
 * @returns Response containing job ID for tracking
 */
export async function generateImage(request: GenerateImageRequest): Promise<GenerationResponse> {
  let endpoint = '/api/v1/replicate/nano-banana'

  // Handle image_input: ensure it's an array if provided, or undefined
  let imageInput: string[] | undefined
  if (request.image_input) {
    imageInput = Array.isArray(request.image_input) ? request.image_input : [request.image_input]
  }

  let body: Record<string, any> = {
    prompt: request.prompt,
    quality_tier: request.qualityTier,
    aspect_ratio: request.aspectRatio,
    image_input: imageInput,
  }

  if (request.model === 'flux-schnell') {
    endpoint = '/api/v1/replicate/flux-schnell'
    body = {
      prompt: request.prompt,
      aspect_ratio: request.aspectRatio,
      output_format: request.output_format || 'webp',
      output_quality: request.output_quality || 80,
      disable_safety_checker: request.disable_safety_checker,
      seed: request.seed,
    }
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }))
    throw new Error(error.message || `HTTP error! status: ${response.status}`)
  }

  return response.json()
}

/**
 * Generate a video using the Advanced AI Pipeline
 * (Calls /api/v1/generations which uses PromptAnalysis -> MicroPrompts -> Scenes)
 * 
 * @param request - Video generation request parameters
 * @returns Response containing generation ID (mapped to job_id) for tracking
 */
export async function generateVideo(request: GenerateVideoRequest): Promise<GenerationResponse> {
  // Map parameters to Advanced Pipeline schema
  
  // Aspect Ratio
  const aspectRatio = request.aspectRatio || '16:9'
  
  // Validate duration (must be 15, 30, 45, 60)
  // Default to 15 if not provided or invalid
  let duration = request.duration || 15
  if (duration < 15) duration = 15
  else if (duration > 60) duration = 60
  else {
    // Snap to nearest allowed value: 15, 30, 45, 60
    const allowed = [15, 30, 45, 60]
    duration = allowed.reduce((prev, curr) => 
      Math.abs(curr - duration) < Math.abs(prev - duration) ? curr : prev
    )
  }

  const payload = {
    prompt: request.prompt,
    parameters: {
      duration_seconds: duration,
      aspect_ratio: aspectRatio,
      style: request.style || "professional",
      include_cta: true,
      cta_text: "Shop Now",
      music_style: "corporate"
    },
    options: {
      quality: request.quality || "high",
      parallelize_generations: true
    }
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/generations`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }))
    throw new Error(error.message || `HTTP error! status: ${response.status}`)
  }

  const data = await response.json()
  
  return {
    job_id: data.generation_id, // Map generation_id to job_id for frontend compatibility
    generation_id: data.generation_id,
    status: data.status,
    message: "Generation started",
    websocket_url: data.websocket_url
  }
}

/**
 * Cancel a generation job
 * @param jobId - Job ID to cancel
 */
export async function cancelGeneration(jobId: string): Promise<void> {
  // Try to cancel using new endpoint structure if it looks like a generation ID
  // (Generation IDs are usually 'gen_...')
  const isGenerationId = jobId.startsWith('gen_')
  const endpoint = isGenerationId 
    ? `${API_BASE_URL}/api/v1/generations/${jobId}/cancel`
    : `${API_BASE_URL}/api/v1/jobs/${jobId}/cancel`

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    // Try fallback if first attempt failed (maybe it was the other type)
    if (response.status === 404 && isGenerationId) {
        const fallbackResponse = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}/cancel`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        })
        if (fallbackResponse.ok) return
    }
    
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
  // Check if it's a generation ID (gen_...)
  if (jobId.startsWith('gen_')) {
    const response = await fetch(`${API_BASE_URL}/api/v1/generations/${jobId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: response.statusText }))
      throw new Error(error.message || `Failed to get generation status: ${response.status}`)
    }

    const data = await response.json()
    
    // Map Advanced Pipeline response to simple status format
    let result_url = undefined
    if (data.status === 'completed' && data.metadata?.video_results) {
        // Use first completed video url
        const completed = data.metadata.video_results.find((r: any) => r.status === 'completed')
        if (completed) result_url = completed.video_url
    }

    return {
      status: data.status,
      progress: data.progress?.percentage || 0,
      result_url,
      error: data.status === 'failed' ? 'Generation failed' : undefined
    }
  } else {
    // Legacy job ID
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
}
