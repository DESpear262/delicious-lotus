# PR-F004: WebSocket Integration Implementation Plan

## Overview
Implement Socket.io client for real-time video generation and composition progress updates with auto-reconnection, offline message queuing, and fallback to polling.

**Estimated Time:** 3 hours  
**Dependencies:** PR-F001 ✅, PR-F003 ✅  
**Priority:** HIGH - Blocks PR-F009 (Progress Tracking)

## Goals
- Enable real-time progress updates during video generation
- Provide reliable WebSocket connection with auto-reconnection
- Implement graceful fallback to polling when WebSocket fails
- Support multiple concurrent job connections
- Ensure type-safe event handling with TypeScript

---

## Files to Create

### 1. `/home/user/delicious-lotus/frontend/src/types/websocket.ts`
**Purpose:** TypeScript interfaces for all WebSocket event types

**Interfaces to Define:**
```typescript
// Connection states
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

// Event types from API spec Section D
export type WebSocketEventType = 
  | 'progress' 
  | 'clip_completed' 
  | 'status_change' 
  | 'completed' 
  | 'error'
  | 'encoding_progress';

// Generation progress events
export interface ProgressEvent {
  type: 'progress';
  data: {
    step: string;
    clip_number: number;
    total_clips: number;
    percentage: number;
    message: string;
  };
}

export interface ClipCompletedEvent {
  type: 'clip_completed';
  data: {
    clip_id: string;
    thumbnail_url: string;
    duration: number;
  };
}

export interface StatusChangeEvent {
  type: 'status_change';
  data: {
    old_status: GenerationStatus;
    new_status: GenerationStatus;
    message: string;
  };
}

export interface CompletedEvent {
  type: 'completed';
  data: {
    video_url: string;
    thumbnail_url: string;
    duration: number;
  };
}

export interface ErrorEvent {
  type: 'error';
  data: {
    code: string;
    message: string;
    recoverable: boolean;
  };
}

// Composition progress events
export interface EncodingProgressEvent {
  type: 'encoding_progress';
  data: {
    percentage: number;
    frames_processed: number;
    total_frames: number;
    estimated_remaining: number;
  };
}

// Union type for all events
export type WebSocketEvent = 
  | ProgressEvent 
  | ClipCompletedEvent 
  | StatusChangeEvent 
  | CompletedEvent 
  | ErrorEvent
  | EncodingProgressEvent;

// Event handlers
export type EventHandler<T = any> = (data: T) => void;

// WebSocket configuration
export interface WebSocketConfig {
  url: string;
  reconnectionAttempts?: number;
  reconnectionDelay?: number;
  timeout?: number;
  enablePollingFallback?: boolean;
}

// Connection state
export interface ConnectionState {
  status: ConnectionStatus;
  connectedAt?: Date;
  disconnectedAt?: Date;
  reconnectAttempts: number;
  lastError?: Error;
}
```

**Key Features:**
- Strict typing for all event types from API spec
- Type-safe event handlers
- Connection state tracking
- Configuration options

---

### 2. `/home/user/delicious-lotus/frontend/src/utils/websocket.ts`
**Purpose:** Socket.io client configuration and connection manager

