/**
 * FilePreview Component
 * Preview component for uploaded files (images and audio)
 */

import { formatFileSize } from '@/services/ad-generator/services/assets';
import type { UploadedAsset } from '@/hooks/ad-generator/useFileUpload';
import './FilePreview.css';

interface FilePreviewProps {
  asset: UploadedAsset;
  onRemove: () => void;
  onClick?: () => void;
}

// Simple audio icon component
function AudioIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
      />
    </svg>
  );
}

// Simple close icon component
function CloseIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M12 4L4 12M4 4L12 12"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function truncateFilename(filename: string, maxLength: number): string {
  if (filename.length <= maxLength) return filename;

  const ext = filename.split('.').pop() || '';
  const name = filename.slice(0, filename.length - ext.length - 1);
  const truncated = name.slice(0, maxLength - ext.length - 4);
  return `${truncated}...${ext}`;
}

export function FilePreview({
  asset,
  onRemove,
  onClick,
}: FilePreviewProps) {
  const isImage = asset.type.startsWith('image/');
  const isAudio = asset.type.startsWith('audio/');

  return (
    <div className="file-preview">
      {/* Preview content */}
      <div
        className="file-preview__content"
        onClick={onClick}
        role={onClick ? 'button' : undefined}
        tabIndex={onClick ? 0 : undefined}
        onKeyDown={
          onClick
            ? (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onClick();
                }
              }
            : undefined
        }
      >
        {isImage && (
          <img
            src={asset.thumbnail || asset.url}
            alt={asset.filename}
            className="file-preview__image"
          />
        )}

        {isAudio && (
          <div className="file-preview__audio">
            <AudioIcon className="file-preview__audio-icon" />
            <audio src={asset.url} controls className="file-preview__audio-player" />
          </div>
        )}
      </div>

      {/* File info */}
      <div className="file-preview__info">
        <p className="file-preview__filename" title={asset.filename}>
          {truncateFilename(asset.filename, 20)}
        </p>
        <p className="file-preview__size">{formatFileSize(asset.size)}</p>
        {asset.metadata?.dimensions &&
          typeof asset.metadata.dimensions === 'object' &&
          'width' in asset.metadata.dimensions &&
          'height' in asset.metadata.dimensions ? (
            <p className="file-preview__dimensions">
              {(asset.metadata.dimensions as { width: number; height: number }).width} ×{' '}
              {(asset.metadata.dimensions as { width: number; height: number }).height}
            </p>
          ) : null}
      </div>

      {/* Remove button */}
      <button
        className="file-preview__remove"
        onClick={(e) => {
          e.stopPropagation();
          onRemove();
        }}
        aria-label={`Remove ${asset.filename}`}
        title="Remove"
      >
        <CloseIcon />
      </button>
    </div>
  );
}
