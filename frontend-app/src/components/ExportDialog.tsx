import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog'
import { Button } from './ui/button'
import type { ExportSettings, VideoResolution, VideoFormat } from '../types/composition'
import { DEFAULT_OUTPUT_SETTINGS } from '../types/composition'

interface ExportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  payload: {
    clips: Array<{
      video_url: string
      start_time: number
      end_time: number
      trim_start: number
      trim_end: number
    }>
    overlays: unknown[]
  } | null
  onConfirm: (settings: ExportSettings) => void
}

/**
 * Export dialog that shows the JSON payload before sending
 */
export function ExportDialog({ open, onOpenChange, payload, onConfirm }: ExportDialogProps) {
  const [isExporting, setIsExporting] = useState(false)

  // Form state
  const [description, setDescription] = useState('')
  const [resolution, setResolution] = useState<VideoResolution>(DEFAULT_OUTPUT_SETTINGS.resolution)
  const [format, setFormat] = useState<VideoFormat>(DEFAULT_OUTPUT_SETTINGS.format)
  const [fps, setFps] = useState(DEFAULT_OUTPUT_SETTINGS.fps)
  const [bitrate, setBitrate] = useState('')

  const handleConfirm = async () => {
    setIsExporting(true)
    try {
      const settings: ExportSettings = {
        description: description.trim() || null,
        output: {
          resolution,
          format,
          fps,
          bitrate: bitrate.trim() || null,
        },
      }
      await onConfirm(settings)
      onOpenChange(false)
    } catch (error) {
      // Error is already handled in the onConfirm handler
      console.error('Export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  // Validate bitrate format
  const isBitrateValid = !bitrate.trim() || /^\d+[kKmM]$/.test(bitrate.trim())

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[700px] max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Confirm Export</DialogTitle>
          <DialogDescription>
            Review the composition data that will be sent to the backend API
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto py-4">
          {payload ? (
            <div className="space-y-4">
              {/* Export Settings Form */}
              <div className="bg-zinc-800/50 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-zinc-100 mb-3">
                  Export Settings
                </h3>
                <div className="space-y-3">
                  {/* Description */}
                  <div>
                    <label className="text-xs text-zinc-400 block mb-1">
                      Description (optional)
                    </label>
                    <textarea
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Add a description for this composition..."
                      className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                      rows={2}
                    />
                  </div>

                  {/* Resolution & Format Row */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs text-zinc-400 block mb-1">
                        Resolution
                      </label>
                      <select
                        value={resolution}
                        onChange={(e) => setResolution(e.target.value as VideoResolution)}
                        className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="480p">480p (SD)</option>
                        <option value="720p">720p (HD)</option>
                        <option value="1080p">1080p (Full HD)</option>
                        <option value="4k">4K (Ultra HD)</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-xs text-zinc-400 block mb-1">
                        Format
                      </label>
                      <select
                        value={format}
                        onChange={(e) => setFormat(e.target.value as VideoFormat)}
                        className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="mp4">MP4</option>
                        <option value="mov">MOV</option>
                        <option value="avi">AVI</option>
                      </select>
                    </div>
                  </div>

                  {/* FPS & Bitrate Row */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs text-zinc-400 block mb-1">
                        FPS (24-60)
                      </label>
                      <input
                        type="number"
                        min={24}
                        max={60}
                        value={fps}
                        onChange={(e) => setFps(Math.max(24, Math.min(60, parseInt(e.target.value) || 30)))}
                        className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>

                    <div>
                      <label className="text-xs text-zinc-400 block mb-1">
                        Bitrate (optional, e.g. 2000k, 5M)
                      </label>
                      <input
                        type="text"
                        value={bitrate}
                        onChange={(e) => setBitrate(e.target.value)}
                        placeholder="Auto"
                        className={`w-full bg-zinc-900 border rounded px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 ${
                          isBitrateValid
                            ? 'border-zinc-700 focus:ring-blue-500'
                            : 'border-red-500 focus:ring-red-500'
                        }`}
                      />
                      {!isBitrateValid && (
                        <p className="text-xs text-red-400 mt-1">
                          Format: number followed by k/K/m/M (e.g., 2000k, 5M)
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Clips Summary */}
              <div className="bg-zinc-800/50 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-zinc-100 mb-2">
                  Summary
                </h3>
                <div className="text-sm text-zinc-400">
                  <p>Total clips: {payload.clips.length}</p>
                  <p>Overlays: {payload.overlays.length}</p>
                </div>
              </div>

              {/* JSON Payload */}
              <div className="bg-zinc-950 rounded-lg p-4 border border-zinc-800">
                <h3 className="text-sm font-semibold text-zinc-100 mb-2">
                  API Payload
                </h3>
                <pre className="text-xs text-zinc-300 overflow-x-auto whitespace-pre-wrap break-words font-mono">
                  {JSON.stringify(payload, null, 2)}
                </pre>
              </div>

              {/* Clips Details */}
              {payload.clips.length > 0 && (
                <div className="bg-zinc-800/50 rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-zinc-100 mb-2">
                    Clips Details
                  </h3>
                  <div className="space-y-3">
                    {payload.clips.map((clip, index) => (
                      <div
                        key={index}
                        className="bg-zinc-900 rounded p-3 text-xs space-y-1"
                      >
                        <div className="font-semibold text-zinc-100">
                          Clip {index + 1}
                        </div>
                        <div className="text-zinc-400 space-y-0.5">
                          <div className="truncate">
                            <span className="text-zinc-500">URL:</span>{' '}
                            {clip.video_url}
                          </div>
                          <div>
                            <span className="text-zinc-500">Timeline:</span>{' '}
                            {clip.start_time.toFixed(2)}s - {clip.end_time.toFixed(2)}s
                            ({(clip.end_time - clip.start_time).toFixed(2)}s duration)
                          </div>
                          <div>
                            <span className="text-zinc-500">Trim:</span> start{' '}
                            {clip.trim_start.toFixed(2)}s, end {clip.trim_end.toFixed(2)}s
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center text-zinc-500 py-8">
              No export data available
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="ghost"
            onClick={() => onOpenChange(false)}
            disabled={isExporting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={!payload || isExporting || !isBitrateValid}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            {isExporting ? 'Exporting...' : 'Confirm & Export'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
