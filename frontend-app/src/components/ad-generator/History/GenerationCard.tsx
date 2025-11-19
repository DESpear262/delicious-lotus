import React, { useState } from 'react';
import { Card, CardBody } from '@/components/ad-generator/ui/Card';
import { Button } from '@/components/ad-generator/ui/Button';
import type { GenerationListItem, GenerationStatus } from '@/services/ad-generator/types';

export interface GenerationCardProps {
  generation: GenerationListItem;
  onView: (generationId: string) => void;
  onDownload: (generationId: string) => void;
  onDelete: (generationId: string) => void;
}

const STATUS_CONFIG: Record<
  GenerationStatus,
  { label: string; className: string }
> = {
  queued: { label: 'Queued', className: 'bg-gray-500/90 text-white' },
  processing: { label: 'Processing', className: 'bg-blue-500/90 text-white' },
  composing: { label: 'Composing', className: 'bg-violet-500/90 text-white' },
  completed: { label: 'Completed', className: 'bg-emerald-500/90 text-white' },
  failed: { label: 'Failed', className: 'bg-red-500/90 text-white' },
  cancelled: { label: 'Cancelled', className: 'bg-gray-400/90 text-white' },
};

export const GenerationCard: React.FC<GenerationCardProps> = ({
  generation,
  onView,
  onDownload,
  onDelete,
}) => {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const statusConfig = STATUS_CONFIG[generation.status];
  const createdDate = new Date(generation.created_at);
  const isCompleted = generation.status === 'completed';
  const canDownload = isCompleted;

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await onDelete(generation.generation_id);
    } catch (error) {
      console.error('Failed to delete generation:', error);
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const formatDate = (date: Date): string => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    });
  };

  return (
    <Card variant="bordered" hoverable className="transition-all duration-200 md:p-4">
      <CardBody>
        <div className="flex gap-4 p-4 md:flex-col md:gap-3">
          {/* Thumbnail */}
          <div className="relative shrink-0 w-[160px] h-[90px] rounded-md overflow-hidden bg-muted md:w-full md:h-[180px] md:aspect-video">
            {generation.thumbnail_url ? (
              <img
                src={generation.thumbnail_url}
                alt={`Generation ${generation.generation_id}`}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-muted via-muted/50 to-muted">
                <svg
                  className="w-12 h-12 text-muted-foreground"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                </svg>
              </div>
            )}
            <span className={`absolute top-2 right-2 py-1 px-2 rounded text-xs font-medium uppercase tracking-wide backdrop-blur-sm md:py-2 md:px-3 md:text-sm ${statusConfig.className}`}>
              {statusConfig.label}
            </span>
          </div>

          {/* Details */}
          <div className="flex-1 flex flex-col gap-3 min-w-0">
            <div className="flex flex-col gap-2">
              <h3 className="text-base font-medium text-foreground m-0 overflow-hidden text-ellipsis line-clamp-2 leading-normal">{generation.prompt}</h3>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span className="font-mono text-xs text-muted-foreground" title={generation.generation_id}>
                  ID: {generation.generation_id.substring(0, 8)}...
                </span>
                <span className="text-muted-foreground">•</span>
                <span className="whitespace-nowrap">{formatDate(createdDate)}</span>
                {isCompleted && generation.duration_seconds > 0 && (
                  <>
                    <span className="text-muted-foreground">•</span>
                    <span className="whitespace-nowrap">
                      {formatDuration(generation.duration_seconds)}
                    </span>
                  </>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 mt-auto md:flex-wrap">
              {!showDeleteConfirm ? (
                <>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onView(generation.generation_id)}
                    className="md:min-h-[44px] md:py-2 md:px-4"
                  >
                    View
                  </Button>
                  {canDownload && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onDownload(generation.generation_id)}
                      className="md:min-h-[44px] md:py-2 md:px-4"
                    >
                      Download
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setShowDeleteConfirm(true)}
                    className="text-red-500 hover:bg-red-500/10 md:min-h-[44px] md:py-2 md:px-4"
                  >
                    Delete
                  </Button>
                </>
              ) : (
                <div className="flex items-center gap-2 w-full">
                  <span className="text-sm text-muted-foreground mr-auto">Delete this generation?</span>
                  <Button
                    size="sm"
                    variant="danger"
                    onClick={handleDelete}
                    loading={isDeleting}
                    disabled={isDeleting}
                    className="md:min-h-[44px] md:py-2 md:px-4"
                  >
                    Confirm
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setShowDeleteConfirm(false)}
                    disabled={isDeleting}
                    className="md:min-h-[44px] md:py-2 md:px-4"
                  >
                    Cancel
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </CardBody>
    </Card>
  );
};
