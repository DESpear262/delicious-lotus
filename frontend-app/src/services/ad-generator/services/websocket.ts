/**
 * WebSocket Service
 * High-level WebSocket service layer for generation and composition progress updates
 */

import { createWebSocketConnection } from '@/utils/ad-generator/websocket';
import { getGeneration } from './generation';
import { getComposition } from './composition';
import type {
  ProgressEvent,
  ClipCompletedEvent,
  StatusChangeEvent,
  CompletedEvent,
  ErrorEvent,
  EncodingProgressEvent,
} from '@/types/ad-generator/websocket';
import type { GetGenerationResponse, GetCompositionResponse } from '@/services/ad-generator/types';

/**
 * Generation progress event handlers
 */
export interface GenerationHandlers {
  /** Progress update handler */
  onProgress?: (data: ProgressEvent['data']) => void;
  /** Clip completed handler */
  onClipCompleted?: (data: ClipCompletedEvent['data']) => void;
  /** Status change handler */
  onStatusChange?: (data: StatusChangeEvent['data']) => void;
  /** Completion handler */
  onCompleted?: (data: CompletedEvent['data']) => void;
  /** Error handler */
  onError?: (data: ErrorEvent['data']) => void;
}

/**
 * Composition progress event handlers
 */
export interface CompositionHandlers {
  /** Encoding progress handler */
  onProgress?: (data: EncodingProgressEvent['data']) => void;
  /** Completion handler */
  onCompleted?: (data: any) => void;
  /** Error handler */
  onError?: (data: ErrorEvent['data']) => void;
}

/**
 * WebSocket service for real-time progress updates
 */
export class WebSocketService {
  /**
   * Subscribe to generation progress updates via WebSocket
   *
   * @param generationId - Generation ID to subscribe to
   * @param handlers - Event handlers for different event types
   * @returns Cleanup function to unsubscribe and disconnect
   *
   * @example
   * ```typescript
   * const unsubscribe = WebSocketService.subscribeToGeneration(
   *   generationId,
   *   {
   *     onProgress: (data) => console.log('Progress:', data.percentage),
   *     onCompleted: (data) => console.log('Video ready:', data.video_url),
   *     onError: (data) => console.error('Error:', data.message),
   *   }
   * );
   *
   * // Later, to cleanup:
   * unsubscribe();
   * ```
   */
  static subscribeToGeneration(
    generationId: string,
    handlers: GenerationHandlers
  ): () => void {
    const endpoint = `/ws/generations/${generationId}`;
    const wsManager = createWebSocketConnection(endpoint);

    // Subscribe to progress events
    if (handlers.onProgress) {
      wsManager.subscribe<ProgressEvent['data']>('progress', handlers.onProgress);
    }

    // Subscribe to clip completed events
    if (handlers.onClipCompleted) {
      wsManager.subscribe<ClipCompletedEvent['data']>(
        'clip_completed',
        handlers.onClipCompleted
      );
    }

    // Subscribe to status change events
    if (handlers.onStatusChange) {
      wsManager.subscribe<StatusChangeEvent['data']>(
        'status_change',
        handlers.onStatusChange
      );
    }

    // Subscribe to completion events
    if (handlers.onCompleted) {
      wsManager.subscribe<CompletedEvent['data']>('completed', handlers.onCompleted);
    }

    // Subscribe to error events
    if (handlers.onError) {
      wsManager.subscribe<ErrorEvent['data']>('error', handlers.onError);
    }

    // Return cleanup function
    return () => {
      wsManager.disconnect();
    };
  }

