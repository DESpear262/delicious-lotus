// WebSocket Type Definitions

// ============================================================================
// Job Status Types
// ============================================================================

export type JobStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'canceled'
export type JobType = 'export' | 'ai_generation' | 'thumbnail' | 'processing'

// ============================================================================
// WebSocket Message Types
// ============================================================================

export interface JobUpdateMessage {
  event: 'job.queued' | 'job.running' | 'job.succeeded' | 'job.failed' | 'job.canceled'
  jobId: string
  jobType: JobType
  status: JobStatus
  progress?: number // 0-100
  message?: string
  error?: string
  result?: unknown // Job-specific result data
  timestamp: string
  // Backend snake_case variants (optional for compatibility)
  job_id?: string
  type?: string
  composition_id?: string
  compositionId?: string
  output_url?: string
}

export interface ExportJobResult {
  downloadUrl: string
  fileName: string
  fileSize: number
  duration: number
  format: string
}

export interface AIGenerationJobResult {
  assetId: string
  assetUrl: string
  thumbnailUrl: string
  prompt: string
  modelUsed: string
}

export interface PingMessage {
  event: 'ping'
  timestamp: string
}

export interface PongMessage {
  event: 'pong'
  timestamp: string
}

export type WebSocketMessage = JobUpdateMessage | PingMessage | PongMessage

// ============================================================================
// Connection Status Types
// ============================================================================

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'reconnecting' | 'error'

export interface ConnectionMetrics {
  status: ConnectionStatus
  latency?: number // milliseconds
  lastMessageTime?: Date
  reconnectAttempts: number
  messagesReceived: number
  messagesSent: number
}

// ============================================================================
// WebSocket Configuration Types
// ============================================================================

export interface WebSocketConfig {
  url: string
  heartbeatInterval?: number // milliseconds (default: 30000)
  pongTimeout?: number // milliseconds (default: 5000)
  reconnectInitialDelay?: number // milliseconds (default: 1000)
  reconnectMaxDelay?: number // milliseconds (default: 30000)
  reconnectBackoffMultiplier?: number // (default: 1.5)
  maxReconnectAttempts?: number // (default: 10)
  authToken?: string
}

// ============================================================================
// Event Callback Types
// ============================================================================

export type MessageHandler = (message: WebSocketMessage) => void
export type ConnectionHandler = (status: ConnectionStatus) => void
export type ErrorHandler = (error: Error) => void

// ============================================================================
// Message Queue Types
// ============================================================================

export interface QueuedMessage {
  id: string
  message: unknown
  timestamp: Date
  priority: 'normal' | 'high'
  retryCount: number
}

export interface MessageQueueConfig {
  maxSize?: number // default: 100
  persistToCritical?: boolean // default: false
}
