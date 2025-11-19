import { useCallback, useState, useRef } from 'react'
import { Upload } from 'lucide-react'
import { Button } from '../ui/button'

export interface MediaUploadProps {
  onFilesSelected?: (files: File[]) => void
  accept?: string
  maxFiles?: number
  disabled?: boolean
}

export function MediaUpload({
  onFilesSelected,
  accept = 'image/*,video/*,audio/*',
  maxFiles,
  disabled = false,
}: MediaUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (!disabled) {
      setIsDragOver(true)
    }
  }, [disabled])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()

    // Only set isDragOver to false if we're leaving the drop zone entirely
    const rect = e.currentTarget.getBoundingClientRect()
    const x = e.clientX
    const y = e.clientY

    if (
      x <= rect.left ||
      x >= rect.right ||
      y <= rect.top ||
      y >= rect.bottom
    ) {
      setIsDragOver(false)
    }
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)

    if (disabled) return

    const files = Array.from(e.dataTransfer.files)
    const limitedFiles = maxFiles ? files.slice(0, maxFiles) : files

    if (limitedFiles.length > 0) {
      onFilesSelected?.(limitedFiles)
    }
  }, [disabled, maxFiles, onFilesSelected])

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files ? Array.from(e.target.files) : []
    const limitedFiles = maxFiles ? files.slice(0, maxFiles) : files

    if (limitedFiles.length > 0) {
      onFilesSelected?.(limitedFiles)
    }

    // Reset input value to allow selecting the same file again
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [maxFiles, onFilesSelected])

  const handleClick = useCallback(() => {
    if (!disabled) {
      fileInputRef.current?.click()
    }
  }, [disabled])

  return (
    <div
      className={`
        relative border-2 border-dashed rounded-lg
        transition-all duration-200
        ${isDragOver
          ? 'border-blue-500 bg-blue-500/10'
          : 'border-zinc-700 bg-zinc-900/50'
        }
        ${disabled
          ? 'opacity-50 cursor-not-allowed'
          : 'cursor-pointer hover:border-zinc-600 hover:bg-zinc-900/70'
        }
      `}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept={accept}
        multiple={!maxFiles || maxFiles > 1}
        onChange={handleFileInputChange}
        disabled={disabled}
      />

      <div className="flex flex-col items-center justify-center p-12 text-center">
        <div className={`
          mb-4 p-4 rounded-full
          ${isDragOver ? 'bg-blue-500/20' : 'bg-zinc-800'}
          transition-colors duration-200
        `}>
          <Upload className={`
            w-8 h-8
            ${isDragOver ? 'text-blue-400' : 'text-zinc-400'}
            transition-colors duration-200
          `} />
        </div>

        <h3 className="text-lg font-medium text-zinc-200 mb-2">
          {isDragOver ? 'Drop files here' : 'Upload media files'}
        </h3>

        <p className="text-sm text-zinc-400 mb-4">
          Drag and drop files here, or click to browse
        </p>

        <div className="text-xs text-zinc-500">
          <p>Supported formats:</p>
          <p className="mt-1">
            Images (JPG, PNG, WebP, GIF) • Videos (MP4, WebM, MOV, AVI) • Audio (MP3, WAV, OGG, M4A)
          </p>
          <p className="mt-2">
            Max file size: 100MB for images, 1GB for videos, 500MB for audio
          </p>
        </div>

        {!disabled && (
          <Button
            variant="outline"
            className="mt-6"
            onClick={(e) => {
              e.stopPropagation()
              handleClick()
            }}
          >
            Browse Files
          </Button>
        )}
      </div>

      {isDragOver && (
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute inset-2 border-2 border-blue-400 rounded-lg animate-pulse" />
        </div>
      )}
    </div>
  )
}
