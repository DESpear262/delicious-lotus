/**
 * Video Actions Component
 * Action buttons for video preview page (download, create another, history, share)
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ROUTES } from '../../types/routes';

import { Button } from './ui/Button';
import { useVideoDownload } from '@/hooks/ad-generator/useVideoDownload';
import type { GenerationParameters } from '@/services/ad-generator/types';


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
    navigate(`${ROUTES.AD_GENERATOR}/history`);
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
    <div className="flex flex-col gap-6 w-full">
      <div className="flex flex-col gap-2 w-full">
        {/* Download Button - Primary action */}
        <Button
          variant="primary"
          size="lg"
          onClick={handleDownload}
          loading={isDownloading}
          disabled={isDownloading}
          className="w-full text-lg py-6"
        >
          {isDownloading
            ? `Downloading... ${progress?.percentage || 0}%`
            : 'Download Video'}
        </Button>

        {/* Download Progress Bar */}
        {isDownloading && progress && (
          <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-300 ease-in-out"
              style={{ width: `${progress.percentage}%` }}
            />
          </div>
        )}
      </div>

      <div className="flex flex-col gap-3 w-full sm:flex-row sm:flex-wrap">
        {/* Create Another Video */}
        <Button
          variant="outline"
          size="md"
          onClick={handleCreateAnother}
          className="flex-1"
        >
          Create Another Video
        </Button>

        {/* Return to History */}
        <Button
          variant="outline"
          size="md"
          onClick={handleReturnToHistory}
          className="flex-1"
        >
          Return to History
        </Button>

        {/* Share (Copy Link) */}
        <Button
          variant="ghost"
          size="md"
          onClick={handleShare}
          className="flex-1"
        >
          {copied ? 'Link Copied!' : 'Share Link'}
        </Button>
      </div>
    </div>
  );
}
