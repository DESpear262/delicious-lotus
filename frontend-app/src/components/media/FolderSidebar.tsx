import { useState, useCallback } from 'react';
import { Folder, FolderPlus, Trash2, ChevronRight, ChevronDown } from 'lucide-react';
import { useMediaStore } from '../../contexts/StoreContext';
import { Button } from '../ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import type { MediaFolder } from '../../types/stores';

/**
 * FolderSidebar component for folder navigation and management
 */
export function FolderSidebar() {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [folderToDelete, setFolderToDelete] = useState<string | null>(null);

  const folders = useMediaStore((state) => state.folders);
  const currentFolderId = useMediaStore((state) => state.currentFolderId);
  const assets = useMediaStore((state) => state.assets);

  const createFolder = useMediaStore((state) => state.createFolder);
  const removeFolder = useMediaStore((state) => state.removeFolder);
  const setCurrentFolder = useMediaStore((state) => state.setCurrentFolder);

  // Get asset count for a folder
  const getAssetCount = useCallback(
    (folderId?: string) => {
      let count = 0;
      assets.forEach((asset) => {
        if (asset.folderId === folderId) {
          count++;
        }
      });
      return count;
    },
    [assets]
  );

  // Toggle folder expansion
  const toggleFolder = useCallback((folderId: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(folderId)) {
        next.delete(folderId);
      } else {
        next.add(folderId);
      }
      return next;
    });
  }, []);

  // Handle folder click
  const handleFolderClick = useCallback(
    (folderId?: string) => {
      setCurrentFolder(folderId);
    },
    [setCurrentFolder]
  );

  // Handle create folder
  const handleCreateFolder = useCallback(() => {
    if (newFolderName.trim()) {
      createFolder({
        name: newFolderName.trim(),
        parentId: undefined,
      });
      setNewFolderName('');
      setShowCreateDialog(false);
    }
  }, [newFolderName, createFolder]);

  // Handle delete folder
  const handleDeleteFolder = useCallback(() => {
    if (folderToDelete) {
      removeFolder(folderToDelete);
      setFolderToDelete(null);
      setShowDeleteDialog(false);
    }
  }, [folderToDelete, removeFolder]);

  // Render folder item
  const renderFolder = useCallback(
    (folder: MediaFolder, level: number = 0) => {
      const isExpanded = expandedFolders.has(folder.id);
      const isActive = currentFolderId === folder.id;
      const assetCount = getAssetCount(folder.id);
      const childFolders = folders.filter((f) => f.parentId === folder.id);

      return (
        <div key={folder.id}>
          <div
            className={`
              flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors
              ${isActive ? 'bg-blue-500/20 text-blue-400' : 'hover:bg-zinc-800 text-zinc-300'}
            `}
            style={{ paddingLeft: `${12 + level * 16}px` }}
          >
            {childFolders.length > 0 && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  toggleFolder(folder.id);
                }}
                className="p-0.5 hover:bg-zinc-700 rounded"
              >
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </button>
            )}
            {childFolders.length === 0 && <div className="w-5" />}

            <div
              onClick={() => handleFolderClick(folder.id)}
              className="flex items-center gap-2 flex-1 min-w-0"
            >
              <Folder className="w-4 h-4 flex-shrink-0" />
              <span className="text-sm truncate flex-1">{folder.name}</span>
              <span className="text-xs text-zinc-500 flex-shrink-0">{assetCount}</span>
            </div>

            <button
              onClick={(e) => {
                e.stopPropagation();
                setFolderToDelete(folder.id);
                setShowDeleteDialog(true);
              }}
              className="p-1 hover:bg-red-500/20 hover:text-red-400 rounded opacity-0 group-hover:opacity-100 transition-opacity"
              title="Delete folder"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          </div>

          {/* Render child folders */}
          {isExpanded &&
            childFolders.map((childFolder) => renderFolder(childFolder, level + 1))}
        </div>
      );
    },
    [
      expandedFolders,
      currentFolderId,
      folders,
      getAssetCount,
      toggleFolder,
      handleFolderClick,
    ]
  );

  // Get top-level folders
  const topLevelFolders = folders.filter((f) => !f.parentId);
  const allMediaCount = getAssetCount(undefined);

  return (
    <div className="w-64 bg-zinc-950 border-r border-zinc-800 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-zinc-800">
        <h2 className="text-sm font-semibold text-zinc-200 mb-3">Folders</h2>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowCreateDialog(true)}
          className="w-full"
        >
          <FolderPlus className="w-4 h-4 mr-2" />
          New Folder
        </Button>
      </div>

      {/* Folder List */}
      <div className="flex-1 overflow-y-auto p-2">
        {/* All Media */}
        <div
          className={`
            group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors mb-2
            ${currentFolderId === undefined ? 'bg-blue-500/20 text-blue-400' : 'hover:bg-zinc-800 text-zinc-300'}
          `}
          onClick={() => handleFolderClick(undefined)}
        >
          <Folder className="w-4 h-4" />
          <span className="text-sm flex-1">All Media</span>
          <span className="text-xs text-zinc-500">{allMediaCount}</span>
        </div>

        {/* Folders */}
        <div className="space-y-1">
          {topLevelFolders.map((folder) => (
            <div key={folder.id} className="group">
              {renderFolder(folder)}
            </div>
          ))}
        </div>

        {topLevelFolders.length === 0 && (
          <div className="text-center py-8 text-zinc-500 text-sm">
            No folders yet. Create one to organize your media.
          </div>
        )}
      </div>

      {/* Create Folder Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Folder</DialogTitle>
            <DialogDescription>Enter a name for your new folder.</DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <input
              type="text"
              placeholder="Folder name"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleCreateFolder();
                }
              }}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateFolder} disabled={!newFolderName.trim()}>
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Folder Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Folder</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this folder? Assets in this folder will be moved
              to All Media.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteFolder}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
