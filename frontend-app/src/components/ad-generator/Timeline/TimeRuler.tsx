/**
 * TimeRuler Component
 * Displays time ruler with markers and current time indicator
 */

import React, { useRef, useCallback } from 'react';
import { formatTime } from '@/utils/ad-generator/timeline';
import styles from './TimeRuler.module.css';

export interface TimeRulerProps {
  /** Total duration in seconds */
  duration: number;
  /** Current playhead time in seconds */
  currentTime: number;
  /** Pixels per second for zoom */
  pixelsPerSecond: number;
  /** Callback when user clicks on ruler to seek */
  onSeek: (time: number) => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * TimeRuler Component
 * Horizontal time ruler with markers, labels, and playhead
 */
export const TimeRuler: React.FC<TimeRulerProps> = ({
  duration,
  currentTime,
  pixelsPerSecond,
  onSeek,
  className = '',
}) => {
  const rulerRef = useRef<HTMLDivElement>(null);

  // Calculate total width
  const totalWidth = duration * pixelsPerSecond;

  // Calculate marker interval based on zoom level
  const getMarkerInterval = (): number => {
    if (pixelsPerSecond >= 80) return 1; // Every second
    if (pixelsPerSecond >= 40) return 2; // Every 2 seconds
    if (pixelsPerSecond >= 20) return 5; // Every 5 seconds
    return 10; // Every 10 seconds
  };

  const markerInterval = getMarkerInterval();

  // Generate time markers
  const markers: number[] = [];
  for (let time = 0; time <= duration; time += markerInterval) {
    markers.push(time);
  }

  // Handle click on ruler to seek
  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!rulerRef.current) return;

      const rect = rulerRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const time = Math.max(0, Math.min((x / pixelsPerSecond), duration));
      onSeek(time);
    },
    [pixelsPerSecond, duration, onSeek]
  );

  // Calculate playhead position
  const playheadPosition = currentTime * pixelsPerSecond;

  return (
    <div className={`${styles.timeRuler} ${className}`}>
      <div
        ref={rulerRef}
        className={styles.timeRuler__track}
        style={{ width: `${totalWidth}px` }}
        onClick={handleClick}
      >
        {/* Time markers */}
        {markers.map(time => {
          const position = time * pixelsPerSecond;
          const isMajor = time % (markerInterval * 2) === 0;

          return (
            <div
              key={time}
              className={`${styles.timeRuler__marker} ${
                isMajor ? styles['timeRuler__marker--major'] : styles['timeRuler__marker--minor']
              }`}
              style={{ left: `${position}px` }}
            >
              <div className={styles.timeRuler__tick} />
              {isMajor && (
                <div className={styles.timeRuler__label}>
                  {formatTime(time)}
                </div>
              )}
            </div>
          );
        })}

        {/* Playhead indicator */}
        <div
          className={styles.timeRuler__playhead}
          style={{ left: `${playheadPosition}px` }}
        >
          <div className={styles.timeRuler__playheadLine} />
          <div className={styles.timeRuler__playheadHandle} />
        </div>
      </div>
    </div>
  );
};

TimeRuler.displayName = 'TimeRuler';
