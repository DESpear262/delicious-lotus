/**
 * Assets Service
 * API calls for asset upload and management
 */

import { upload, del } from '@/api/client';

/**
 * Upload response type
 */
export interface UploadResponse {
  asset_id: string;
  url: string;
  filename: string;
  size_bytes: number;
  content_type: string;
  created_at: string;
}

/**
 * Upload a brand asset (logo, image)
 */
export const uploadBrandAsset = async (
  file: File,
  onProgress?: (progress: number) => void
): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('type', 'brand_asset');

  return upload<UploadResponse>('/v1/assets/upload', formData, onProgress);
};

/**
 * Upload audio file for music video generation
 */
export const uploadAudioFile = async (
  file: File,
  onProgress?: (progress: number) => void
): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('type', 'audio');

  return upload<UploadResponse>('/v1/assets/upload', formData, onProgress);
};

/**
 * Upload generic file
 */
export const uploadFile = async (
  file: File,
  type: string,
  onProgress?: (progress: number) => void
): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('type', type);

  return upload<UploadResponse>('/v1/assets/upload', formData, onProgress);
};

/**
 * Upload asset with full options support (including abort signal)
 */
export const uploadAsset = async (
  formData: FormData,
  options?: {
    signal?: AbortSignal;
    onUploadProgress?: (progressEvent: ProgressEvent) => void;
  }
): Promise<UploadResponse> => {
  return upload<UploadResponse>(
    '/v1/assets/upload',
    formData,
    options?.onUploadProgress
      ? (progress) => {
          // Convert progress number to ProgressEvent-like object
          const progressEvent = {
            loaded: progress,
            total: 100,
          } as ProgressEvent;
          options.onUploadProgress?.(progressEvent);
        }
      : undefined,
    {
      signal: options?.signal,
    }
  );
};

/**
 * Delete an uploaded asset
 */
export const deleteAsset = async (assetId: string): Promise<void> => {
  return del<void>(`/v1/assets/${assetId}`);
};

/**
 * Validate file before upload
 */
export interface FileValidationResult {
  valid: boolean;
  error?: string;
}

/**
 * Validate brand asset file
 */
export const validateBrandAsset = (file: File): FileValidationResult => {
  const MAX_SIZE = 50 * 1024 * 1024; // 50MB
  const ALLOWED_TYPES = [
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/webp',
    'image/svg+xml',
  ];

  if (file.size > MAX_SIZE) {
    return {
      valid: false,
      error: 'File size exceeds 50MB limit',
    };
  }

  if (!ALLOWED_TYPES.includes(file.type)) {
    return {
      valid: false,
      error: 'Invalid file type. Allowed types: JPEG, PNG, WebP, SVG',
    };
  }

  return { valid: true };
};

/**
 * Validate audio file
 */
export const validateAudioFile = (file: File): FileValidationResult => {
  const MAX_SIZE = 100 * 1024 * 1024; // 100MB
  const ALLOWED_TYPES = [
    'audio/mpeg',
    'audio/mp3',
    'audio/wav',
    'audio/x-wav',
    'audio/ogg',
    'audio/aac',
  ];

  if (file.size > MAX_SIZE) {
    return {
      valid: false,
      error: 'File size exceeds 100MB limit',
    };
  }

  if (!ALLOWED_TYPES.includes(file.type)) {
    return {
      valid: false,
      error: 'Invalid file type. Allowed types: MP3, WAV, OGG, AAC',
    };
  }

  return { valid: true };
};

/**
 * Format file size for display
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

/**
 * Get file extension from filename
 */
export const getFileExtension = (filename: string): string => {
  return filename.slice(((filename.lastIndexOf('.') - 1) >>> 0) + 2);
};

/**
 * Check if file is an image
 */
export const isImageFile = (file: File): boolean => {
  return file.type.startsWith('image/');
};

/**
 * Check if file is an audio file
 */
export const isAudioFile = (file: File): boolean => {
  return file.type.startsWith('audio/');
};
