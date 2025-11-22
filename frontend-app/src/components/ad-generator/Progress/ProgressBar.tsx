/**
 * ProgressBar Component
 * Displays overall progress with smooth animations and percentage
 */

import React from 'react';
import styles from './ProgressBar.module.css';

export interface ProgressBarProps {
  /** Progress percentage (0-100) */
  percentage: number;
  /** Status message to display */
  status?: string;
  /** Estimated time remaining in seconds */
  estimatedTime?: number | null;
  /** Progress bar variant */
  variant?: 'primary' | 'success' | 'error' | 'warning';
  /** Show percentage label */
  showPercentage?: boolean;
  /** Indeterminate/loading state */
  indeterminate?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Format seconds to human-readable time
 */
const formatTime = (seconds: number): string => {
  if (seconds < 60) {
    return `${seconds}s`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (minutes < 60) {
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
  }

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;

  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
};

/**
 * ProgressBar component for displaying generation progress
 */
export const ProgressBar: React.FC<ProgressBarProps> = ({
  percentage,
  status,
  estimatedTime,
  variant = 'primary',
  showPercentage = true,
  indeterminate = false,
  className = '',
}) => {
  // Clamp percentage to 0-100
  const clampedPercentage = Math.min(100, Math.max(0, percentage));

  const containerClasses = [styles.container, className].filter(Boolean).join(' ');

  const barClasses = [
    styles.bar,
    indeterminate && styles.indeterminate,
    styles[`bar-${variant}`],
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={containerClasses}>
      {/* Header with status and time */}
      <div className={styles.header}>
        <div className={styles.info}>
          {status && <p className={styles.status}>{status}</p>}
          {estimatedTime !== null && estimatedTime !== undefined && estimatedTime > 0 && (
            <p className={styles.time}>
              Estimated time: <span className={styles.timeValue}>{formatTime(estimatedTime)}</span>
            </p>
          )}
        </div>
        {showPercentage && !indeterminate && (
          <div className={styles.percentage}>
            <span className={styles.percentageValue}>{clampedPercentage}</span>
            <span className={styles.percentageSymbol}>%</span>
          </div>
        )}
      </div>

      {/* Progress bar track */}
      <div className={styles.track} role="progressbar" aria-valuenow={clampedPercentage} aria-valuemin={0} aria-valuemax={100}>
        <div
          className={barClasses}
          style={{
            width: indeterminate ? '100%' : `${clampedPercentage}%`,
          }}
        >
          {/* Animated shimmer effect */}
          <div className={styles.shimmer} />
        </div>
      </div>

      {/* Visual indicators for milestones */}
      {!indeterminate && (
        <div className={styles.milestones}>
          {[25, 50, 75].map((milestone) => (
            <div
              key={milestone}
              className={`${styles.milestone} ${
                clampedPercentage >= milestone ? styles.milestonePassed : ''
              }`}
              style={{ left: `${milestone}%` }}
            >
              <div className={styles.milestoneDot} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

ProgressBar.displayName = 'ProgressBar';
