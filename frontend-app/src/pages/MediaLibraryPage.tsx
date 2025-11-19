import { Upload, Search, Sparkles, Trash2 } from 'lucide-react';
import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import AIGenerationPanel from '../components/ai-generation/AIGenerationPanel';
import { MediaLibraryUpload } from '../components/media/MediaLibraryUpload';
import { UploadProgressList } from '../components/media/UploadProgressList';
import { MediaAssetCard } from '../components/media/MediaAssetCard';
import { MediaPreviewModal } from '../components/media/MediaPreviewModal';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Button } from '../components/ui/button';
import { useMediaStore } from '../contexts/StoreContext';
import type { MediaAssetType, MediaAsset } from '../types/stores';

/**
 * Media library page for asset management interface
 */
export default function MediaLibraryPage() {
  const [showAIPanel, setShowAIPanel] = useState(false);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [lastSelectedIndex, setLastSelectedIndex] = useState<number>(-1);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<MediaAssetType | 'all'>('all');
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [previewAsset, setPreviewAsset] = useState<MediaAsset | null>(null);
  const uploadInputRef = useRef<HTMLInputElement>(null);

  // Access MediaStore state and actions
  const assets = useMediaStore((state) => state.assets);
  const selectedAssetIds = useMediaStore((state) => state.selectedAssetIds);

  const queueUpload = useMediaStore((state) => state.queueUpload);
  const selectAsset = useMediaStore((state) => state.selectAsset);
  const clearAssetSelection = useMediaStore((state) => state.clearAssetSelection);
  const deleteAsset = useMediaStore((state) => state.deleteAsset);
  const searchAssets = useMediaStore((state) => state.searchAssets);
  const loadAssets = useMediaStore((state) => state.loadAssets);

  // Convert assets Map to array and apply filters
  const assetsArray = useMemo(() => {
    let arr = Array.from(assets.values());

    // Filter by type
    if (filterType !== 'all') {
      arr = arr.filter((asset) => asset.type === filterType);
    }

    // Apply search query
    if (searchQuery.trim()) {
      const lowerQuery = searchQuery.toLowerCase();
      arr = arr.filter(
        (asset) =>
          asset.name.toLowerCase().includes(lowerQuery) ||
          JSON.stringify(asset.metadata).toLowerCase().includes(lowerQuery)
      );
    }

    return arr;
  }, [assets, filterType, searchQuery]);

  // Handle file selection from file input
  const handleFilesSelected = useCallback((files: File[]) => {
    files.forEach((file) => {
      queueUpload(file);
    });
  }, [queueUpload]);

  // Trigger file picker programmatically
  const triggerUpload = useCallback(() => {
    uploadInputRef.current?.click();
  }, []);

  // Handle asset click with multi-select support
  const handleAssetClick = useCallback(
    (assetId: string, index: number, event: React.MouseEvent) => {
      if (event.shiftKey && lastSelectedIndex !== -1) {
        // Shift-click: range selection
        const start = Math.min(lastSelectedIndex, index);
        const end = Math.max(lastSelectedIndex, index);
        const selectedRange = assetsArray.slice(start, end + 1);

        // Clear current selection and select range
        clearAssetSelection();
        selectedRange.forEach((asset) => selectAsset(asset.id, true));
      } else if (event.ctrlKey || event.metaKey) {
        // Ctrl/Cmd-click: toggle individual selection
        selectAsset(assetId, true);
        setLastSelectedIndex(index);
      } else {
        // Regular click: single selection
        selectAsset(assetId, false);
        setLastSelectedIndex(index);
      }
    },
    [assetsArray, lastSelectedIndex, selectAsset, clearAssetSelection]
  );

  // Handle asset deletion
  const handleDeleteAssets = useCallback(async () => {
    if (selectedAssetIds.length === 0) {
      setShowDeleteDialog(false);
      return;
    }

    // Delete all selected assets
    const deletePromises = selectedAssetIds.map((assetId) => deleteAsset(assetId));

    try {
      await Promise.all(deletePromises);
      clearAssetSelection();
      setShowDeleteDialog(false);
      console.log(`Successfully deleted ${selectedAssetIds.length} asset(s)`);
    } catch (error) {
      console.error('Failed to delete some assets:', error);
      // Keep dialog open on error so user can retry
    }
  }, [selectedAssetIds, deleteAsset, clearAssetSelection]);

  // Handle individual asset delete
  const handleDeleteSingleAsset = useCallback(
    async (assetId: string) => {
      try {
        await deleteAsset(assetId);
        console.log('Successfully deleted asset');
      } catch (error) {
        console.error('Failed to delete asset:', error);
      }
    },
    [deleteAsset]
  );

  // Handle asset preview
  const handleAssetPreview = useCallback(
    (asset: MediaAsset) => {
      setPreviewAsset(asset);
    },
    []
  );

  // Load assets from backend on mount
  useEffect(() => {
    console.log('[MediaLibraryPage] Loading assets from backend');
    loadAssets()
      .then(() => console.log('[MediaLibraryPage] Assets loaded successfully'))
      .catch((error) => console.error('[MediaLibraryPage] Failed to load assets:', error));
  }, [loadAssets]);

  // Keyboard shortcut for select all (Ctrl/Cmd+A)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
        e.preventDefault();
        clearAssetSelection();
        assetsArray.forEach((asset) => selectAsset(asset.id, true));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [assetsArray, selectAsset, clearAssetSelection]);

  return (
    <div className="flex h-full">
      {/* Main Content Area */}
      <div className="flex-1 p-8 overflow-auto">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-zinc-100">Media Library</h1>
              <p className="text-zinc-400 mt-2">
                {assetsArray.length} {assetsArray.length === 1 ? 'asset' : 'assets'}
                {selectedAssetIds.length > 0 && (
                  <span className="ml-2 text-blue-400">
                    • {selectedAssetIds.length} selected
                  </span>
                )}
              </p>
            </div>
            <div className="flex gap-2">
              {selectedAssetIds.length > 0 && (
                <button
                  onClick={() => setShowDeleteDialog(true)}
                  className="flex items-center gap-2 bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  <Trash2 className="w-5 h-5" />
                  Delete ({selectedAssetIds.length})
                </button>
              )}
              <button
                onClick={() => setShowAIPanel(!showAIPanel)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                  showAIPanel
                    ? 'bg-purple-500 hover:bg-purple-600 text-white'
                    : 'bg-zinc-800 hover:bg-zinc-700 text-zinc-200'
                }`}
              >
                <Sparkles className="w-5 h-5" />
                AI Generate
              </button>
              <button
                onClick={() => setShowUploadDialog(true)}
                className="flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors"
              >
                <Upload className="w-5 h-5" />
                Upload Media
              </button>
            </div>
          </div>

          {/* Search and Filters */}
          <div className="mb-6 flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
              <input
                type="text"
                placeholder="Search media..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-10 pr-4 py-3 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value as MediaAssetType | 'all')}
              className="bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-3 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Types</option>
              <option value="image">Images</option>
              <option value="video">Videos</option>
              <option value="audio">Audio</option>
            </select>
          </div>

          {/* Media Grid */}
          {assetsArray.length === 0 ? (
            /* Empty State */
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="bg-zinc-900 border-2 border-dashed border-zinc-800 rounded-lg p-12 max-w-md">
                <Upload className="w-16 h-16 text-zinc-700 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-zinc-300 mb-2">No media yet</h3>
                <p className="text-zinc-500 mb-6">
                  Upload images, videos, or audio files, or generate content with AI
                </p>
                <div className="flex gap-2 justify-center">
                  <button
                    onClick={() => setShowUploadDialog(true)}
                    className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg transition-colors"
                  >
                    Upload Media
                  </button>
                  <button
                    onClick={() => setShowAIPanel(true)}
                    className="bg-purple-500 hover:bg-purple-600 text-white px-6 py-2 rounded-lg transition-colors flex items-center gap-2"
                  >
                    <Sparkles className="w-4 h-4" />
                    Generate with AI
                  </button>
                </div>
              </div>
            </div>
          ) : (
            /* Asset Grid */
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {assetsArray.map((asset, index) => (
                <MediaAssetCard
                  key={asset.id}
                  asset={asset}
                  isSelected={selectedAssetIds.includes(asset.id)}
                  onClick={(e) => handleAssetClick(asset.id, index, e)}
                  onDelete={() => handleDeleteSingleAsset(asset.id)}
                  onPreview={() => handleAssetPreview(asset)}
                />
              ))}
            </div>
          )}

          {/* Hidden file input for quick upload */}
          <input
            ref={uploadInputRef}
            type="file"
            className="hidden"
            accept="image/*,video/*,audio/*"
            multiple
            onChange={(e) => {
              const files = e.target.files ? Array.from(e.target.files) : [];
              if (files.length > 0) {
                handleFilesSelected(files);
              }
              // Reset input value to allow selecting the same file again
              if (uploadInputRef.current) {
                uploadInputRef.current.value = '';
              }
            }}
          />
        </div>
      </div>

      {/* Upload Panel (Slide-in from right) */}
      {showUploadDialog && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => setShowUploadDialog(false)}
          />

          {/* Panel */}
          <div className="fixed right-0 top-0 bottom-0 w-[550px] bg-zinc-950 border-l border-zinc-800 z-50 shadow-2xl">
            <div className="flex items-center justify-between p-4 border-b border-zinc-800">
              <h2 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
                <Upload className="w-5 h-5 text-blue-500" />
                Upload Media
              </h2>
              <button
                onClick={() => setShowUploadDialog(false)}
                className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100 transition-colors"
              >
                ×
              </button>
            </div>
            <div className="h-[calc(100%-65px)] overflow-auto p-4">
              <MediaLibraryUpload />
            </div>
          </div>
        </>
      )}

      {/* AI Generation Panel (Slide-in from right) */}
      {showAIPanel && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => setShowAIPanel(false)}
          />

          {/* Panel */}
          <div className="fixed right-0 top-0 bottom-0 w-[450px] bg-zinc-950 border-l border-zinc-800 z-50 shadow-2xl">
            <div className="flex items-center justify-between p-4 border-b border-zinc-800">
              <h2 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-500" />
                AI Generation
              </h2>
              <button
                onClick={() => setShowAIPanel(false)}
                className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100 transition-colors"
              >
                ×
              </button>
            </div>
            <div className="h-[calc(100%-65px)]">
              <AIGenerationPanel />
            </div>
          </div>
        </>
      )}

      {/* Upload Progress List */}
      <UploadProgressList />

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Assets</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete {selectedAssetIds.length}{' '}
              {selectedAssetIds.length === 1 ? 'asset' : 'assets'}? This action cannot be
              undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteAssets}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Media Preview Modal */}
      <MediaPreviewModal
        asset={previewAsset}
        isOpen={!!previewAsset}
        onClose={() => setPreviewAsset(null)}
      />
    </div>
  );
}
