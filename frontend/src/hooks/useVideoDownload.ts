/**
 * Video Download Hook
 * Manages video download functionality with progress tracking
 */

import { useState, useCallback } from 'react';
import { apiClient } from '@/api/client';

export interface DownloadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export interface UseVideoDownloadReturn {
  isDownloading: boolean;
  progress: DownloadProgress | null;
  error: Error | null;
  downloadVideo: (compositionId: string, filename?: string) => Promise<void>;
  reset: () => void;
}

/**
 * Hook for downloading videos with progress tracking
 */
export function useVideoDownload(): UseVideoDownloadReturn {
  const [isDownloading, setIsDownloading] = useState(false);
  const [progress, setProgress] = useState<DownloadProgress | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const downloadVideo = useCallback(
    async (compositionId: string, filename?: string) => {
      try {
        setIsDownloading(true);
        setError(null);
        setProgress({ loaded: 0, total: 0, percentage: 0 });

        const finalFilename = filename || `video_${compositionId}.mp4`;

        // Use axios with progress tracking
        const response = await apiClient.get(
          `/v1/compositions/${compositionId}/download`,
          {
            responseType: 'blob',
            onDownloadProgress: (progressEvent) => {
              const total = progressEvent.total || 0;
              const loaded = progressEvent.loaded || 0;
              const percentage = total > 0 ? Math.round((loaded / total) * 100) : 0;

              setProgress({
                loaded,
                total,
                percentage,
              });
            },
          }
        );

        // Create blob and trigger download
        const blob = response.data as Blob;
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = finalFilename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(downloadUrl);

        setIsDownloading(false);
        setProgress({ loaded: blob.size, total: blob.size, percentage: 100 });
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err : new Error('Download failed');
        setError(errorMessage);
        setIsDownloading(false);
        setProgress(null);
        throw errorMessage;
      }
    },
    []
  );

  const reset = useCallback(() => {
    setIsDownloading(false);
    setProgress(null);
    setError(null);
  }, []);

  return {
    isDownloading,
    progress,
    error,
    downloadVideo,
    reset,
  };
}
