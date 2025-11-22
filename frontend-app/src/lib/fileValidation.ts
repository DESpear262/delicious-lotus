/**
 * File Validation Utilities
 * Handles validation of uploaded media files against size and type constraints
 */

export type MediaFileType = 'image' | 'video' | 'audio' | 'unknown'

export const ValidationErrorType = {
  INVALID_TYPE: 'INVALID_TYPE',
  FILE_TOO_LARGE: 'FILE_TOO_LARGE',
  INVALID_EXTENSION: 'INVALID_EXTENSION',
} as const

export type ValidationErrorType = typeof ValidationErrorType[keyof typeof ValidationErrorType]

export class FileValidationError extends Error {
  type: ValidationErrorType
  fileName: string

  constructor(
    type: ValidationErrorType,
    fileName: string,
    message: string
  ) {
    super(message)
    this.type = type
    this.fileName = fileName
    this.name = 'FileValidationError'
  }
}

export interface ValidationConfig {
  maxSizeImage: number // bytes
  maxSizeVideo: number // bytes
  maxSizeAudio: number // bytes
  allowedImageTypes: string[]
  allowedVideoTypes: string[]
  allowedAudioTypes: string[]
}

// Default configuration based on environment limits
export const DEFAULT_VALIDATION_CONFIG: ValidationConfig = {
  maxSizeImage: 100 * 1024 * 1024, // 100MB
  maxSizeVideo: 1024 * 1024 * 1024, // 1GB
  maxSizeAudio: 500 * 1024 * 1024, // 500MB
  allowedImageTypes: ['image/jpeg', 'image/png', 'image/webp', 'image/gif'],
  allowedVideoTypes: ['video/mp4', 'video/webm', 'video/quicktime', 'video/x-msvideo'],
  allowedAudioTypes: ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4'],
}

// Map of file extensions to MIME types (fallback for when browser doesn't provide correct MIME)
const EXTENSION_TO_MIME: Record<string, string> = {
  // Images
  jpg: 'image/jpeg',
  jpeg: 'image/jpeg',
  png: 'image/png',
  webp: 'image/webp',
  gif: 'image/gif',
  // Videos
  mp4: 'video/mp4',
  webm: 'video/webm',
  mov: 'video/quicktime',
  avi: 'video/x-msvideo',
  // Audio
  mp3: 'audio/mpeg',
  wav: 'audio/wav',
  ogg: 'audio/ogg',
  m4a: 'audio/mp4',
}

/**
 * Determines the media type from MIME type
 */
export function getMediaType(mimeType: string): MediaFileType {
  if (mimeType.startsWith('image/')) return 'image'
  if (mimeType.startsWith('video/')) return 'video'
  if (mimeType.startsWith('audio/')) return 'audio'
  return 'unknown'
}

/**
 * Gets the file extension from a filename
 */
export function getFileExtension(filename: string): string {
  const parts = filename.split('.')
  return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : ''
}

/**
 * Attempts to determine MIME type from file extension if browser doesn't provide it
 */
export function getMimeTypeFromExtension(filename: string): string | undefined {
  const extension = getFileExtension(filename)
  return EXTENSION_TO_MIME[extension]
}

/**
 * Validates a single file against the configuration
 */
export function validateFile(
  file: File,
  config: ValidationConfig = DEFAULT_VALIDATION_CONFIG
): { valid: true } | { valid: false; error: FileValidationError } {
  // Determine MIME type (use extension fallback if needed)
  let mimeType = file.type
  if (!mimeType || mimeType === 'application/octet-stream') {
    const fallbackMime = getMimeTypeFromExtension(file.name)
    if (fallbackMime) {
      mimeType = fallbackMime
    }
  }

  const mediaType = getMediaType(mimeType)

  // Check if file type is supported
  let isTypeAllowed = false
  let maxSize = 0

  switch (mediaType) {
    case 'image':
      isTypeAllowed = config.allowedImageTypes.includes(mimeType)
      maxSize = config.maxSizeImage
      break
    case 'video':
      isTypeAllowed = config.allowedVideoTypes.includes(mimeType)
      maxSize = config.maxSizeVideo
      break
    case 'audio':
      isTypeAllowed = config.allowedAudioTypes.includes(mimeType)
      maxSize = config.maxSizeAudio
      break
    default:
      return {
        valid: false,
        error: new FileValidationError(
          ValidationErrorType.INVALID_TYPE,
          file.name,
          `File type "${mimeType}" is not supported. Please upload an image, video, or audio file.`
        ),
      }
  }

  if (!isTypeAllowed) {
    return {
      valid: false,
      error: new FileValidationError(
        ValidationErrorType.INVALID_TYPE,
        file.name,
        `File type "${mimeType}" is not allowed for ${mediaType} files.`
      ),
    }
  }

  // Check file size
  if (file.size > maxSize) {
    const maxSizeMB = Math.round(maxSize / (1024 * 1024))
    const fileSizeMB = Math.round(file.size / (1024 * 1024))
    return {
      valid: false,
      error: new FileValidationError(
        ValidationErrorType.FILE_TOO_LARGE,
        file.name,
        `File "${file.name}" is too large (${fileSizeMB}MB). Maximum size for ${mediaType} files is ${maxSizeMB}MB.`
      ),
    }
  }

  return { valid: true }
}

/**
 * Validates multiple files and returns results for each
 */
export interface BatchValidationResult {
  validFiles: File[]
  invalidFiles: Array<{ file: File; error: FileValidationError }>
  allValid: boolean
}

export function validateFiles(
  files: File[],
  config: ValidationConfig = DEFAULT_VALIDATION_CONFIG
): BatchValidationResult {
  const validFiles: File[] = []
  const invalidFiles: Array<{ file: File; error: FileValidationError }> = []

  for (const file of files) {
    const result = validateFile(file, config)
    if (result.valid) {
      validFiles.push(file)
    } else {
      // Type guard: result.valid === false means error exists
      invalidFiles.push({ file, error: (result as { valid: false; error: FileValidationError }).error })
    }
  }

  return {
    validFiles,
    invalidFiles,
    allValid: invalidFiles.length === 0,
  }
}

/**
 * Formats file size in human-readable format
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

/**
 * Gets a user-friendly description of allowed file types
 */
export function getAllowedTypesDescription(): string {
  const imageExts = 'JPG, PNG, WebP, GIF'
  const videoExts = 'MP4, WebM, MOV, AVI'
  const audioExts = 'MP3, WAV, OGG, M4A'

  return `Images (${imageExts}), Videos (${videoExts}), Audio (${audioExts})`
}
