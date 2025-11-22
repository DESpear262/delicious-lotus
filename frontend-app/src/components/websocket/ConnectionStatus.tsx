import { Wifi, WifiOff, AlertCircle, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ConnectionStatus as Status } from '@/types/websocket'

interface ConnectionStatusProps {
  status: Status
  className?: string
  showLabel?: boolean
  showMetrics?: boolean
  latency?: number
  reconnectAttempts?: number
}

export function ConnectionStatus({
  status,
  className,
  showLabel = false,
  showMetrics = false,
  latency,
  reconnectAttempts,
}: ConnectionStatusProps) {
  const getStatusConfig = (status: Status) => {
    switch (status) {
      case 'connected':
        return {
          icon: Wifi,
          color: 'text-green-500',
          bgColor: 'bg-green-500/10',
          label: 'Connected',
          pulse: false,
        }
      case 'connecting':
        return {
          icon: Loader2,
          color: 'text-yellow-500',
          bgColor: 'bg-yellow-500/10',
          label: 'Connecting...',
          pulse: true,
        }
      case 'reconnecting':
        return {
          icon: Loader2,
          color: 'text-orange-500',
          bgColor: 'bg-orange-500/10',
          label: reconnectAttempts ? `Reconnecting (${reconnectAttempts})...` : 'Reconnecting...',
          pulse: true,
        }
      case 'disconnected':
        return {
          icon: WifiOff,
          color: 'text-zinc-500',
          bgColor: 'bg-zinc-500/10',
          label: 'Disconnected',
          pulse: false,
        }
      case 'error':
        return {
          icon: AlertCircle,
          color: 'text-red-500',
          bgColor: 'bg-red-500/10',
          label: 'Connection Error',
          pulse: false,
        }
    }
  }

  const config = getStatusConfig(status)
  const Icon = config.icon

  return (
    <div
      className={cn('flex items-center gap-2', className)}
      title={showMetrics && latency ? `Latency: ${latency}ms` : config.label}
    >
      <div className={cn('flex items-center justify-center w-8 h-8 rounded-full', config.bgColor)}>
        <Icon
          className={cn('w-4 h-4', config.color, config.pulse && 'animate-spin')}
          aria-label={config.label}
        />
      </div>

      {showLabel && (
        <div className="flex flex-col">
          <span className={cn('text-sm font-medium', config.color)}>{config.label}</span>
          {showMetrics && latency !== undefined && status === 'connected' && (
            <span className="text-xs text-zinc-500">{latency}ms</span>
          )}
        </div>
      )}
    </div>
  )
}

// Compact version for header/status bar
export function ConnectionStatusIndicator({ status, className }: { status: Status; className?: string }) {
  const getIndicatorColor = (status: Status) => {
    switch (status) {
      case 'connected':
        return 'bg-green-500'
      case 'connecting':
      case 'reconnecting':
        return 'bg-yellow-500 animate-pulse'
      case 'disconnected':
        return 'bg-zinc-500'
      case 'error':
        return 'bg-red-500'
    }
  }

  return (
    <div className={cn('w-2 h-2 rounded-full', getIndicatorColor(status), className)} title={status} />
  )
}
