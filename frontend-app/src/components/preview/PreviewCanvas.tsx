import { useEffect, useRef, useContext } from 'react'
import { PreviewRenderer } from '../../services/PreviewRenderer'
import {
  TimelineStoreContext,
  EditorStoreContext,
  MediaStoreContext,
} from '../../contexts/StoreContext'

interface PreviewCanvasProps {
  className?: string
}

/**
 * PreviewCanvas - Renders timeline content using PreviewRenderer
 * Shows videos, images, and other media assets from the timeline
 */
export function PreviewCanvas({ className = '' }: PreviewCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const rendererRef = useRef<PreviewRenderer | null>(null)

  // Get store instances from context
  const timelineStore = useContext(TimelineStoreContext)
  const editorStore = useContext(EditorStoreContext)
  const mediaStore = useContext(MediaStoreContext)

  useEffect(() => {
    if (!containerRef.current || !timelineStore || !editorStore || !mediaStore) {
      return
    }

    // Create PreviewRenderer instance
    try {
      rendererRef.current = new PreviewRenderer({
        containerElement: containerRef.current,
        timelineStore,
        editorStore,
        mediaStore: mediaStore.getState(),
        quality: editorStore.getState().previewSettings.quality,
      })

      console.log('PreviewRenderer initialized successfully')
    } catch (error) {
      console.error('Failed to initialize PreviewRenderer:', error)
    }

    // Cleanup on unmount
    return () => {
      if (rendererRef.current) {
        rendererRef.current.dispose()
        rendererRef.current = null
      }
    }
  }, [timelineStore, editorStore, mediaStore])

  // Handle container resize
  useEffect(() => {
    if (!containerRef.current || !rendererRef.current) return

    const resizeObserver = new ResizeObserver((entries) => {
      const entry = entries[0]
      if (entry && rendererRef.current) {
        const { width, height } = entry.contentRect
        rendererRef.current.updateSize(width, height)
      }
    })

    resizeObserver.observe(containerRef.current)

    return () => {
      resizeObserver.disconnect()
    }
  }, [])

  return (
    <div
      ref={containerRef}
      className={`relative w-full h-full bg-black ${className}`}
      style={{
        aspectRatio: '16/9',
        maxHeight: '100%',
      }}
    >
      {/* PreviewRenderer will inject video elements here */}
      {/* Fallback content shown if no clips */}
      <div className="absolute inset-0 flex items-center justify-center text-zinc-600 pointer-events-none">
        <div className="text-center opacity-50">
          <p className="text-sm">Preview</p>
          <p className="text-xs mt-1">Add clips to timeline</p>
        </div>
      </div>
    </div>
  )
}
