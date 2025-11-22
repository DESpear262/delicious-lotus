import { useState } from 'react'
import { ChevronDown, ChevronRight, Video, Image as ImageIcon, Type } from 'lucide-react'
import type { Clip, MediaAsset } from '../../types/stores'
import { useMediaStore } from '../../contexts/StoreContext'

interface ClipsListPanelProps {
  clips: Map<string, Clip>
  fps: number
  onClipSelect?: (clipId: string) => void
  selectedClipIds?: string[]
}

export function ClipsListPanel({ clips, fps, onClipSelect, selectedClipIds = [] }: ClipsListPanelProps) {
  const [expandedClips, setExpandedClips] = useState<Set<string>>(new Set())
  const mediaAssets = useMediaStore((state) => state.assets)

  const toggleClipExpanded = (clipId: string) => {
    const newExpanded = new Set(expandedClips)
    if (newExpanded.has(clipId)) {
      newExpanded.delete(clipId)
    } else {
      newExpanded.add(clipId)
    }
    setExpandedClips(newExpanded)
  }

  const getAssetForClip = (clip: Clip): MediaAsset | undefined => {
    return mediaAssets.get(clip.assetId)
  }

  const getAssetTypeIcon = (asset: MediaAsset | undefined) => {
    if (!asset) return <Video className="w-4 h-4 text-zinc-500" />

    switch (asset.type) {
      case 'video':
        return <Video className="w-4 h-4 text-purple-400" />
      case 'image':
        return <ImageIcon className="w-4 h-4 text-blue-400" />
      case 'audio':
        return <Type className="w-4 h-4 text-green-400" />
      default:
        return <Video className="w-4 h-4 text-zinc-500" />
    }
  }

  const formatTime = (frames: number): string => {
    const totalSeconds = frames / fps
    const minutes = Math.floor(totalSeconds / 60)
    const seconds = Math.floor(totalSeconds % 60)
    const remainingFrames = frames % fps

    if (minutes > 0) {
      return `${minutes}m ${seconds}s ${remainingFrames}f`
    }
    return `${seconds}s ${remainingFrames}f`
  }

  const clipsArray = Array.from(clips.values()).sort((a, b) => a.startTime - b.startTime)

  if (clipsArray.length === 0) {
    return (
      <div className="p-4 bg-zinc-900 h-full">
        <h3 className="text-sm font-semibold text-zinc-200 mb-3">Media Details</h3>
        <div className="flex flex-col items-center justify-center py-8 text-center text-zinc-500">
          <Video className="w-12 h-12 mb-2" />
          <p className="text-sm">No clips added yet</p>
          <p className="text-xs mt-1">Drag media from the library to the timeline</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-4 bg-zinc-900 h-full flex flex-col">
      <h3 className="text-sm font-semibold text-zinc-200 mb-3">Media Details</h3>
      <div className="flex-1 overflow-y-auto space-y-2">
        {clipsArray.map((clip) => {
          const asset = getAssetForClip(clip)
          const isExpanded = expandedClips.has(clip.id)
          const isSelected = selectedClipIds.includes(clip.id)

          return (
            <div
              key={clip.id}
              className={`border rounded-lg overflow-hidden transition-colors ${
                isSelected ? 'border-blue-500 bg-blue-950/20' : 'border-zinc-700 bg-zinc-800'
              }`}
            >
              {/* Clip header - always visible */}
              <div
                className="flex items-center justify-between p-3 cursor-pointer hover:bg-zinc-750 transition-colors"
                onClick={() => toggleClipExpanded(clip.id)}
              >
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  {getAssetTypeIcon(asset)}
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium text-zinc-200 truncate">
                      {asset?.name || `Clip ${clip.id.slice(0, 8)}`}
                    </div>
                    <div className="text-[10px] text-zinc-500">
                      {formatTime(clip.duration)}
                    </div>
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    toggleClipExpanded(clip.id)
                  }}
                  className="p-1 hover:bg-zinc-700 rounded transition-colors"
                >
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-zinc-400" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-zinc-400" />
                  )}
                </button>
              </div>

              {/* Clip details - expandable */}
              {isExpanded && (
                <div className="px-3 pb-3 pt-1 space-y-2 border-t border-zinc-700">
                  {/* Asset info */}
                  {asset && (
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="text-zinc-500">Type:</span>
                        <span className="text-zinc-300 capitalize">{asset.type}</span>
                      </div>
                      {asset.width && asset.height && (
                        <div className="flex items-center justify-between text-[10px]">
                          <span className="text-zinc-500">Dimensions:</span>
                          <span className="text-zinc-300">{asset.width}x{asset.height}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Timeline info */}
                  <div className="space-y-1 pt-1 border-t border-zinc-700">
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-zinc-500">Start Time:</span>
                      <span className="text-zinc-300">{formatTime(clip.startTime)}</span>
                    </div>
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-zinc-500">Duration:</span>
                      <span className="text-zinc-300">{formatTime(clip.duration)}</span>
                    </div>
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-zinc-500">End Time:</span>
                      <span className="text-zinc-300">{formatTime(clip.startTime + clip.duration)}</span>
                    </div>
                  </div>

                  {/* Transform info */}
                  <div className="space-y-1 pt-1 border-t border-zinc-700">
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-zinc-500">Opacity:</span>
                      <span className="text-zinc-300">{Math.round(clip.opacity * 100)}%</span>
                    </div>
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-zinc-500">Scale:</span>
                      <span className="text-zinc-300">{clip.scale.x.toFixed(2)}x, {clip.scale.y.toFixed(2)}x</span>
                    </div>
                    {clip.rotation !== 0 && (
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="text-zinc-500">Rotation:</span>
                        <span className="text-zinc-300">{clip.rotation}°</span>
                      </div>
                    )}
                  </div>

                  {/* Select button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onClipSelect?.(clip.id)
                    }}
                    className="w-full mt-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors"
                  >
                    Select Clip
                  </button>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
