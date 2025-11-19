/**
 * useNotification Hook
 * Provides access to the global notification system
 */

import { useContext } from 'react';
import {
  NotificationContext,
  type NotificationContextValue,
} from '@/contexts/ad-generator/NotificationContext';

/**
 * useNotification Hook
 *
 * Provides access to the global notification/toast system.
 * Must be used within a NotificationProvider.
 *
 * @throws Error if used outside NotificationProvider
 *
 * @returns Notification context methods
 *
 * @example
 * ```tsx
 * const { showSuccess, showError } = useNotification();
 *
 * // Show success message
 * showSuccess('Your changes have been saved!');
 *
 * // Show error with custom title
 * showError('Unable to save changes', 'Save Failed');
 *
 * // Show custom notification
 * showNotification({
 *   type: 'warning',
 *   title: 'Warning',
 *   message: 'This action cannot be undone',
 *   duration: 10000,
 * });
 * ```
 */
export const useNotification = (): NotificationContextValue => {
  const context = useContext(NotificationContext);

  if (!context) {
    throw new Error(
      'useNotification must be used within a NotificationProvider. ' +
        'Wrap your component tree with <NotificationProvider>.'
    );
  }

  return context;
};
