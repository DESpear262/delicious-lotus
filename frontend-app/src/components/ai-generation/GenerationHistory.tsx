import { useState } from 'react'
import { Search, Heart, RotateCcw, Trash2, Image, Video } from 'lucide-react'
import type { GenerationHistory as GenerationHistoryType } from '../../types/stores'

interface GenerationHistoryProps {
  history: GenerationHistoryType[]
  onRerun: (prompt: string, type: 'image' | 'video', aspectRatio: string, qualityTier?: string) => void
  onToggleFavorite: (historyId: string) => void
  onDelete: (historyId: string) => void
  onAddToTimeline?: (assetId: string) => void
}

export default function GenerationHistory({
  history,
  onRerun,
  onToggleFavorite,
  onDelete,
  onAddToTimeline,
}: GenerationHistoryProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState<'all' | 'image' | 'video'>('all')
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false)

  // Filter history
  const filteredHistory = history.filter((item) => {
    // Search filter
    if (searchQuery && !item.request.prompt.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false
    }

    // Type filter
    if (filterType !== 'all' && item.request.type !== filterType) {
      return false
    }

    // Favorites filter
    if (showFavoritesOnly && !item.isFavorite) {
      return false
    }

    return true
  })

  if (history.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="bg-zinc-900 border-2 border-dashed border-zinc-800 rounded-lg p-8 max-w-md">
          <RotateCcw className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-zinc-300 mb-2">No Generation History</h3>
          <p className="text-zinc-500 text-sm">
            Your completed generations will appear here for easy access
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Search and Filters */}
      <div className="space-y-3">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search history..."
            className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-10 pr-4 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Filter Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-sm transition-colors ${showFavoritesOnly
                ? 'bg-pink-500/20 border-pink-500/50 text-pink-400'
                : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:border-zinc-700'
              }`}
          >
            <Heart className={`w-4 h-4 ${showFavoritesOnly ? 'fill-current' : ''}`} />
            Favorites
          </button>

          <div className="flex gap-1 ml-auto">
            {(['all', 'image', 'video'] as const).map((type) => (
              <button
                key={type}
                onClick={() => setFilterType(type)}
                className={`px-3 py-1.5 rounded-lg border text-sm capitalize transition-colors ${filterType === type
                    ? 'bg-zinc-800 border-zinc-700 text-zinc-100'
                    : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:border-zinc-700'
                  }`}
              >
                {type}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* History Grid */}
      {filteredHistory.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-zinc-500 text-sm">No items match your filters</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {filteredHistory.map((item) => (
            <HistoryCard
              key={item.id}
              item={item}
              onRerun={onRerun}
              onToggleFavorite={onToggleFavorite}
              onDelete={onDelete}
              onAddToTimeline={onAddToTimeline}
            />
          ))}
        </div>
      )}
    </div>
  )
}

interface HistoryCardProps {
  item: GenerationHistoryType
  onRerun: (prompt: string, type: 'image' | 'video', aspectRatio: string, qualityTier?: string) => void
  onToggleFavorite: (historyId: string) => void
  onDelete: (historyId: string) => void
  onAddToTimeline?: (assetId: string) => void
}

function HistoryCard({ item, onRerun, onToggleFavorite, onDelete }: HistoryCardProps) {
  const [showActions, setShowActions] = useState(false)

  return (
    <div
      className="group relative bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden hover:border-zinc-700 transition-colors"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      {/* Thumbnail / Placeholder */}
      <div className="aspect-video bg-zinc-800 flex items-center justify-center relative">
        {item.request.resultUrl ? (
          <img
            src={item.request.resultUrl}
            alt={item.request.prompt}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="text-zinc-600">
            {item.request.type === 'image' ? (
              <Image className="w-12 h-12" />
            ) : (
              <Video className="w-12 h-12" />
            )}
          </div>
        )}

        {/* Favorite Badge */}
        {item.isFavorite && (
          <div className="absolute top-2 right-2">
            <Heart className="w-5 h-5 text-pink-500 fill-current drop-shadow-lg" />
          </div>
        )}

        {/* Hover Actions */}
        {showActions && (
          <div className="absolute inset-0 bg-black/60 flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={() => onToggleFavorite(item.id)}
              className="p-2 bg-zinc-900 rounded-lg hover:bg-zinc-800 transition-colors"
              title={item.isFavorite ? 'Remove from favorites' : 'Add to favorites'}
            >
              <Heart className={`w-5 h-5 ${item.isFavorite ? 'text-pink-500 fill-current' : 'text-zinc-400'}`} />
            </button>
            <button
              onClick={() =>
                onRerun(
                  item.request.prompt,
                  item.request.type as 'image' | 'video',
                  item.request.aspectRatio,
                  item.request.qualityTier
                )
              }
              className="p-2 bg-zinc-900 rounded-lg hover:bg-zinc-800 transition-colors"
              title="Rerun generation"
            >
              <RotateCcw className="w-5 h-5 text-zinc-400" />
            </button>
            <button
              onClick={() => onDelete(item.id)}
              className="p-2 bg-zinc-900 rounded-lg hover:bg-red-900 transition-colors"
              title="Delete from history"
            >
              <Trash2 className="w-5 h-5 text-zinc-400 group-hover:text-red-400" />
            </button>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-3">
        <p className="text-xs text-zinc-100 line-clamp-2 mb-2">{item.request.prompt}</p>
        <div className="flex items-center justify-between text-xs text-zinc-500">
          <span className="capitalize">{item.request.type}</span>
          <span>{item.request.aspectRatio}</span>
        </div>
      </div>
    </div>
  )
}
