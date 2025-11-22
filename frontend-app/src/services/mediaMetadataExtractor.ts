/**
 * Client-side media metadata extraction utilities
 * Extracts duration, dimensions, and other properties from File objects
 */

export interface ExtractedMediaMetadata {
  duration?: number // seconds (for video/audio)
  width?: number
  height?: number
  frameRate?: number
  codec?: string
  bitrate?: number
}

/**
 * Extract metadata from a video file using HTML5 Video API
 */
export async function extractVideoMetadata(file: File): Promise<ExtractedMediaMetadata> {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video')
    const objectUrl = URL.createObjectURL(file)

    const cleanup = () => {
      video.remove()
      URL.revokeObjectURL(objectUrl)
    }

    // Set timeout to prevent hanging
    const timeout = setTimeout(() => {
      cleanup()
      reject(new Error('Video metadata extraction timed out'))
    }, 10000)

    video.addEventListener('loadedmetadata', () => {
      clearTimeout(timeout)

      const metadata: ExtractedMediaMetadata = {
        duration: video.duration,
        width: video.videoWidth,
        height: video.videoHeight,
      }

      cleanup()
      resolve(metadata)
    })

    video.addEventListener('error', (e) => {
      clearTimeout(timeout)
      cleanup()
      reject(new Error(`Failed to load video: ${e.toString()}`))
    })

    // Preload metadata only (don't download entire video)
    video.preload = 'metadata'
    video.src = objectUrl

    // Manually load if not already triggered
    video.load()
  })
}

/**
 * Extract metadata from a video URL (e.g., presigned S3 URL)
 * This is useful for extracting metadata from remote videos without uploading them
 */
export async function extractVideoMetadataFromUrl(url: string): Promise<ExtractedMediaMetadata> {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video')

    const cleanup = () => {
      video.remove()
    }

    // Set timeout to prevent hanging
    const timeout = setTimeout(() => {
      cleanup()
      reject(new Error('Video metadata extraction from URL timed out'))
    }, 10000)

    video.addEventListener('loadedmetadata', () => {
      clearTimeout(timeout)

      const metadata: ExtractedMediaMetadata = {
        duration: video.duration,
        width: video.videoWidth,
        height: video.videoHeight,
      }

      cleanup()
      resolve(metadata)
    })

    video.addEventListener('error', (e) => {
      clearTimeout(timeout)
      cleanup()
      reject(new Error(`Failed to load video from URL: ${e.toString()}`))
    })

    // Enable CORS for cross-origin requests (S3 presigned URLs)
    video.crossOrigin = 'anonymous'

    // Preload metadata only (don't download entire video)
    video.preload = 'metadata'
    video.src = url

    // Manually load if not already triggered
    video.load()
  })
}

/**
 * Extract metadata from an image file using HTML5 Image API
 */
export async function extractImageMetadata(file: File): Promise<ExtractedMediaMetadata> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const objectUrl = URL.createObjectURL(file)

    const cleanup = () => {
      URL.revokeObjectURL(objectUrl)
    }

    const timeout = setTimeout(() => {
      cleanup()
      reject(new Error('Image metadata extraction timed out'))
    }, 5000)

    img.addEventListener('load', () => {
      clearTimeout(timeout)

      const metadata: ExtractedMediaMetadata = {
        width: img.naturalWidth,
        height: img.naturalHeight,
      }

      cleanup()
      resolve(metadata)
    })

    img.addEventListener('error', (e) => {
      clearTimeout(timeout)
      cleanup()
      reject(new Error(`Failed to load image: ${e.toString()}`))
    })

    img.src = objectUrl
  })
}

/**
 * Extract metadata from an audio file using HTML5 Audio API
 */
export async function extractAudioMetadata(file: File): Promise<ExtractedMediaMetadata> {
  return new Promise((resolve, reject) => {
    const audio = new Audio()
    const objectUrl = URL.createObjectURL(file)

    const cleanup = () => {
      audio.remove()
      URL.revokeObjectURL(objectUrl)
    }

    const timeout = setTimeout(() => {
      cleanup()
      reject(new Error('Audio metadata extraction timed out'))
    }, 10000)

    audio.addEventListener('loadedmetadata', () => {
      clearTimeout(timeout)

      const metadata: ExtractedMediaMetadata = {
        duration: audio.duration,
      }

      cleanup()
      resolve(metadata)
    })

    audio.addEventListener('error', (e) => {
      clearTimeout(timeout)
      cleanup()
      reject(new Error(`Failed to load audio: ${e.toString()}`))
    })

    audio.preload = 'metadata'
    audio.src = objectUrl
    audio.load()
  })
}

/**
 * Extract metadata from any media file
 * Automatically detects type and uses appropriate extraction method
 */
export async function extractMediaMetadata(file: File): Promise<ExtractedMediaMetadata> {
  const type = file.type.toLowerCase()

  try {
    if (type.startsWith('video/')) {
      return await extractVideoMetadata(file)
    } else if (type.startsWith('image/')) {
      return await extractImageMetadata(file)
    } else if (type.startsWith('audio/')) {
      return await extractAudioMetadata(file)
    } else {
      console.warn(`Unsupported media type: ${type}`)
      return {}
    }
  } catch (error) {
    console.error('Failed to extract media metadata:', error)
    // Return empty metadata on error (non-blocking)
    return {}
  }
}
