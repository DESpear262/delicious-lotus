import { useState } from 'react'
import { Sparkles, Image, Video } from 'lucide-react'
import { Button } from '../ui/button'
import { Label } from '../ui/label'
import type { GenerationType, QualityTier } from '../../types/stores'

interface PromptInputProps {
  onGenerate: (params: {
    prompt: string
    type: GenerationType
    qualityTier: QualityTier
    aspectRatio: '16:9' | '9:16' | '1:1' | '4:3'
  }) => void
  isGenerating?: boolean
}

export default function PromptInput({ onGenerate, isGenerating = false }: PromptInputProps) {
  const [prompt, setPrompt] = useState('')
  const [generationType, setGenerationType] = useState<GenerationType>('image')
  const [qualityTier, setQualityTier] = useState<QualityTier>('draft')
  const [aspectRatio, setAspectRatio] = useState<'16:9' | '9:16' | '1:1' | '4:3'>('16:9')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (prompt.trim()) {
      onGenerate({ prompt, type: generationType, qualityTier, aspectRatio })
    }
  }

  const maxChars = 500
  const charsRemaining = maxChars - prompt.length

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Generation Type Toggle */}
      <div className="space-y-2">
        <Label>Generation Type</Label>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setGenerationType('image')}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border transition-colors ${
              generationType === 'image'
                ? 'bg-blue-500 border-blue-500 text-white'
                : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:border-zinc-700'
            }`}
          >
            <Image className="w-5 h-5" />
            <span>Image</span>
          </button>
          <button
            type="button"
            onClick={() => setGenerationType('video')}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border transition-colors ${
              generationType === 'video'
                ? 'bg-blue-500 border-blue-500 text-white'
                : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:border-zinc-700'
            }`}
          >
            <Video className="w-5 h-5" />
            <span>Video</span>
          </button>
        </div>
      </div>

      {/* Prompt Input */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="prompt">Prompt</Label>
          <span
            className={`text-sm ${charsRemaining < 50 ? 'text-orange-500' : 'text-zinc-500'}`}
          >
            {charsRemaining} characters remaining
          </span>
        </div>
        <textarea
          id="prompt"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value.slice(0, maxChars))}
          placeholder={`Describe the ${generationType} you want to generate...`}
          className="w-full h-24 bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-3 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          disabled={isGenerating}
        />
      </div>

      {/* Quality Tier (Images only) */}
      {generationType === 'image' && (
        <div className="space-y-2">
          <Label>Quality</Label>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setQualityTier('draft')}
              className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
                qualityTier === 'draft'
                  ? 'bg-zinc-800 border-zinc-700 text-zinc-100'
                  : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:border-zinc-700'
              }`}
            >
              Draft
            </button>
            <button
              type="button"
              onClick={() => setQualityTier('production')}
              className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
                qualityTier === 'production'
                  ? 'bg-zinc-800 border-zinc-700 text-zinc-100'
                  : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:border-zinc-700'
              }`}
            >
              Production
            </button>
          </div>
        </div>
      )}

      {/* Aspect Ratio */}
      <div className="space-y-2">
        <Label>Aspect Ratio</Label>
        <div className="grid grid-cols-4 gap-2">
          {(['16:9', '9:16', '1:1', '4:3'] as const).map((ratio) => (
            <button
              key={ratio}
              type="button"
              onClick={() => setAspectRatio(ratio)}
              className={`px-4 py-2 rounded-lg border transition-colors ${
                aspectRatio === ratio
                  ? 'bg-zinc-800 border-zinc-700 text-zinc-100'
                  : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:border-zinc-700'
              }`}
            >
              {ratio}
            </button>
          ))}
        </div>
      </div>

      {/* Generate Button */}
      <Button
        type="submit"
        disabled={!prompt.trim() || isGenerating}
        className="w-full flex items-center justify-center gap-2"
      >
        <Sparkles className="w-5 h-5" />
        {isGenerating ? 'Generating...' : `Generate ${generationType === 'image' ? 'Image' : 'Video'}`}
      </Button>
    </form>
  )
}
