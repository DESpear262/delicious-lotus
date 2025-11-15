/**
 * ClipPreview Component
 * Displays individual clip preview with thumbnail, duration, and status
 */

import React, { useState } from 'react';
import styles from './ClipPreview.module.css';

export interface ClipPreviewProps {
  /** Clip ID */
  clipId: string;
  /** Thumbnail URL */
  thumbnailUrl?: string;
  /** Clip duration in seconds */
  duration: number;
  /** Clip number in sequence */
  clipNumber?: number;
  /** Clip status */
  status?: 'generating' | 'completed' | 'error';
  /** On click handler */
  onClick?: () => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Format duration to MM:SS
 */
const formatDuration = (seconds: number): string => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

/**
 * ClipPreview component for displaying generated clips
 */
export const ClipPreview: React.FC<ClipPreviewProps> = ({
  clipId,
  thumbnailUrl,
  duration,
  clipNumber,
  status = 'completed',
  onClick,
  className = '',
}) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const containerClasses = [
    styles.container,
    status === 'generating' && styles.containerGenerating,
    onClick && styles.containerClickable,
    className,
  ]
    .filter(Boolean)
    .join(' ');

  const handleImageLoad = () => {
    setImageLoaded(true);
  };

  const handleImageError = () => {
    setImageError(true);
  };

  return (
    <div className={containerClasses} onClick={onClick} role={onClick ? 'button' : undefined} tabIndex={onClick ? 0 : undefined}>
      {/* Thumbnail */}
      <div className={styles.thumbnail}>
        {status === 'generating' ? (
          // Loading skeleton for generating clips
          <div className={styles.skeleton}>
            <div className={styles.skeletonAnimation} />
            <div className={styles.loadingSpinner}>
              <svg
                className={styles.spinner}
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className={styles.spinnerCircle}
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className={styles.spinnerPath}
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            </div>
          </div>
        ) : imageError || !thumbnailUrl ? (
          // Error/fallback state
          <div className={styles.fallback}>
            <svg
              className={styles.fallbackIcon}
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <polyline points="21 15 16 10 5 21" />
            </svg>
          </div>
        ) : (
          <>
            {/* Loading skeleton while image loads */}
            {!imageLoaded && (
              <div className={styles.skeleton}>
                <div className={styles.skeletonAnimation} />
              </div>
            )}
            {/* Actual image */}
            <img
              src={thumbnailUrl}
              alt={`Clip ${clipNumber || clipId}`}
              className={`${styles.image} ${imageLoaded ? styles.imageLoaded : ''}`}
              onLoad={handleImageLoad}
              onError={handleImageError}
            />
          </>
        )}

        {/* Duration badge */}
        {status !== 'generating' && (
          <div className={styles.durationBadge}>
            <span className={styles.duration}>{formatDuration(duration)}</span>
          </div>
        )}

        {/* Status indicator */}
        {status === 'error' && (
          <div className={styles.errorBadge}>
            <svg
              className={styles.errorIcon}
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
        )}
      </div>

      {/* Clip info */}
      <div className={styles.info}>
        {clipNumber !== undefined && (
          <span className={styles.clipNumber}>Clip {clipNumber}</span>
        )}
        {status === 'generating' && (
          <span className={styles.statusLabel}>Generating...</span>
        )}
        {status === 'error' && (
          <span className={`${styles.statusLabel} ${styles.statusError}`}>Failed</span>
        )}
      </div>
    </div>
  );
};

ClipPreview.displayName = 'ClipPreview';

/**
 * ClipPreview grid container for displaying multiple clips
 */
export interface ClipPreviewGridProps {
  children: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
}

export const ClipPreviewGrid: React.FC<ClipPreviewGridProps> = ({
  children,
  className = '',
}) => {
  return <div className={`${styles.grid} ${className}`}>{children}</div>;
};

ClipPreviewGrid.displayName = 'ClipPreviewGrid';