**Key Functions:**
```typescript
import { io, Socket } from 'socket.io-client';
import type { WebSocketConfig, ConnectionState, WebSocketEvent } from '../types/websocket';

export class WebSocketManager {
  private socket: Socket | null = null;
  private config: WebSocketConfig;
  private connectionState: ConnectionState;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private messageQueue: WebSocketEvent[] = [];
  
  constructor(config: WebSocketConfig) {
    // Initialize with config
    // Set default values for reconnection
  }
  
  connect(endpoint: string): Promise<void> {
    // Create Socket.io connection
    // Set up event listeners
    // Handle connection lifecycle
  }
  
  disconnect(): void {
    // Clean disconnect
    // Clear timers
    // Clean up resources
  }
  
  private handleConnect(): void {
    // Connection established
    // Flush message queue
    // Reset reconnect attempts
  }
  
  private handleDisconnect(reason: string): void {
    // Connection lost
    // Trigger reconnection logic
    // Update connection state
  }
  
  private handleReconnect(): void {
    // Exponential backoff: 1s, 2s, 4s, 8s, 16s (max)
    // Max 5 attempts before falling back to polling
  }
  
  subscribe<T>(eventType: string, handler: (data: T) => void): void {
    // Register event handler
    // Type-safe event subscription
  }
  
  unsubscribe(eventType: string, handler?: Function): void {
    // Remove event handler
    // Support removing all handlers for event
  }
  
  send(event: string, data: any): void {
    // Send message to server
    // Queue if offline
  }
  
  getConnectionState(): ConnectionState {
    // Return current state
  }
  
  private processMessageQueue(): void {
    // Process queued messages when reconnected
  }
}

// Factory function
export function createWebSocketConnection(
  endpoint: string,
  config?: Partial<WebSocketConfig>
): WebSocketManager {
  const defaultConfig: WebSocketConfig = {
    url: import.meta.env.VITE_WS_URL || window.location.origin,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    timeout: 300000, // 5 minutes
    enablePollingFallback: true,
  };
  
  return new WebSocketManager({ ...defaultConfig, ...config });
}
```

**Implementation Details:**
- Use Socket.io client library
- Exponential backoff for reconnection (1s, 2s, 4s, 8s, 16s max)
- Max 5 reconnection attempts
- 5-minute idle timeout
- Message queue for offline messages
- Include X-Request-ID in connection headers

---

### 3. `/home/user/delicious-lotus/frontend/src/utils/messageQueue.ts`
**Purpose:** Message queue for offline handling

**Key Functions:**
```typescript
export interface QueuedMessage {
  id: string;
  timestamp: Date;
  event: string;
  data: any;
  retries: number;
}

export class MessageQueue {
  private queue: QueuedMessage[] = [];
  private maxSize: number = 100;
  private maxRetries: number = 3;
  
  enqueue(event: string, data: any): string {
    // Add message to queue
    // Return message ID
    // Enforce size limit
  }
  
  dequeue(): QueuedMessage | null {
    // Remove and return oldest message
  }
  
  peek(): QueuedMessage | null {
    // View oldest without removing
  }
  
  remove(id: string): boolean {
    // Remove specific message
  }
  
  clear(): void {
    // Clear entire queue
  }
  
  size(): number {
    // Return queue size
  }
  
  incrementRetries(id: string): boolean {
    // Increment retry count
    // Return false if max retries exceeded
  }
  
  getAll(): QueuedMessage[] {
    // Return all messages
  }
  
  removeOldMessages(maxAge: number): void {
    // Remove messages older than maxAge (ms)
  }
}
```

**Implementation Details:**
- FIFO queue implementation
- Max 100 messages (configurable)
- Max 3 retries per message
- Auto-remove messages older than 1 hour
- Persist to localStorage for offline resilience

---

### 4. `/home/user/delicious-lotus/frontend/src/hooks/useWebSocket.ts`
**Purpose:** React hook for WebSocket connection management

