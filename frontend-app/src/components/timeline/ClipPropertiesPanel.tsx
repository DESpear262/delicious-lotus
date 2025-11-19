import { useState } from 'react'
import type { Clip, Transition } from '../../types/stores'
import { useMediaStore } from '../../contexts/StoreContext'
import { Label } from '../ui/label'
import { Input } from '../ui/input'
import { Slider } from '../ui/slider'
import { Button } from '../ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'
import { Lock, Unlock } from 'lucide-react'

interface ClipPropertiesPanelProps {
  clip: Clip
  fps: number
  onUpdate: (clipId: string, updates: Partial<Clip>) => void
}

export function ClipPropertiesPanel({ clip, fps, onUpdate }: ClipPropertiesPanelProps) {
  const [aspectRatioLocked, setAspectRatioLocked] = useState(true)
  const mediaAssets = useMediaStore((state) => state.assets)
  const asset = mediaAssets.get(clip.assetId)
  const isVideo = asset?.type === 'video'
  const isImage = asset?.type === 'image'

  const handleOpacityChange = (value: number[]) => {
    onUpdate(clip.id, { opacity: value[0] / 100 })
  }

  const handleScaleChange = (axis: 'x' | 'y', value: number) => {
    if (aspectRatioLocked) {
      // If locked, change both axes
      onUpdate(clip.id, {
        scale: { x: value, y: value },
      })
    } else {
      // If unlocked, change only the specified axis
      onUpdate(clip.id, {
        scale: { ...clip.scale, [axis]: value },
      })
    }
  }

  const handlePositionChange = (axis: 'x' | 'y', value: number) => {
    onUpdate(clip.id, {
      position: { ...clip.position, [axis]: value },
    })
  }

  const handleRotationChange = (value: number) => {
    onUpdate(clip.id, { rotation: value })
  }

  const handleTransitionChange = (direction: 'in' | 'out', type: Transition['type'] | 'none') => {
    if (type === 'none') {
      onUpdate(clip.id, { [`transition${direction === 'in' ? 'In' : 'Out'}`]: undefined })
    } else {
      const transition: Transition = {
        type,
        duration: fps, // Default to 1 second
      }
      onUpdate(clip.id, { [`transition${direction === 'in' ? 'In' : 'Out'}`]: transition })
    }
  }

  const handleTransitionDurationChange = (direction: 'in' | 'out', frames: number) => {
    const currentTransition = direction === 'in' ? clip.transitionIn : clip.transitionOut
    if (currentTransition) {
      const transition: Transition = {
        ...currentTransition,
        duration: frames,
      }
      onUpdate(clip.id, { [`transition${direction === 'in' ? 'In' : 'Out'}`]: transition })
    }
  }

  // Format duration as seconds
  const durationInSeconds = (clip.duration / fps).toFixed(2)
  const startTimeInSeconds = (clip.startTime / fps).toFixed(2)

  const handleStartTimeChange = (value: number) => {
    const newStartTime = Math.round(value * fps)
    onUpdate(clip.id, { startTime: Math.max(0, newStartTime) })
  }

  const handleDurationChange = (value: number) => {
    const newDuration = Math.round(value * fps)
    onUpdate(clip.id, { duration: Math.max(1, newDuration) })
  }

  const handleTrimStartChange = (value: number) => {
    const newInPoint = Math.round(value * fps)
    const maxInPoint = clip.outPoint - fps // Ensure at least 1 second of content
    onUpdate(clip.id, {
      inPoint: Math.max(0, Math.min(newInPoint, maxInPoint)),
      duration: clip.outPoint - Math.max(0, Math.min(newInPoint, maxInPoint))
    })
  }

  const handleTrimEndChange = (value: number) => {
    const newOutPoint = Math.round(value * fps)
    const minOutPoint = clip.inPoint + fps // Ensure at least 1 second of content
    const assetDuration = asset?.duration ? Math.round(asset.duration * fps) : clip.outPoint
    onUpdate(clip.id, {
      outPoint: Math.min(assetDuration, Math.max(newOutPoint, minOutPoint)),
      duration: Math.min(assetDuration, Math.max(newOutPoint, minOutPoint)) - clip.inPoint
    })
  }

  return (
    <div className="h-full flex flex-col bg-zinc-900 border-l border-zinc-700">
      <div className="p-4 space-y-6 overflow-y-auto flex-1">
        <div>
          <h3 className="text-sm font-semibold text-zinc-200 mb-3">Clip Properties</h3>

          {/* Basic Info */}
          <div className="space-y-3 mb-4">
            {/* Start Time - Editable */}
            <div className="space-y-1">
              <Label htmlFor="startTime" className="text-xs text-zinc-400">Start Time</Label>
              <div className="flex items-center gap-2">
                <Input
                  id="startTime"
                  type="number"
                  value={parseFloat(startTimeInSeconds)}
                  onChange={(e) => handleStartTimeChange(parseFloat(e.target.value))}
                  step={0.1}
                  min={0}
                  className="h-8 text-xs"
                />
                <span className="text-xs text-zinc-500 flex-shrink-0">s</span>
              </div>
            </div>

            {/* Duration - Editable (for images this is the time_length) */}
            <div className="space-y-1">
              <Label htmlFor="duration" className="text-xs text-zinc-400">
                {isImage ? 'Time Length' : 'Duration'}
              </Label>
              <div className="flex items-center gap-2">
                <Input
                  id="duration"
                  type="number"
                  value={parseFloat(durationInSeconds)}
                  onChange={(e) => handleDurationChange(parseFloat(e.target.value))}
                  step={0.1}
                  min={0.1}
                  className="h-8 text-xs"
                />
                <span className="text-xs text-zinc-500 flex-shrink-0">s</span>
              </div>
              {isImage && (
                <p className="text-[10px] text-zinc-500 mt-1">
                  How long the image displays on timeline
                </p>
              )}
            </div>

            {/* Trim controls for videos */}
            {isVideo && (
              <>
                <div className="space-y-1">
                  <Label htmlFor="trimStart" className="text-xs text-zinc-400">Trim Start</Label>
                  <div className="flex items-center gap-2">
                    <Input
                      id="trimStart"
                      type="number"
                      value={(clip.inPoint / fps).toFixed(2)}
                      onChange={(e) => handleTrimStartChange(parseFloat(e.target.value))}
                      step={0.1}
                      min={0}
                      max={asset?.duration ? asset.duration : (clip.outPoint / fps)}
                      className="h-8 text-xs"
                    />
                    <span className="text-xs text-zinc-500 flex-shrink-0">s</span>
                  </div>
                  <p className="text-[10px] text-zinc-500 mt-1">
                    Where to start playing from source video
                  </p>
                </div>

                <div className="space-y-1">
                  <Label htmlFor="trimEnd" className="text-xs text-zinc-400">Trim End</Label>
                  <div className="flex items-center gap-2">
                    <Input
                      id="trimEnd"
                      type="number"
                      value={(clip.outPoint / fps).toFixed(2)}
                      onChange={(e) => handleTrimEndChange(parseFloat(e.target.value))}
                      step={0.1}
                      min={(clip.inPoint / fps) + 0.1}
                      max={asset?.duration ? asset.duration : (clip.outPoint / fps)}
                      className="h-8 text-xs"
                    />
                    <span className="text-xs text-zinc-500 flex-shrink-0">s</span>
                  </div>
                  <p className="text-[10px] text-zinc-500 mt-1">
                    Where to stop playing from source video
                  </p>
                </div>
              </>
            )}
          </div>
        </div>

      {/* Opacity */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="opacity" className="text-xs text-zinc-300">Opacity</Label>
          <span className="text-xs text-zinc-400">{Math.round(clip.opacity * 100)}%</span>
        </div>
        <Slider
          id="opacity"
          value={[clip.opacity * 100]}
          onValueChange={handleOpacityChange}
          min={0}
          max={100}
          step={1}
          className="w-full"
        />
      </div>

      {/* Scale */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label className="text-xs text-zinc-300">Scale</Label>
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0"
            onClick={() => setAspectRatioLocked(!aspectRatioLocked)}
          >
            {aspectRatioLocked ? (
              <Lock className="w-3 h-3 text-blue-400" />
            ) : (
              <Unlock className="w-3 h-3 text-zinc-500" />
            )}
          </Button>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <Label htmlFor="scaleX" className="text-[10px] text-zinc-400">X</Label>
            <Input
              id="scaleX"
              type="number"
              value={clip.scale.x.toFixed(2)}
              onChange={(e) => handleScaleChange('x', parseFloat(e.target.value))}
              step={0.1}
              className="h-8 text-xs"
            />
          </div>
          <div>
            <Label htmlFor="scaleY" className="text-[10px] text-zinc-400">Y</Label>
            <Input
              id="scaleY"
              type="number"
              value={clip.scale.y.toFixed(2)}
              onChange={(e) => handleScaleChange('y', parseFloat(e.target.value))}
              step={0.1}
              className="h-8 text-xs"
              disabled={aspectRatioLocked}
            />
          </div>
        </div>
      </div>

      {/* Position */}
      <div className="space-y-2">
        <Label className="text-xs text-zinc-300">Position</Label>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <Label htmlFor="posX" className="text-[10px] text-zinc-400">X</Label>
            <Input
              id="posX"
              type="number"
              value={clip.position.x}
              onChange={(e) => handlePositionChange('x', parseFloat(e.target.value))}
              step={1}
              className="h-8 text-xs"
            />
          </div>
          <div>
            <Label htmlFor="posY" className="text-[10px] text-zinc-400">Y</Label>
            <Input
              id="posY"
              type="number"
              value={clip.position.y}
              onChange={(e) => handlePositionChange('y', parseFloat(e.target.value))}
              step={1}
              className="h-8 text-xs"
            />
          </div>
        </div>
      </div>

      {/* Rotation */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="rotation" className="text-xs text-zinc-300">Rotation</Label>
          <span className="text-xs text-zinc-400">{clip.rotation}°</span>
        </div>
        <Input
          id="rotation"
          type="number"
          value={clip.rotation}
          onChange={(e) => handleRotationChange(parseFloat(e.target.value))}
          step={1}
          min={-360}
          max={360}
          className="h-8 text-xs"
        />
      </div>

      {/* Transitions */}
      <div className="space-y-3 pt-3 border-t border-zinc-700">
        <h4 className="text-xs font-medium text-zinc-300">Transitions</h4>

        {/* Transition In */}
        <div className="space-y-2">
          <Label htmlFor="transitionIn" className="text-xs text-zinc-400">Transition In</Label>
          <Select
            value={clip.transitionIn?.type || 'none'}
            onValueChange={(value) => handleTransitionChange('in', value as Transition['type'] | 'none')}
          >
            <SelectTrigger id="transitionIn" className="h-8 text-xs">
              <SelectValue placeholder="None" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None</SelectItem>
              <SelectItem value="fade">Fade</SelectItem>
              <SelectItem value="crossDissolve">Cross Dissolve</SelectItem>
              <SelectItem value="wipeLeft">Wipe Left</SelectItem>
              <SelectItem value="wipeRight">Wipe Right</SelectItem>
              <SelectItem value="wipeUp">Wipe Up</SelectItem>
              <SelectItem value="wipeDown">Wipe Down</SelectItem>
            </SelectContent>
          </Select>
          {clip.transitionIn && (
            <div className="flex items-center gap-2">
              <Label htmlFor="transitionInDuration" className="text-[10px] text-zinc-400 flex-shrink-0">
                Duration
              </Label>
              <Input
                id="transitionInDuration"
                type="number"
                value={clip.transitionIn.duration}
                onChange={(e) => handleTransitionDurationChange('in', parseInt(e.target.value))}
                step={1}
                min={1}
                className="h-7 text-xs"
              />
              <span className="text-[10px] text-zinc-500 flex-shrink-0">frames</span>
            </div>
          )}
        </div>

        {/* Transition Out */}
        <div className="space-y-2">
          <Label htmlFor="transitionOut" className="text-xs text-zinc-400">Transition Out</Label>
          <Select
            value={clip.transitionOut?.type || 'none'}
            onValueChange={(value) => handleTransitionChange('out', value as Transition['type'] | 'none')}
          >
            <SelectTrigger id="transitionOut" className="h-8 text-xs">
              <SelectValue placeholder="None" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None</SelectItem>
              <SelectItem value="fade">Fade</SelectItem>
              <SelectItem value="crossDissolve">Cross Dissolve</SelectItem>
              <SelectItem value="wipeLeft">Wipe Left</SelectItem>
              <SelectItem value="wipeRight">Wipe Right</SelectItem>
              <SelectItem value="wipeUp">Wipe Up</SelectItem>
              <SelectItem value="wipeDown">Wipe Down</SelectItem>
            </SelectContent>
          </Select>
          {clip.transitionOut && (
            <div className="flex items-center gap-2">
              <Label htmlFor="transitionOutDuration" className="text-[10px] text-zinc-400 flex-shrink-0">
                Duration
              </Label>
              <Input
                id="transitionOutDuration"
                type="number"
                value={clip.transitionOut.duration}
                onChange={(e) => handleTransitionDurationChange('out', parseInt(e.target.value))}
                step={1}
                min={1}
                className="h-7 text-xs"
              />
              <span className="text-[10px] text-zinc-500 flex-shrink-0">frames</span>
            </div>
          )}
        </div>
      </div>
      </div>
    </div>
  )
}
