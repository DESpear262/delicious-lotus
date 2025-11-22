/**
 * Media Library Upload
 * Complete upload interface with drag-and-drop, queue management, and progress tracking
 */

import { MediaUpload } from './MediaUpload'
import { UploadQueue } from './UploadProgress'
import { useUpload } from '../../hooks/useUpload'
import { useState, useRef, useEffect } from 'react'
import { Input } from '../ui/input'
import { Button } from '../ui/button'
import { Link, Loader2 } from 'lucide-react'

export function MediaLibraryUpload() {
  const {
    uploadFiles,
    cancelUpload,
    retryUpload,
    removeUpload,
    clearCompleted,
    uploads,
    uploadSpeeds,
    importMediaFromUrl,
  } = useUpload()

  const [urlInput, setUrlInput] = useState('')
  const [isImporting, setIsImporting] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const handleFilesSelected = async (files: File[]) => {
    await uploadFiles(files)
  }

  const handleUrlImport = async () => {
    if (!urlInput.trim()) return

    try {
      setIsImporting(true)
      // Basic type detection from extension, default to image
      const type = urlInput.match(/\.(mp4|webm|mov|avi)$/i) ? 'video' :
        urlInput.match(/\.(mp3|wav|ogg|m4a)$/i) ? 'audio' : 'image'

      const name = urlInput.split('/').pop() || `imported-${Date.now()}`

      await importMediaFromUrl(urlInput, name, type)
      setUrlInput('')
    } catch (error) {
      console.error('Import failed:', error)
    } finally {
      setIsImporting(false)
    }
  }

  // Handle paste events
  useEffect(() => {
    const handlePaste = async (e: ClipboardEvent) => {
      const items = e.clipboardData?.items
      if (!items) return

      const files: File[] = []
      let urlFound = ''

      for (let i = 0; i < items.length; i++) {
        const item = items[i]

        if (item.kind === 'file') {
          const file = item.getAsFile()
          // Only accept image, video, or audio files
          if (file && (file.type.startsWith('image/') || file.type.startsWith('video/') || file.type.startsWith('audio/'))) {
            files.push(file)
          }
        } else if (item.kind === 'string' && item.type === 'text/plain') {
          item.getAsString((s) => {
            if (s.match(/^https?:\/\//)) {
              urlFound = s
            }
          })
        }
      }

      // If files are present, always handle them (even if focused on input)
      if (files.length > 0) {
        e.preventDefault()
        await uploadFiles(files)
        return
      }

      // If we're focused on an input, let default text paste happen
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return
      }

      // Otherwise, if we found a URL, populate the input
      if (urlFound) {
        setUrlInput(urlFound)
      }
    }

    window.addEventListener('paste', handlePaste)
    return () => window.removeEventListener('paste', handlePaste)
  }, [uploadFiles])

  return (
    <div className="space-y-4" ref={containerRef}>
      {/* Upload drop zone */}
      <MediaUpload onFilesSelected={handleFilesSelected} />

      {/* URL Import */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Link className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <Input
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            placeholder="Paste image or video URL..."
            className="pl-9 bg-zinc-900 border-zinc-800"
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleUrlImport()
            }}
          />
        </div>
        <Button
          onClick={handleUrlImport}
          disabled={!urlInput.trim() || isImporting}
          variant="secondary"
        >
          {isImporting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            'Import'
          )}
        </Button>
      </div>

      {/* Upload queue with progress tracking */}
      {uploads.length > 0 && (
        <UploadQueue
          uploads={uploads}
          onCancel={cancelUpload}
          onRetry={retryUpload}
          onRemove={removeUpload}
          onClearCompleted={clearCompleted}
          uploadSpeeds={uploadSpeeds}
        />
      )}
    </div>
  )
}