**Hook Interface:**
```typescript
export interface UseWebSocketOptions {
  endpoint: string;
  autoConnect?: boolean;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
  enablePollingFallback?: boolean;
  pollingInterval?: number;
}

export interface UseWebSocketReturn {
  // Connection state
  isConnected: boolean;
  connectionStatus: ConnectionStatus;
  connectionState: ConnectionState;
  
  // Connection control
  connect: () => void;
  disconnect: () => void;
  reconnect: () => void;
  
  // Event management
  subscribe: <T>(eventType: string, handler: EventHandler<T>) => void;
  unsubscribe: (eventType: string, handler?: EventHandler) => void;
  emit: (event: string, data: any) => void;
  
  // Fallback polling
  enablePolling: () => void;
  disablePolling: () => void;
  isPolling: boolean;
}

export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  // State management
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [isPolling, setIsPolling] = useState(false);
  const wsManager = useRef<WebSocketManager | null>(null);
  const pollingTimer = useRef<NodeJS.Timeout | null>(null);
  
  // Initialize WebSocket manager
  useEffect(() => {
    // Create manager
    // Auto-connect if enabled
    return () => {
      // Cleanup on unmount
    };
  }, [options.endpoint]);
  
  // Connection handlers
  const connect = useCallback(() => {
    // Connect to WebSocket
  }, []);
  
  const disconnect = useCallback(() => {
    // Disconnect from WebSocket
  }, []);
  
  const reconnect = useCallback(() => {
    // Force reconnection
  }, []);
  
  // Event management
  const subscribe = useCallback(<T,>(eventType: string, handler: EventHandler<T>) => {
    // Subscribe to event
  }, []);
  
  const unsubscribe = useCallback((eventType: string, handler?: EventHandler) => {
    // Unsubscribe from event
  }, []);
  
  const emit = useCallback((event: string, data: any) => {
    // Send event
  }, []);
  
  // Polling fallback
  const enablePolling = useCallback(() => {
    // Start polling
    // Use generationService.getStatus() from API client
  }, []);
  
  const disablePolling = useCallback(() => {
    // Stop polling
  }, []);
  
  // Auto-fallback to polling on connection failure
  useEffect(() => {
    if (options.enablePollingFallback && connectionStatus === 'error') {
      enablePolling();
    }
  }, [connectionStatus, options.enablePollingFallback]);
  
  return {
    isConnected: connectionStatus === 'connected',
    connectionStatus,
    connectionState: wsManager.current?.getConnectionState() ?? initialState,
    connect,
    disconnect,
    reconnect,
    subscribe,
    unsubscribe,
    emit,
    enablePolling,
    disablePolling,
    isPolling,
  };
}
```

**Implementation Details:**
- Manages WebSocket lifecycle in React
- Auto-cleanup on unmount
- Callback-based event system
- Automatic polling fallback
- Stable references with useCallback
- Type-safe event handlers

---

### 5. `/home/user/delicious-lotus/frontend/src/api/services/websocket.ts`
**Purpose:** WebSocket service layer integration with API client

**Key Functions:**
```typescript
import { apiClient } from '../client';
import type { Generation, Composition } from '../types';

export class WebSocketService {
  /**
   * Subscribe to generation progress updates
   */
  static subscribeToGeneration(
    generationId: string,
    handlers: {
      onProgress?: (data: ProgressEvent['data']) => void;
      onClipCompleted?: (data: ClipCompletedEvent['data']) => void;
      onStatusChange?: (data: StatusChangeEvent['data']) => void;
      onCompleted?: (data: CompletedEvent['data']) => void;
      onError?: (data: ErrorEvent['data']) => void;
    }
  ): () => void {
    // Create WebSocket connection to /ws/generations/{id}
    // Register handlers
    // Return cleanup function
  }
  
  /**
   * Subscribe to composition progress updates
   */
  static subscribeToComposition(
    compositionId: string,
    handlers: {
      onProgress?: (data: EncodingProgressEvent['data']) => void;
      onCompleted?: (data: any) => void;
      onError?: (data: ErrorEvent['data']) => void;
    }
  ): () => void {
    // Create WebSocket connection to /ws/compositions/{id}
    // Register handlers
    // Return cleanup function
  }
  
  /**
   * Fallback polling for generation status
   */
  static async pollGenerationStatus(
    generationId: string,
    onUpdate: (generation: Generation) => void,
    interval: number = 5000
  ): Promise<() => void> {
    // Use generationService.getStatus()
    // Poll every interval
    // Call onUpdate with latest status
    // Return stop function
  }
  
  /**
   * Fallback polling for composition status
   */
  static async pollCompositionStatus(
    compositionId: string,
    onUpdate: (composition: Composition) => void,
    interval: number = 5000
  ): Promise<() => void> {
    // Use compositionService.getStatus()
    // Poll every interval
    // Call onUpdate with latest status
    // Return stop function
  }
}
```

**Implementation Details:**
- High-level API for subscribing to updates
- Integrates with existing API client
- Provides both WebSocket and polling options
- Returns cleanup functions for React useEffect
- Type-safe handlers

