/**
 * File Upload Hook
 * Custom hook for managing file upload state and API integration
 */

import { useState, useCallback, useRef } from 'react';
import { uploadFile as uploadFileService, type UploadResponse } from '@/services/ad-generator/services/assets';

export interface UploadedAsset {
  id: string;
  url: string;
  filename: string;
  size: number;
  type: string;
  thumbnail?: string;
  metadata?: Record<string, unknown>;
}

export interface UploadState {
  id: string;
  file: File;
  progress: number; // 0-100
  status: 'uploading' | 'success' | 'error';
  error?: string;
}

export interface UploadOptions {
  onProgress?: (progress: number, uploadId: string) => void;
  onSuccess?: (asset: UploadedAsset, uploadId: string) => void;
  onError?: (error: Error, uploadId: string) => void;
}

export interface UseFileUploadReturn {
  uploadFile: (file: File, options?: UploadOptions) => Promise<UploadedAsset>;
  uploadMultiple: (
    files: File[],
    options?: UploadOptions
  ) => Promise<UploadedAsset[]>;
  cancelUpload: (uploadId: string) => void;
  uploads: Map<string, UploadState>;
}

/**
 * Generate a simple ID for tracking uploads
 */
function generateId(): string {
  return `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Convert UploadResponse to UploadedAsset
 */
function mapUploadResponseToAsset(response: UploadResponse): UploadedAsset {
  return {
    id: response.asset_id,
    url: response.url,
    filename: response.filename,
    size: response.size_bytes,
    type: response.content_type,
    thumbnail: undefined, // Backend doesn't return thumbnail yet
    metadata: undefined,
  };
}

/**
 * Hook for managing file uploads
 */
export function useFileUpload(): UseFileUploadReturn {
  const [uploads, setUploads] = useState<Map<string, UploadState>>(new Map());
  const abortControllers = useRef<Map<string, AbortController>>(new Map());

  const uploadFile = useCallback(
    async (file: File, options?: UploadOptions): Promise<UploadedAsset> => {
      const uploadId = generateId();
      const abortController = new AbortController();
      abortControllers.current.set(uploadId, abortController);

      // Initialize upload state
      setUploads((prev) =>
        new Map(prev).set(uploadId, {
          id: uploadId,
          file,
          progress: 0,
          status: 'uploading',
        })
      );

      try {
        // Determine file type
        const fileType = file.type.startsWith('image/')
          ? 'brand_asset'
          : file.type.startsWith('audio/')
          ? 'audio'
          : 'other';

        // Upload with progress tracking
        const response = await uploadFileService(file, fileType, (progress) => {
          setUploads((prev) => {
            const current = prev.get(uploadId);
            if (!current) return prev;
            return new Map(prev).set(uploadId, {
              ...current,
              progress,
            });
          });

          options?.onProgress?.(progress, uploadId);
        });

        const asset = mapUploadResponseToAsset(response);

        // Update to success state
        setUploads((prev) => {
          const current = prev.get(uploadId);
          if (!current) return prev;
          return new Map(prev).set(uploadId, {
            ...current,
            progress: 100,
            status: 'success',
          });
        });

        options?.onSuccess?.(asset, uploadId);

        // Clean up after 2 seconds
        setTimeout(() => {
          setUploads((prev) => {
            const next = new Map(prev);
            next.delete(uploadId);
            return next;
          });
          abortControllers.current.delete(uploadId);
        }, 2000);

        return asset;
      } catch (error) {
        // Update to error state
        setUploads((prev) => {
          const current = prev.get(uploadId);
          if (!current) return prev;
          return new Map(prev).set(uploadId, {
            ...current,
            status: 'error',
            error: (error as Error).message,
          });
        });

        options?.onError?.(error as Error, uploadId);

        throw error;
      }
    },
    []
  );

  const uploadMultiple = useCallback(
    async (
      files: File[],
      options?: UploadOptions
    ): Promise<UploadedAsset[]> => {
      const promises = files.map((file) => uploadFile(file, options));
      return Promise.all(promises);
    },
    [uploadFile]
  );

  const cancelUpload = useCallback((uploadId: string) => {
    const controller = abortControllers.current.get(uploadId);
    if (controller) {
      controller.abort();
      abortControllers.current.delete(uploadId);
    }

    setUploads((prev) => {
      const next = new Map(prev);
      next.delete(uploadId);
      return next;
    });
  }, []);

  return {
    uploadFile,
    uploadMultiple,
    cancelUpload,
    uploads,
  };
}
