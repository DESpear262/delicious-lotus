/**
 * Global Error Handler
 * Catches unhandled errors and promise rejections
 */

import { logError, getErrorMessage, shouldNotifyUser } from './errors';
import type { NotificationContextValue } from '@/contexts/ad-generator/NotificationContext';

/**
 * Global error handler instance
 */
let notificationHandler: NotificationContextValue | null = null;

/**
 * Initialize global error handler with notification system
 */
export const initializeGlobalErrorHandler = (
  notification: NotificationContextValue
): void => {
  notificationHandler = notification;

  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', handleUnhandledRejection);

  // Handle global errors (runtime errors)
  window.addEventListener('error', handleGlobalError);

  console.log('[Global Error Handler] Initialized');
};

/**
 * Cleanup global error handler
 */
export const cleanupGlobalErrorHandler = (): void => {
  window.removeEventListener('unhandledrejection', handleUnhandledRejection);
  window.removeEventListener('error', handleGlobalError);
  notificationHandler = null;

  console.log('[Global Error Handler] Cleaned up');
};

/**
 * Handle unhandled promise rejections
 */
const handleUnhandledRejection = (event: PromiseRejectionEvent): void => {
  event.preventDefault(); // Prevent default console error

  const error = event.reason;

  // Log the error
  logError(error, 'Unhandled Promise Rejection');

  // Show notification if appropriate
  if (notificationHandler && shouldNotifyUser(error)) {
    const message = getErrorMessage(error);
    notificationHandler.showError(message, 'Unexpected Error');
  }
};

/**
 * Handle global runtime errors
 */
const handleGlobalError = (event: ErrorEvent): void => {
  // Don't prevent default for script load errors
  if (event.error === null) {
    return;
  }

  event.preventDefault(); // Prevent default console error

  const error = event.error || new Error(event.message);

  // Log the error
  logError(error, 'Global Runtime Error');

  // Show notification if appropriate
  if (notificationHandler && shouldNotifyUser(error)) {
    const message = getErrorMessage(error);
    notificationHandler.showError(message, 'Unexpected Error');
  }
};

/**
 * Manually report an error to the global handler
 */
export const reportError = (
  error: unknown,
  context?: string,
  showNotification: boolean = true
): void => {
  // Log the error
  logError(error, context || 'Manual Error Report');

  // Show notification if requested
  if (showNotification && notificationHandler && shouldNotifyUser(error)) {
    const message = getErrorMessage(error);
    notificationHandler.showError(message, 'Error');
  }
};

/**
 * Check if global error handler is initialized
 */
export const isGlobalErrorHandlerInitialized = (): boolean => {
  return notificationHandler !== null;
};