---

### 6. `/home/user/delicious-lotus/frontend/src/components/ConnectionStatus.tsx`
**Purpose:** Connection status indicator component

**Component Interface:**
```typescript
interface ConnectionStatusProps {
  status: ConnectionStatus;
  isPolling?: boolean;
  onReconnect?: () => void;
  className?: string;
}

export function ConnectionStatus({
  status,
  isPolling,
  onReconnect,
  className
}: ConnectionStatusProps): JSX.Element {
  // Display connection status badge
  // Show polling indicator if polling
  // Show reconnect button if disconnected
  // Use design system colors and components
}
```

**UI Elements:**
- Badge showing connection status (green/yellow/red)
- "Polling" indicator when using fallback
- "Reconnect" button when disconnected
- Tooltip with last connection time
- Uses Button and Toast from design system

---

## Files to Modify

None - all new files.

---

## Dependencies

### NPM Packages
- `socket.io-client`: ^4.7.2 (already added in PR-F001)

### Internal Dependencies
- `/frontend/src/api/client.ts` - API client for polling fallback
- `/frontend/src/api/services/generation.ts` - Generation API methods
- `/frontend/src/api/services/composition.ts` - Composition API methods
- `/frontend/src/api/types.ts` - Shared type definitions
- `/frontend/src/components/ui/Button.tsx` - Design system button
- `/frontend/src/components/ui/Toast.tsx` - Design system toast

---

## API Integration

### WebSocket Endpoints (from api-specification-edited.md Section D)

#### 1. Generation Progress WebSocket
**Endpoint:** `/ws/generations/{generation_id}`

**Client to Server:**
```json
{
  "type": "subscribe",
  "generation_id": "gen_abc123xyz"
}
```

**Server to Client Events:**
- `progress` - Step updates with percentage
- `clip_completed` - Individual clip completion
- `status_change` - Status transitions
- `completed` - Final video ready
- `error` - Error notifications

#### 2. Composition Progress WebSocket
**Endpoint:** `/ws/compositions/{composition_id}`

**Server to Client Events:**
- `encoding_progress` - Frame-level progress updates

### Polling Fallback Endpoints

#### Generation Status Polling
**Endpoint:** `GET /api/v1/generations/{generation_id}`
**Interval:** Every 5 seconds
**Stop Condition:** Status is "completed", "failed", or "cancelled"

#### Composition Status Polling
**Endpoint:** `GET /api/v1/compositions/{composition_id}`
**Interval:** Every 5 seconds
**Stop Condition:** Status is "completed" or "failed"

---

## Implementation Details

### Step 1: Create Type Definitions (30 minutes)
1. Create `types/websocket.ts`
2. Define all interfaces from API spec Section D
3. Export type guards for event validation
4. Add JSDoc comments for all types

### Step 2: Build WebSocket Manager (45 minutes)
1. Create `utils/websocket.ts`
2. Implement WebSocketManager class
3. Add connection lifecycle management
4. Implement exponential backoff reconnection
5. Add message queuing for offline messages
6. Include X-Request-ID in connection headers

### Step 3: Implement Message Queue (30 minutes)
1. Create `utils/messageQueue.ts`
2. Implement FIFO queue with max size
3. Add retry tracking
4. Add localStorage persistence
5. Implement auto-cleanup of old messages

### Step 4: Create React Hook (45 minutes)
1. Create `hooks/useWebSocket.ts`
2. Wrap WebSocketManager in React hook
3. Manage lifecycle with useEffect
4. Provide stable callback references
5. Implement polling fallback logic
6. Add auto-reconnection on connection loss

### Step 5: Build Service Layer (30 minutes)
1. Create `api/services/websocket.ts`
2. Implement subscribeToGeneration()
3. Implement subscribeToComposition()
4. Implement polling fallback methods
5. Integrate with existing API client
6. Add error handling and logging

### Step 6: Create Status Component (30 minutes)
1. Create `components/ConnectionStatus.tsx`
2. Display connection status badge
3. Add polling indicator
4. Add reconnect button
5. Style with design system
6. Add tooltips and accessibility

