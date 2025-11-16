import React, { Component, ErrorInfo, ReactNode } from 'react';
import { logError } from '@/utils/errors';
import styles from './ErrorBoundary.module.css';
import { Button } from './ui/Button';

/**
 * ErrorBoundary Props
 */
interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, reset: () => void) => ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

/**
 * ErrorBoundary State
 */
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * ErrorBoundary Component
 *
 * Catches React component errors and displays a fallback UI.
 * Implements React's error boundary lifecycle methods.
 *
 * Features:
 * - Catches rendering errors in child components
 * - Displays user-friendly error fallback UI
 * - Provides "Reload Page" functionality
 * - Logs errors to console (can be extended to error reporting service)
 * - Supports custom fallback UI via props
 *
 * @example
 * ```tsx
 * <ErrorBoundary>
 *   <YourComponent />
 * </ErrorBoundary>
 * ```
 */
export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  /**
   * Update state when error is caught
   */
  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  /**
   * Log error details when caught
   */
  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error for debugging
    logError(error, 'ErrorBoundary');

    // Log component stack
    console.error('Component Stack:', errorInfo.componentStack);

    // Call custom onError handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Update state with error info
    this.setState({
      errorInfo,
    });
  }

  /**
   * Reset error boundary state
   */
  resetError = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  /**
   * Reload the page
   */
  handleReload = (): void => {
    window.location.reload();
  };

  /**
   * Render fallback UI or children
   */
  render(): ReactNode {
    if (this.state.hasError && this.state.error) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.resetError);
      }

      // Default fallback UI
      return (
        <div className={styles.container}>
          <div className={styles.content}>
            <div className={styles.iconWrapper}>
              <svg
                className={styles.icon}
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>

            <h1 className={styles.title}>Something went wrong</h1>

            <p className={styles.message}>
              We encountered an unexpected error. Please try reloading the page.
              If the problem persists, contact support.
            </p>

            {/* Show error details in development */}
            {import.meta.env.DEV && this.state.error && (
              <details className={styles.details}>
                <summary className={styles.detailsSummary}>
                  Error Details (Development Only)
                </summary>
                <div className={styles.errorDetails}>
                  <div className={styles.errorMessage}>
                    <strong>Error:</strong> {this.state.error.toString()}
                  </div>
                  {this.state.error.stack && (
                    <div className={styles.errorStack}>
                      <strong>Stack Trace:</strong>
                      <pre>{this.state.error.stack}</pre>
                    </div>
                  )}
                  {this.state.errorInfo?.componentStack && (
                    <div className={styles.errorStack}>
                      <strong>Component Stack:</strong>
                      <pre>{this.state.errorInfo.componentStack}</pre>
                    </div>
                  )}
                </div>
              </details>
            )}

            <div className={styles.actions}>
              <Button onClick={this.handleReload} variant="primary" size="lg">
                Reload Page
              </Button>
              {import.meta.env.DEV && (
                <Button
                  onClick={this.resetError}
                  variant="secondary"
                  size="lg"
                >
                  Try Again
                </Button>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

ErrorBoundary.displayName = 'ErrorBoundary';
