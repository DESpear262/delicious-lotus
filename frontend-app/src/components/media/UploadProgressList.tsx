import { memo, useCallback } from 'react';
import { X, FileIcon, CheckCircle, AlertCircle } from 'lucide-react';
import { useMediaStore } from '../../contexts/StoreContext';
import { Progress } from '../ui/progress';
import type { UploadItem } from '../../types/stores';

/**
 * Individual upload progress item component
 */
const UploadProgressItem = memo(({ upload }: { upload: UploadItem }) => {
  const cancelUpload = useMediaStore((state) => state.cancelUpload);

  const handleCancel = useCallback(() => {
    cancelUpload(upload.id);
  }, [cancelUpload, upload.id]);

  // Format file size
  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  };

  // Get status icon and color
  const getStatusDisplay = () => {
    switch (upload.status) {
      case 'completed':
        return {
          icon: <CheckCircle className="w-4 h-4 text-green-500" />,
          color: 'text-green-500',
          label: 'Completed',
        };
      case 'failed':
        return {
          icon: <AlertCircle className="w-4 h-4 text-red-500" />,
          color: 'text-red-500',
          label: upload.error || 'Failed',
        };
      case 'cancelled':
        return {
          icon: <X className="w-4 h-4 text-zinc-500" />,
          color: 'text-zinc-500',
          label: 'Cancelled',
        };
      case 'uploading':
        return {
          icon: null,
          color: 'text-blue-500',
          label: `${upload.progress.toFixed(0)}%`,
        };
      case 'queued':
      default:
        return {
          icon: null,
          color: 'text-zinc-400',
          label: 'Queued',
        };
    }
  };

  const statusDisplay = getStatusDisplay();

  return (
    <div className="flex items-center gap-3 p-3 bg-zinc-900 rounded-lg border border-zinc-800">
      {/* File Icon */}
      <div className="flex-shrink-0">
        <FileIcon className="w-8 h-8 text-zinc-600" />
      </div>

      {/* File Info and Progress */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <p className="text-sm font-medium text-zinc-200 truncate">
            {upload.file.name}
          </p>
          <div className="flex items-center gap-2 ml-2">
            {statusDisplay.icon}
            <span className={`text-xs font-medium ${statusDisplay.color}`}>
              {statusDisplay.label}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs text-zinc-500">
            {formatSize(upload.file.size)}
          </span>
        </div>

        {/* Progress Bar */}
        {(upload.status === 'uploading' || upload.status === 'queued') && (
          <Progress value={upload.progress} className="h-1" />
        )}

        {/* Error Message */}
        {upload.status === 'failed' && upload.error && (
          <p className="text-xs text-red-400 mt-1">{upload.error}</p>
        )}
      </div>

      {/* Cancel Button */}
      {upload.status === 'uploading' && (
        <button
          onClick={handleCancel}
          className="flex-shrink-0 p-1 rounded hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
          title="Cancel upload"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison for memoization
  return (
    prevProps.upload.id === nextProps.upload.id &&
    prevProps.upload.progress === nextProps.upload.progress &&
    prevProps.upload.status === nextProps.upload.status &&
    prevProps.upload.error === nextProps.upload.error
  );
});

UploadProgressItem.displayName = 'UploadProgressItem';

/**
 * Upload progress list component showing all active uploads
 */
export function UploadProgressList() {
  const uploadQueue = useMediaStore((state) => state.uploadQueue);

  // Don't render if no uploads
  if (uploadQueue.length === 0) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 w-96 max-h-96 overflow-y-auto z-30">
      <div className="bg-zinc-950 border border-zinc-800 rounded-lg shadow-2xl">
        <div className="p-3 border-b border-zinc-800">
          <h3 className="text-sm font-semibold text-zinc-200">
            Uploads ({uploadQueue.length})
          </h3>
        </div>
        <div className="p-3 space-y-2">
          {uploadQueue.map((upload) => (
            <UploadProgressItem key={upload.id} upload={upload} />
          ))}
        </div>
      </div>
    </div>
  );
}
