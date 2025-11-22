/**
 * ConnectionStatus Component
 * Visual indicator for WebSocket connection status with reconnect functionality
 */

import React from 'react';
import type { ConnectionStatus as ConnectionStatusType } from '@/types/ad-generator/websocket';
import { Button } from './ui/Button';

export interface ConnectionStatusProps {
  /** Current connection status */
  status: ConnectionStatusType;
  /** Whether polling fallback is active */
  isPolling?: boolean;
  /** Callback when reconnect button is clicked */
  onReconnect?: () => void;
  /** Additional CSS class name */
  className?: string;
  /** Show detailed status text (default: true) */
  showText?: boolean;
  /** Compact mode - only show icon (default: false) */
  compact?: boolean;
}

/**
 * Connection status badge with visual indicator and reconnect button
 *
 * @example
 * ```typescript
 * <ConnectionStatus
 *   status={connectionStatus}
 *   isPolling={isPolling}
 *   onReconnect={() => reconnect()}
 * />
 * ```
 */
export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  status,
  isPolling = false,
  onReconnect,
  className = '',
  showText = true,
  compact = false,
}) => {
  /**
   * Get status color
   */
  const getStatusColor = (): string => {
    switch (status) {
      case 'connected':
        return '#10b981'; // green
      case 'connecting':
        return '#f59e0b'; // yellow
      case 'disconnected':
        return '#6b7280'; // gray
      case 'error':
        return '#ef4444'; // red
      default:
        return '#6b7280'; // gray
    }
  };

  /**
   * Get status text
   */
  const getStatusText = (): string => {
    if (isPolling) {
      return 'Polling';
    }

    switch (status) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'disconnected':
        return 'Disconnected';
      case 'error':
        return 'Connection Error';
      default:
        return 'Unknown';
    }
  };

  /**
   * Get status description for tooltip
   */
  const getStatusDescription = (): string => {
    if (isPolling) {
      return 'Using polling fallback for updates';
    }

    switch (status) {
      case 'connected':
        return 'Real-time updates active';
      case 'connecting':
        return 'Establishing connection...';
      case 'disconnected':
        return 'Not connected to server';
      case 'error':
        return 'Failed to connect. Click to retry.';
      default:
        return '';
    }
  };

  const statusColor = getStatusColor();
  const statusText = getStatusText();
  const statusDescription = getStatusDescription();

  const containerStyles: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: compact ? '4px' : '8px',
    padding: compact ? '4px 8px' : '6px 12px',
    borderRadius: '6px',
    backgroundColor: 'rgba(0, 0, 0, 0.05)',
    fontSize: compact ? '12px' : '14px',
    fontWeight: 500,
  };

  const dotStyles: React.CSSProperties = {
    width: compact ? '6px' : '8px',
    height: compact ? '6px' : '8px',
    borderRadius: '50%',
    backgroundColor: statusColor,
    flexShrink: 0,
    animation: status === 'connecting' ? 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite' : 'none',
  };

  const textStyles: React.CSSProperties = {
    color: '#374151',
    whiteSpace: 'nowrap',
  };

  const pollingBadgeStyles: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '2px 6px',
    borderRadius: '4px',
    backgroundColor: '#fef3c7',
    color: '#92400e',
    fontSize: '11px',
    fontWeight: 600,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
  };

  return (
    <div className={className} style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
      {/* Status Badge */}
      <div
        style={containerStyles}
        title={statusDescription}
        role="status"
        aria-label={`Connection status: ${statusText}`}
      >
        <span style={dotStyles} aria-hidden="true" />
        {!compact && showText && <span style={textStyles}>{statusText}</span>}
      </div>

      {/* Polling Indicator */}
      {isPolling && !compact && (
        <span style={pollingBadgeStyles} title="Using polling fallback for updates">
          Polling
        </span>
      )}

      {/* Reconnect Button */}
      {(status === 'disconnected' || status === 'error') && onReconnect && !compact && (
        <Button
          variant="outline"
          size="sm"
          onClick={onReconnect}
          aria-label="Reconnect to server"
        >
          Reconnect
        </Button>
      )}

      {/* Inline CSS for pulse animation */}
      <style>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }
      `}</style>
    </div>
  );
};

ConnectionStatus.displayName = 'ConnectionStatus';
