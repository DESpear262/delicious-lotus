import { ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'
import { Button } from '../ui/button'
import { useEffect } from 'react'

interface ZoomControlsProps {
  zoom: number
  onZoomChange: (zoom: number) => void
  minZoom?: number
  maxZoom?: number
}

export function ZoomControls({
  zoom,
  onZoomChange,
  minZoom = 0.25,
  maxZoom = 8,
}: ZoomControlsProps) {
  const handleZoomIn = () => {
    const newZoom = Math.min(zoom * 1.5, maxZoom)
    onZoomChange(newZoom)
  }

  const handleZoomOut = () => {
    const newZoom = Math.max(zoom / 1.5, minZoom)
    onZoomChange(newZoom)
  }

  const handleFitToWindow = () => {
    onZoomChange(1) // Reset to 1x zoom
  }

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + Plus/Equals for zoom in
      if ((e.ctrlKey || e.metaKey) && (e.key === '=' || e.key === '+')) {
        e.preventDefault()
        handleZoomIn()
      }
      // Ctrl/Cmd + Minus for zoom out
      else if ((e.ctrlKey || e.metaKey) && e.key === '-') {
        e.preventDefault()
        handleZoomOut()
      }
      // Ctrl/Cmd + 0 for fit to window
      else if ((e.ctrlKey || e.metaKey) && e.key === '0') {
        e.preventDefault()
        handleFitToWindow()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [zoom]) // Re-register when zoom changes

  const zoomPercentage = Math.round(zoom * 100)

  return (
    <div className="flex items-center gap-2 bg-zinc-900 border border-zinc-700 rounded-md p-1">
      <Button
        variant="ghost"
        size="sm"
        onClick={handleZoomOut}
        disabled={zoom <= minZoom}
        className="h-7 w-7 p-0"
        title="Zoom out (Ctrl/Cmd + -)"
      >
        <ZoomOut className="w-4 h-4" />
      </Button>

      <div className="flex items-center gap-1 px-2 min-w-[60px] justify-center">
        <input
          type="range"
          min={Math.log2(minZoom)}
          max={Math.log2(maxZoom)}
          step={0.1}
          value={Math.log2(zoom)}
          onChange={(e) => {
            const newZoom = Math.pow(2, parseFloat(e.target.value))
            onZoomChange(newZoom)
          }}
          className="w-20 h-1 bg-zinc-700 rounded-lg appearance-none cursor-pointer
                     [&::-webkit-slider-thumb]:appearance-none
                     [&::-webkit-slider-thumb]:w-3
                     [&::-webkit-slider-thumb]:h-3
                     [&::-webkit-slider-thumb]:rounded-full
                     [&::-webkit-slider-thumb]:bg-blue-500
                     [&::-webkit-slider-thumb]:cursor-pointer
                     [&::-moz-range-thumb]:w-3
                     [&::-moz-range-thumb]:h-3
                     [&::-moz-range-thumb]:rounded-full
                     [&::-moz-range-thumb]:bg-blue-500
                     [&::-moz-range-thumb]:border-0
                     [&::-moz-range-thumb]:cursor-pointer"
        />
        <span className="text-xs text-zinc-400 font-mono w-12 text-right">
          {zoomPercentage}%
        </span>
      </div>

      <Button
        variant="ghost"
        size="sm"
        onClick={handleZoomIn}
        disabled={zoom >= maxZoom}
        className="h-7 w-7 p-0"
        title="Zoom in (Ctrl/Cmd + +)"
      >
        <ZoomIn className="w-4 h-4" />
      </Button>

      <div className="w-px h-5 bg-zinc-700" />

      <Button
        variant="ghost"
        size="sm"
        onClick={handleFitToWindow}
        className="h-7 w-7 p-0"
        title="Fit to window (Ctrl/Cmd + 0)"
      >
        <Maximize2 className="w-4 h-4" />
      </Button>
    </div>
  )
}