---

## State Management Approach

### WebSocket State
- Store in React hook state (local to component using WebSocket)
- Connection status: `useState<ConnectionStatus>`
- Connection state: `useRef<WebSocketManager>`
- Polling state: `useState<boolean>`

### Message Queue State
- Managed internally in WebSocketManager
- Persisted to localStorage for offline resilience
- Cleared on successful reconnection

### Event Handlers
- Registered via subscribe/unsubscribe methods
- Stored in Map<eventType, Set<handler>>
- Auto-cleanup on component unmount

---

## Error Handling Strategy

### Connection Errors
1. **Initial Connection Failure:**
   - Try reconnection with exponential backoff
   - Max 5 attempts
   - Fall back to polling after 5 failures

2. **Mid-Session Disconnect:**
   - Attempt immediate reconnection
   - Use exponential backoff if immediate fails
   - Queue messages during offline period
   - Flush queue on reconnection

3. **Timeout Errors:**
   - 5-minute idle timeout
   - Send ping/pong heartbeat every 30 seconds
   - Reconnect if no pong response

### Message Errors
1. **Invalid Message Format:**
   - Log error to console
   - Display user-friendly error toast
   - Continue listening for valid messages

2. **Handler Errors:**
   - Wrap handler execution in try-catch
   - Log error but don't crash connection
   - Notify via error callback

### Fallback Strategy
1. **WebSocket Unavailable:**
   - Automatically enable polling
   - Poll every 5 seconds
   - Show "Polling" indicator to user

2. **Polling Errors:**
   - Use retry logic from API client (exponential backoff)
   - Max 3 retries per poll
   - Show error toast if all retries fail

---

## Acceptance Criteria

- [ ] Socket.io client configured with auto-reconnection
- [ ] Custom `useWebSocket` hook with:
  - [ ] Connection state management
  - [ ] Automatic reconnection with exponential backoff (1s, 2s, 4s, 8s, 16s)
  - [ ] Message queue for offline messages (max 100, max 3 retries)
  - [ ] Event subscription/unsubscription
- [ ] Event handlers for generation progress:
  - [ ] `progress` - Step updates with percentage
  - [ ] `clip_completed` - Individual clip completion
  - [ ] `status_change` - Status transitions
  - [ ] `completed` - Final video ready
  - [ ] `error` - Error notifications
- [ ] Event handlers for composition progress:
  - [ ] `encoding_progress` - Frame-level progress
- [ ] Graceful fallback to polling if WebSocket fails (5s interval)
- [ ] Connection status indicator component with:
  - [ ] Visual status (green/yellow/red)
  - [ ] Polling indicator
  - [ ] Reconnect button
- [ ] TypeScript types for all message formats (from API spec)
- [ ] Reconnection logic (5min idle timeout, immediate reconnect on disconnect)
- [ ] Message validation and error handling
- [ ] X-Request-ID in connection headers
- [ ] Support for multiple concurrent connections
- [ ] Heartbeat ping/pong every 30 seconds
- [ ] localStorage persistence for message queue

---

## Testing Approach

### Unit Tests
1. **WebSocketManager:**
   - Test connection lifecycle
   - Test reconnection with backoff
   - Test message queuing
   - Test event subscription/unsubscription

2. **MessageQueue:**
   - Test enqueue/dequeue
   - Test size limits
   - Test retry tracking
   - Test old message cleanup

3. **useWebSocket Hook:**
   - Test with @testing-library/react-hooks
   - Test auto-connect
   - Test cleanup on unmount
   - Test polling fallback

### Integration Tests
1. **Mock WebSocket Server:**
   - Create mock Socket.io server
   - Test full message flow
   - Test reconnection scenarios
   - Test error handling

2. **Polling Fallback:**
   - Mock failed WebSocket connection
   - Verify polling starts automatically
   - Verify correct polling interval
   - Verify polling stops when reconnected

### Manual Testing
1. **Connection Flow:**
   - Open app, verify auto-connect
   - Monitor connection status
   - Disconnect network, verify reconnection
   - Verify message queue works offline

