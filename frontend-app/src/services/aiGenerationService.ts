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
  image_input?: string
  output_format?: string
  output_quality?: number
  seed?: number
  disable_safety_checker?: boolean
}

export interface GenerateVideoRequest {
  prompt: string
  size?: string
  duration?: number
  model?: string
  aspectRatio?: string
  resolution?: string
  // Advanced params
  image?: string
  last_image?: string
  last_frame?: string
  start_image?: string
  first_frame_image?: string
  negative_prompt?: string
  seed?: number
  fps?: number
  camera_fixed?: boolean
  prompt_optimizer?: boolean
  audio?: string
  enable_prompt_expansion?: boolean
}

export interface GenerateAudioRequest {
  prompt: string
  duration?: number
  model?: string
  // Advanced params
  negative_prompt?: string
  seed?: number
  lyrics?: string
  voice_file?: string
  song_file?: string
  instrumental_file?: string
}

export interface GenerationResponse {
  job_id: string
  status: string
  message?: string
}

/**
 * Generate an image using Replicate models
 * @param request - Image generation request parameters
 * @returns Response containing job ID for tracking
 */
export async function generateImage(request: GenerateImageRequest): Promise<GenerationResponse> {
  let endpoint = '/api/v1/replicate/nano-banana'
  let body: Record<string, any> = {
    prompt: request.prompt,
    quality_tier: request.qualityTier,
    aspect_ratio: request.aspectRatio,
    image_input: request.image_input ? [request.image_input] : undefined,
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
 * Generate a video using Replicate models
 * @param request - Video generation request parameters
 * @returns Response containing job ID for tracking
 */
export async function generateVideo(request: GenerateVideoRequest): Promise<GenerationResponse> {
  let endpoint = '/api/v1/replicate/wan-video-t2v'
  let body: Record<string, any> = {
    prompt: request.prompt,
    size: request.size || '1280*720',
    duration: request.duration || 5,
  }

  // Handle different video models
  switch (request.model) {
    case 'veo-3.1':
      endpoint = '/api/v1/replicate/veo-3.1-fast'
      body = {
        prompt: request.prompt,
        aspect_ratio: request.aspectRatio || '16:9',
        duration: request.duration || 8,
        resolution: request.resolution || '1080p',
        image: request.image,
        last_frame: request.last_frame,
        negative_prompt: request.negative_prompt,
        seed: request.seed,
      }
      break
    case 'kling-v2.5':
      endpoint = '/api/v1/replicate/kling-v2.5-turbo-pro'
      body = {
        prompt: request.prompt,
        aspect_ratio: request.aspectRatio || '16:9',
        duration: request.duration || 5,
        start_image: request.start_image || request.image, // Normalize image input
        negative_prompt: request.negative_prompt,
      }
      break
    case 'hailuo-2.3':
      endpoint = '/api/v1/replicate/hailuo-2.3-fast'
      body = {
        prompt: request.prompt,
        first_frame_image: request.first_frame_image || request.image, // Normalize image input
        duration: request.duration || 6,
        resolution: request.resolution || '768p',
        prompt_optimizer: request.prompt_optimizer !== false, // Default true
      }
      break
    case 'seedance':
      endpoint = '/api/v1/replicate/seedance-1-pro-fast'
      body = {
        prompt: request.prompt,
        duration: request.duration || 5,
        resolution: request.resolution || '1080p',
        aspect_ratio: request.aspectRatio || '16:9',
        image: request.image,
        fps: request.fps || 24,
        camera_fixed: request.camera_fixed,
        seed: request.seed,
      }
      break
    case 'wan-video-i2v':
      endpoint = '/api/v1/replicate/wan-video-i2v'
      body = {
        prompt: request.prompt,
        image: request.image,
        audio: request.audio,
        duration: request.duration || 5,
        resolution: request.resolution || '720p',
        negative_prompt: request.negative_prompt,
        enable_prompt_expansion: request.enable_prompt_expansion !== false, // Default true
      }
      break
    case 'wan-video-t2v':
    default:
      // Default is Wan Video T2V
      endpoint = '/api/v1/replicate/wan-video-t2v'
      body = {
        prompt: request.prompt,
        size: request.size || '1280*720',
        duration: request.duration || 5,
      }
      break
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
 * Generate audio using Replicate models
 * @param request - Audio generation request parameters
 * @returns Response containing job ID for tracking
 */
export async function generateAudio(request: GenerateAudioRequest): Promise<GenerationResponse> {
  let endpoint = '/api/v1/replicate/stable-audio-2.5'
  let body: Record<string, any> = {
    prompt: request.prompt,
    duration: request.duration || 45,
  }

  switch (request.model) {
    case 'music-01':
      endpoint = '/api/v1/replicate/music-01'
      body = {
        lyrics: request.prompt, // Music-01 uses lyrics/prompt field
        voice_file: request.voice_file,
        song_file: request.song_file,
        instrumental_file: request.instrumental_file,
      }
      break
    case 'lyria-2':
      endpoint = '/api/v1/replicate/lyria-2'
      body = {
        prompt: request.prompt,
        negative_prompt: request.negative_prompt,
        seed: request.seed,
      }
      break
    case 'stable-audio':
    default:
      endpoint = '/api/v1/replicate/stable-audio-2.5'
      body = {
        prompt: request.prompt,
        duration: request.duration || 45,
        seed: request.seed,
      }
      break
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
