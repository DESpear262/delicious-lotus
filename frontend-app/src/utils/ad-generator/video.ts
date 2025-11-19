/**
 * Video utility functions for the video player component
 */

/**
 * Format time in seconds to MM:SS or HH:MM:SS
 */
export function formatTime(seconds: number): string {
  if (!isFinite(seconds)) return '0:00';

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }

  return `${minutes}:${String(secs).padStart(2, '0')}`;
}

/**
 * Format file size in bytes to human-readable string
 */
export function formatFileSize(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return `${size.toFixed(1)} ${units[unitIndex]}`;
}

/**
 * Download video file
 */
export async function downloadVideo(
  url: string,
  filename?: string,
  onProgress?: (progress: number) => void
): Promise<void> {
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error('Download failed');

    const contentLength = response.headers.get('content-length');
    const total = contentLength ? parseInt(contentLength, 10) : 0;

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const chunks: BlobPart[] = [];
    let received = 0;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      chunks.push(value);
      received += value.length;

      if (onProgress && total > 0) {
        onProgress((received / total) * 100);
      }
    }

    const blob = new Blob(chunks, { type: 'video/mp4' });
    const blobUrl = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = filename || 'video.mp4';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(blobUrl);

  } catch (error) {
    console.error('Download error:', error);
    throw error;
  }
}

/**
 * Generate video thumbnail from video element
 */
export function generateThumbnail(
  videoElement: HTMLVideoElement,
  time: number = 0
): Promise<string> {
  return new Promise((resolve, reject) => {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');

    if (!context) {
      reject(new Error('Canvas context not available'));
      return;
    }

    const seekHandler = () => {
      canvas.width = videoElement.videoWidth;
      canvas.height = videoElement.videoHeight;
      context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

      const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
      resolve(dataUrl);

      videoElement.removeEventListener('seeked', seekHandler);
    };

    videoElement.addEventListener('seeked', seekHandler);
    videoElement.currentTime = time;
  });
}

/**
 * Check if video can play
 */
export function canPlayType(mimeType: string): boolean {
  const video = document.createElement('video');
  return video.canPlayType(mimeType) !== '';
}

/**
 * Get video metadata
 */
export async function getVideoMetadata(url: string): Promise<{
  duration: number;
  width: number;
  height: number;
}> {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video');

    video.onloadedmetadata = () => {
      resolve({
        duration: video.duration,
        width: video.videoWidth,
        height: video.videoHeight,
      });
    };

    video.onerror = () => {
      reject(new Error('Failed to load video metadata'));
    };

    video.src = url;
  });
}