2. **Event Handling:**
   - Start generation job
   - Verify progress events received
   - Verify clip completion events
   - Verify final completion event

3. **Error Scenarios:**
   - Kill WebSocket server
   - Verify fallback to polling
   - Verify reconnection on server restart
   - Verify error messages displayed

### Browser Testing
- Chrome, Firefox, Safari, Edge
- Test on mobile browsers (iOS Safari, Chrome Android)
- Test with network throttling
- Test with DevTools to simulate offline

---

## Environment Variables

```bash
# WebSocket Configuration
VITE_WS_URL=ws://localhost:8000  # WebSocket server URL (defaults to same origin)
VITE_WS_RECONNECT_ATTEMPTS=5     # Max reconnection attempts
VITE_WS_RECONNECT_DELAY=1000     # Initial reconnection delay (ms)
VITE_WS_TIMEOUT=300000           # Idle timeout (ms) - 5 minutes
VITE_WS_HEARTBEAT_INTERVAL=30000 # Heartbeat interval (ms)
VITE_POLLING_INTERVAL=5000       # Polling interval when WS fails (ms)
VITE_ENABLE_POLLING_FALLBACK=true # Enable auto-fallback to polling
```

---

## Performance Considerations

1. **Connection Pooling:**
   - Reuse WebSocket connections when possible
   - Support multiple subscriptions per connection
   - Clean up unused connections

2. **Message Throttling:**
   - Debounce rapid progress updates (max 10/sec)
   - Batch status updates

3. **Memory Management:**
   - Limit message queue size (100 messages)
   - Clear old messages (1 hour TTL)
   - Cleanup event handlers on unmount

4. **Network Efficiency:**
   - Use binary format for large messages (if needed)
   - Compress JSON messages
   - Minimize heartbeat frequency (30s)

---

## Security Considerations

1. **Authentication:**
   - Send session cookie with WebSocket handshake
   - Validate user permissions on server

2. **Message Validation:**
   - Validate all incoming messages
   - Sanitize user-provided data
   - Type-check events

3. **Rate Limiting:**
   - Respect server rate limits (5 concurrent connections)
   - Throttle client-side events

4. **CORS:**
   - Configure CORS for WebSocket endpoint
   - Use same-origin policy for production

---

## Migration Notes

None - this is new functionality.

---

## Documentation

1. **Code Comments:**
   - JSDoc for all public functions
   - Inline comments for complex logic
   - Example usage in hook documentation

2. **Usage Examples:**
   ```typescript
   // Basic usage
   const { isConnected, subscribe, disconnect } = useWebSocket({
     endpoint: `/ws/generations/${generationId}`,
     autoConnect: true,
     onConnect: () => console.log('Connected'),
   });
   
   // Subscribe to events
   useEffect(() => {
     subscribe<ProgressEvent['data']>('progress', (data) => {
       console.log('Progress:', data.percentage);
     });
     
     subscribe<CompletedEvent['data']>('completed', (data) => {
       console.log('Video ready:', data.video_url);
     });
     
     return () => disconnect();
   }, [subscribe, disconnect]);
   ```

3. **Troubleshooting Guide:**
   - Common connection issues
   - How to enable polling fallback
   - Debugging WebSocket messages
   - Performance optimization tips

---

## Follow-up Tasks

1. **PR-F009:** Use WebSocket hook in Progress Tracking component
2. **PR-F010:** Use WebSocket for composition progress
3. **Monitoring:** Add analytics for connection success/failure rates
4. **Optimization:** Implement message compression if needed
5. **Testing:** Add E2E tests with Playwright

---

## Success Criteria

This PR is successful when:
1. WebSocket connection establishes reliably
2. All event types are received and handled correctly
3. Reconnection works automatically after disconnect
4. Polling fallback activates when WebSocket fails
5. Multiple concurrent connections work without conflicts
6. No memory leaks in long-running sessions
7. Connection status is clearly visible to users
8. All acceptance criteria are met
9. Code passes TypeScript strict mode
10. Integration tests pass with mock WebSocket server
