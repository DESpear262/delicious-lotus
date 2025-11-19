import { Dialog, DialogContent } from '../ui/dialog'
import { ExternalLink, X } from 'lucide-react'
import type { MediaAsset } from '../../types/stores'
import { useEffect, useRef } from 'react'

interface MediaPreviewModalProps {
  asset: MediaAsset | null
  isOpen: boolean
  onClose: () => void
}

/**
 * MediaPreviewModal - Full-size preview modal for media assets
 * Shows images or playable videos with source URL link
 */
export function MediaPreviewModal({ asset, isOpen, onClose }: MediaPreviewModalProps) {
  const videoRef = useRef<HTMLVideoElement>(null)

  // Reset video when modal closes
  useEffect(() => {
    if (!isOpen && videoRef.current) {
      videoRef.current.pause()
      videoRef.current.currentTime = 0
    }
  }, [isOpen])

  if (!asset) return null

  const isVideo = asset.type === 'video'
  const isImage = asset.type === 'image'

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-[95vw] max-h-[95vh] w-auto h-auto p-0 bg-zinc-950 border-zinc-800 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-zinc-800 bg-zinc-900">
          <div className="flex-1 min-w-0 mr-4">
            <h2 className="text-lg font-semibold text-zinc-100 truncate">{asset.name}</h2>
            <p className="text-sm text-zinc-400">
              {asset.type.charAt(0).toUpperCase() + asset.type.slice(1)}
              {asset.width && asset.height && ` • ${asset.width} × ${asset.height}`}
              {asset.duration && ` • ${Math.floor(asset.duration / 60)}:${String(Math.floor(asset.duration % 60)).padStart(2, '0')}`}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <a
              href={asset.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors text-sm"
              onClick={(e) => e.stopPropagation()}
            >
              <ExternalLink className="w-4 h-4" />
              Open Source
            </a>
            <button
              onClick={onClose}
              className="p-2 hover:bg-zinc-800 rounded-lg transition-colors text-zinc-400 hover:text-zinc-100"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Media Content */}
        <div className="flex items-center justify-center p-4 bg-black" style={{ maxHeight: 'calc(95vh - 80px)' }}>
          {isImage && (
            <img
              src={asset.url}
              alt={asset.name}
              className="max-w-full max-h-full object-contain"
              style={{ maxWidth: '95vw', maxHeight: 'calc(95vh - 80px)' }}
            />
          )}

          {isVideo && (
            <video
              ref={videoRef}
              src={asset.url}
              controls
              autoPlay
              className="max-w-full max-h-full"
              style={{ maxWidth: '95vw', maxHeight: 'calc(95vh - 80px)' }}
            >
              Your browser does not support the video tag.
            </video>
          )}

          {!isImage && !isVideo && (
            <div className="text-center text-zinc-400 p-8">
              <p className="mb-2">Preview not available for this media type</p>
              <a
                href={asset.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 underline"
              >
                Open in new tab
              </a>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