  /**
   * Subscribe to composition progress updates via WebSocket
   *
   * @param compositionId - Composition ID to subscribe to
   * @param handlers - Event handlers for different event types
   * @returns Cleanup function to unsubscribe and disconnect
   *
   * @example
   * ```typescript
   * const unsubscribe = WebSocketService.subscribeToComposition(
   *   compositionId,
   *   {
   *     onProgress: (data) => console.log('Encoding:', data.percentage),
   *     onCompleted: (data) => console.log('Composition ready'),
   *     onError: (data) => console.error('Error:', data.message),
   *   }
   * );
   *
   * // Later, to cleanup:
   * unsubscribe();
   * ```
   */
  static subscribeToComposition(
    compositionId: string,
    handlers: CompositionHandlers
  ): () => void {
    const endpoint = `/ws/compositions/${compositionId}`;
    const wsManager = createWebSocketConnection(endpoint);

    // Subscribe to encoding progress events
    if (handlers.onProgress) {
      wsManager.subscribe<EncodingProgressEvent['data']>(
        'encoding_progress',
        handlers.onProgress
      );
    }

    // Subscribe to completion events
    if (handlers.onCompleted) {
      wsManager.subscribe('completed', handlers.onCompleted);
    }

    // Subscribe to error events
    if (handlers.onError) {
      wsManager.subscribe<ErrorEvent['data']>('error', handlers.onError);
    }

    // Return cleanup function
    return () => {
      wsManager.disconnect();
    };
  }

  /**
   * Fallback polling for generation status
   * Used when WebSocket connection fails
   *
   * @param generationId - Generation ID to poll
   * @param onUpdate - Callback when status is updated
   * @param interval - Polling interval in milliseconds (default: 5000)
   * @returns Stop function to cancel polling
   *
   * @example
   * ```typescript
   * const stopPolling = await WebSocketService.pollGenerationStatus(
   *   generationId,
   *   (generation) => {
   *     console.log('Status:', generation.status);
   *     console.log('Progress:', generation.progress.percentage);
   *   },
   *   5000
   * );
   *
   * // Later, to stop polling:
   * stopPolling();
   * ```
   */
  static async pollGenerationStatus(
    generationId: string,
    onUpdate: (generation: GetGenerationResponse) => void,
    interval: number = 5000
  ): Promise<() => void> {
    let isPolling = true;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    const poll = async () => {
      if (!isPolling) {
        return;
      }

      try {
        const response = await getGeneration(generationId);
        onUpdate(response);

        // Stop polling if generation is complete or failed
        if (
          response.status === 'completed' ||
          response.status === 'failed' ||
          response.status === 'cancelled'
        ) {
          console.log('[WebSocketService] Generation finished, stopping polling');
          isPolling = false;
          return;
        }

        // Schedule next poll
        if (isPolling) {
          timeoutId = setTimeout(poll, interval);
        }
      } catch (error) {
        console.error('[WebSocketService] Polling error:', error);

        // Continue polling even on error
        if (isPolling) {
          timeoutId = setTimeout(poll, interval);
        }
      }
    };

    // Start polling
    poll();

    // Return stop function
    return () => {
      isPolling = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }

  /**
   * Fallback polling for composition status
   * Used when WebSocket connection fails
   *
   * @param compositionId - Composition ID to poll
   * @param onUpdate - Callback when status is updated
   * @param interval - Polling interval in milliseconds (default: 5000)
   * @returns Stop function to cancel polling
   *
   * @example
   * ```typescript
   * const stopPolling = await WebSocketService.pollCompositionStatus(
   *   compositionId,
   *   (composition) => {
   *     console.log('Status:', composition.status);
   *     console.log('Progress:', composition.progress.percentage);
   *   },
   *   5000
   * );
   *
   * // Later, to stop polling:
   * stopPolling();
   * ```
   */
  static async pollCompositionStatus(
    compositionId: string,
    onUpdate: (composition: GetCompositionResponse) => void,
    interval: number = 5000
  ): Promise<() => void> {
    let isPolling = true;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    const poll = async () => {
      if (!isPolling) {
        return;
      }

      try {
        const response = await getComposition(compositionId);
        onUpdate(response);

        // Stop polling if composition is complete or failed
        if (response.status === 'completed' || response.status === 'failed') {
          console.log('[WebSocketService] Composition finished, stopping polling');
          isPolling = false;
          return;
        }

        // Schedule next poll
        if (isPolling) {
          timeoutId = setTimeout(poll, interval);
        }
      } catch (error) {
        console.error('[WebSocketService] Polling error:', error);

        // Continue polling even on error
        if (isPolling) {
          timeoutId = setTimeout(poll, interval);
        }
      }
    };

    // Start polling
    poll();

    // Return stop function
    return () => {
      isPolling = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }
}
