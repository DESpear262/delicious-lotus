import { useWebSocketStore } from '@/contexts/StoreContext'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import {
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  Download,
  X as XIcon,
} from 'lucide-react'
import type { JobState } from '@/types/stores'
import type { ExportJobResult } from '@/types/websocket'
import { cancelExportJob } from '@/services/exportService'

interface ExportProgressProps {
  onDownload?: (downloadUrl: string, fileName: string) => void
  onClose?: (jobId: string) => void
}

export function ExportProgress({ onDownload, onClose }: ExportProgressProps) {
  // Get export jobs from WebSocket store
  const jobs = useWebSocketStore((state) => state.jobs)
  const activeJobIds = useWebSocketStore((state) => state.activeJobIds)

  // Filter for export jobs only
  const exportJobs = Array.from(jobs.values()).filter(
    (job) => job.type === 'export'
  )

  // Show active and recently completed jobs
  const visibleJobs = exportJobs.filter(
    (job) =>
      activeJobIds.includes(job.id) ||
      job.status === 'succeeded' ||
      job.status === 'failed'
  )

  if (visibleJobs.length === 0) {
    return null
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-md space-y-2">
      {visibleJobs.map((job) => (
        <ExportJobCard
          key={job.id}
          job={job}
          onDownload={onDownload}
          onClose={onClose}
        />
      ))}
    </div>
  )
}

interface ExportJobCardProps {
  job: JobState
  onDownload?: (downloadUrl: string, fileName: string) => void
  onClose?: (jobId: string) => void
}

function ExportJobCard({ job, onDownload, onClose }: ExportJobCardProps) {
  const result = job.result as ExportJobResult | undefined

  const handleCancel = async () => {
    try {
      await cancelExportJob(job.id)
    } catch (error) {
      console.error('Failed to cancel export:', error)
    }
  }

  const handleDownload = () => {
    if (result?.downloadUrl && result?.fileName) {
      onDownload?.(result.downloadUrl, result.fileName)
    }
  }

  const handleClose = () => {
    onClose?.(job.id)
  }

  return (
    <Card className="relative overflow-hidden bg-zinc-900 border-zinc-800 p-4 shadow-lg">
      {/* Close button */}
      {(job.status === 'succeeded' || job.status === 'failed') && (
        <button
          onClick={handleClose}
          className="absolute top-2 right-2 text-zinc-400 hover:text-zinc-200 transition-colors"
          aria-label="Close"
        >
          <XIcon className="h-4 w-4" />
        </button>
      )}

      <div className="flex items-start gap-3">
        {/* Status Icon */}
        <div className="mt-1">
          {job.status === 'queued' && (
            <Clock className="h-5 w-5 text-zinc-400 animate-pulse" />
          )}
          {job.status === 'running' && (
            <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
          )}
          {job.status === 'succeeded' && (
            <CheckCircle2 className="h-5 w-5 text-green-500" />
          )}
          {job.status === 'failed' && <XCircle className="h-5 w-5 text-red-500" />}
          {job.status === 'canceled' && (
            <XCircle className="h-5 w-5 text-zinc-400" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Status Text */}
          <div className="flex items-center justify-between gap-2 mb-1">
            <h4 className="text-sm font-medium text-zinc-100 truncate">
              {getStatusLabel(job.status)}
            </h4>
            {job.progress !== undefined && job.status === 'running' && (
              <span className="text-xs text-zinc-400 font-mono">
                {Math.round(job.progress)}%
              </span>
            )}
          </div>

          {/* Message */}
          {job.message && (
            <p className="text-xs text-zinc-400 mb-2 line-clamp-2">
              {job.message}
            </p>
          )}

          {/* Progress Bar */}
          {job.status === 'running' && job.progress !== undefined && (
            <Progress value={job.progress} className="h-2 mb-3" />
          )}

          {/* Error Message */}
          {job.status === 'failed' && job.error && (
            <div className="mt-2 p-2 rounded bg-red-500/10 border border-red-500/20">
              <p className="text-xs text-red-400">{job.error}</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center gap-2 mt-3">
            {job.status === 'succeeded' && result?.downloadUrl && (
              <Button
                size="sm"
                onClick={handleDownload}
                className="flex items-center gap-1.5"
              >
                <Download className="h-3.5 w-3.5" />
                Download
              </Button>
            )}

            {(job.status === 'queued' || job.status === 'running') && (
              <Button
                size="sm"
                variant="outline"
                onClick={handleCancel}
                className="flex items-center gap-1.5"
              >
                <XIcon className="h-3.5 w-3.5" />
                Cancel
              </Button>
            )}

            {job.status === 'succeeded' && result && (
              <div className="ml-auto text-xs text-zinc-500">
                {formatFileSize(result.fileSize)}
              </div>
            )}
          </div>

          {/* Timestamp */}
          <div className="mt-2 text-xs text-zinc-500">
            {formatTimestamp(job.updatedAt)}
          </div>
        </div>
      </div>
    </Card>
  )
}

function getStatusLabel(status: JobState['status']): string {
  const labels: Record<JobState['status'], string> = {
    queued: 'Queued for Export',
    running: 'Exporting Video...',
    succeeded: 'Export Complete',
    failed: 'Export Failed',
    canceled: 'Export Canceled',
  }
  return labels[status] || 'Processing'
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

function formatTimestamp(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)

  if (diffSec < 60) return 'Just now'
  if (diffMin < 60) return `${diffMin} minute${diffMin > 1 ? 's' : ''} ago`
  if (diffHour < 24) return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
