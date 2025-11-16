import React, { useEffect, useState } from 'react';
import styles from './OfflineBanner.module.css';

/**
 * OfflineBanner Props
 */
export interface OfflineBannerProps {
  /** Show banner when offline (default: true) */
  showWhenOffline?: boolean;
  /** Show banner when back online temporarily (default: true) */
  showWhenOnline?: boolean;
  /** Duration to show online banner in ms (default: 3000) */
  onlineDuration?: number;
  /** Custom offline message */
  offlineMessage?: string;
  /** Custom online message */
  onlineMessage?: string;
}

/**
 * OfflineBanner Component
 *
 * Displays a banner when the user's network connection is lost.
 * Auto-hides when the connection is restored.
 *
 * Features:
 * - Detects online/offline status using navigator.onLine
 * - Shows banner when offline
 * - Optionally shows "back online" message
 * - Auto-hides online message after duration
 * - Listens to window online/offline events
 * - Slide-down animation
 *
 * @example
 * ```tsx
 * <OfflineBanner />
 * ```
 */
export const OfflineBanner: React.FC<OfflineBannerProps> = ({
  showWhenOffline = true,
  showWhenOnline = true,
  onlineDuration = 3000,
  offlineMessage = 'No internet connection. Some features may be unavailable.',
  onlineMessage = 'Connection restored. You are back online.',
}) => {
  const [isOnline, setIsOnline] = useState<boolean>(navigator.onLine);
  const [showOnlineBanner, setShowOnlineBanner] = useState<boolean>(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);

      if (showWhenOnline) {
        setShowOnlineBanner(true);

        // Hide the online banner after duration
        const timer = setTimeout(() => {
          setShowOnlineBanner(false);
        }, onlineDuration);

        return () => clearTimeout(timer);
      }
    };

    const handleOffline = () => {
      setIsOnline(false);
      setShowOnlineBanner(false);
    };

    // Add event listeners
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Cleanup
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [showWhenOnline, onlineDuration]);

  // Show offline banner
  if (!isOnline && showWhenOffline) {
    return (
      <div
        className={`${styles.banner} ${styles.bannerOffline}`}
        role="alert"
        aria-live="assertive"
      >
        <div className={styles.content}>
          <div className={styles.iconWrapper}>
            <svg
              className={styles.icon}
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 6.707 6.293a1 1 0 00-1.414 1.414L8.586 11l-3.293 3.293a1 1 0 101.414 1.414L10 12.414l3.293 3.293a1 1 0 001.414-1.414L11.414 11l3.293-3.293z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <span className={styles.message}>{offlineMessage}</span>
        </div>
      </div>
    );
  }

  // Show online banner temporarily
  if (isOnline && showOnlineBanner) {
    return (
      <div
        className={`${styles.banner} ${styles.bannerOnline}`}
        role="status"
        aria-live="polite"
      >
        <div className={styles.content}>
          <div className={styles.iconWrapper}>
            <svg
              className={styles.icon}
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <span className={styles.message}>{onlineMessage}</span>
        </div>
      </div>
    );
  }

  return null;
};

OfflineBanner.displayName = 'OfflineBanner';
