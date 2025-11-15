/**
 * Video Actions Component
 * Action buttons for video preview page (download, create another, history, share)
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/Button';
import { useVideoDownload } from '@/hooks/useVideoDownload';
import type { GenerationParameters } from '@/api/types';
import styles from './VideoActions.module.css';

export interface VideoActionsProps {
  compositionId: string;
  generationId: string;
  filename?: string;
  generationParameters?: GenerationParameters;
  onDownloadSuccess?: () => void;
  onDownloadError?: (error: Error) => void;
}

export function VideoActions({
  compositionId,
  generationId,
  filename,
  generationParameters,
  onDownloadSuccess,
  onDownloadError,
}: VideoActionsProps) {
  const navigate = useNavigate();
  const { isDownloading, progress, downloadVideo } = useVideoDownload();
  const [copied, setCopied] = useState(false);

  const handleDownload = async () => {
    try {
      await downloadVideo(compositionId, filename);
      onDownloadSuccess?.();
    } catch (error) {
      onDownloadError?.(error as Error);
    }
  };

  const handleCreateAnother = () => {
    // Navigate to home (generation form) with optional pre-filled parameters
    if (generationParameters) {
      navigate('/', { state: { parameters: generationParameters } });
    } else {
      navigate('/');
    }
  };

  const handleReturnToHistory = () => {
    navigate('/history');
  };

  const handleShare = async () => {
    const shareUrl = `${window.location.origin}/preview/${generationId}`;

    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy link:', error);
    }
  };

  return (
    <div className={styles.videoActions}>
      <div className={styles.primaryActions}>
        {/* Download Button - Primary action */}
        <Button
          variant="primary"
          size="lg"
          onClick={handleDownload}
          loading={isDownloading}
          disabled={isDownloading}
          className={styles.downloadButton}
        >
          {isDownloading
            ? `Downloading... ${progress?.percentage || 0}%`
            : 'Download Video'}
        </Button>

        {/* Download Progress Bar */}
        {isDownloading && progress && (
          <div className={styles.progressBar}>
            <div
              className={styles.progressFill}
              style={{ width: `${progress.percentage}%` }}
            />
          </div>
        )}
      </div>

      <div className={styles.secondaryActions}>
        {/* Create Another Video */}
        <Button
          variant="outline"
          size="md"
          onClick={handleCreateAnother}
          className={styles.actionButton}
        >
          Create Another Video
        </Button>

        {/* Return to History */}
        <Button
          variant="outline"
          size="md"
          onClick={handleReturnToHistory}
          className={styles.actionButton}
        >
          Return to History
        </Button>

        {/* Share (Copy Link) */}
        <Button
          variant="ghost"
          size="md"
          onClick={handleShare}
          className={styles.actionButton}
        >
          {copied ? 'Link Copied!' : 'Share Link'}
        </Button>
      </div>
    </div>
  );
}
