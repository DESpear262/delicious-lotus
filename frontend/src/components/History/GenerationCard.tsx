/**
 * Generation Card Component
 * Displays a single generation item with thumbnail, status, and actions
 */

import React, { useState } from 'react';
import { Card, CardBody } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import type { GenerationListItem, GenerationStatus } from '@/api/types';
import styles from './GenerationCard.module.css';

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
  queued: { label: 'Queued', className: styles.statusQueued },
  processing: { label: 'Processing', className: styles.statusProcessing },
  composing: { label: 'Composing', className: styles.statusComposing },
  completed: { label: 'Completed', className: styles.statusCompleted },
  failed: { label: 'Failed', className: styles.statusFailed },
  cancelled: { label: 'Cancelled', className: styles.statusCancelled },
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
    <Card variant="bordered" hoverable className={styles.generationCard}>
      <CardBody padding="none">
        <div className={styles.cardContent}>
          {/* Thumbnail */}
          <div className={styles.thumbnail}>
            {generation.thumbnail_url ? (
              <img
                src={generation.thumbnail_url}
                alt={`Generation ${generation.generation_id}`}
                className={styles.thumbnailImage}
              />
            ) : (
              <div className={styles.thumbnailPlaceholder}>
                <svg
                  className={styles.placeholderIcon}
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
            <span className={`${styles.statusBadge} ${statusConfig.className}`}>
              {statusConfig.label}
            </span>
          </div>

          {/* Details */}
          <div className={styles.details}>
            <div className={styles.header}>
              <h3 className={styles.prompt}>{generation.prompt}</h3>
              <div className={styles.metadata}>
                <span className={styles.generationId} title={generation.generation_id}>
                  ID: {generation.generation_id.substring(0, 8)}...
                </span>
                <span className={styles.separator}>•</span>
                <span className={styles.date}>{formatDate(createdDate)}</span>
                {isCompleted && generation.duration_seconds > 0 && (
                  <>
                    <span className={styles.separator}>•</span>
                    <span className={styles.duration}>
                      {formatDuration(generation.duration_seconds)}
                    </span>
                  </>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className={styles.actions}>
              {!showDeleteConfirm ? (
                <>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onView(generation.generation_id)}
                  >
                    View
                  </Button>
                  {canDownload && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onDownload(generation.generation_id)}
                    >
                      Download
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setShowDeleteConfirm(true)}
                    className={styles.deleteButton}
                  >
                    Delete
                  </Button>
                </>
              ) : (
                <div className={styles.deleteConfirm}>
                  <span className={styles.confirmText}>Delete this generation?</span>
                  <Button
                    size="sm"
                    variant="danger"
                    onClick={handleDelete}
                    loading={isDeleting}
                    disabled={isDeleting}
                  >
                    Confirm
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setShowDeleteConfirm(false)}
                    disabled={isDeleting}
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
