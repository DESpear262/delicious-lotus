/**
 * DropZone Component
 * Drag-and-drop zone for file uploads
 */

import { useState, useRef } from 'react';
import { formatFileSize } from '@/services/ad-generator/services/assets';
import './DropZone.css';

interface DropZoneProps {
  accept: string;
  maxSize: number;
  multiple: boolean;
  onFilesSelected: (files: FileList | File[]) => void;
  disabled?: boolean;
}

// Simple upload icon component
function UploadIcon({ className }: { className?: string }) {
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
        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
      />
    </svg>
  );
}

function formatAcceptedTypes(accept: string): string {
  if (accept === 'image/*') return 'JPEG, PNG';
  if (accept === 'audio/*') return 'MP3, WAV';
  if (accept.includes('image') && accept.includes('audio'))
    return 'Images, Audio';
  return accept;
}

export function DropZone({
  accept,
  maxSize,
  multiple,
  onFilesSelected,
  disabled = false,
}: DropZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled) return;

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      onFilesSelected(files);
    }
  };

  const handleClick = () => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onFilesSelected(files);
    }
    // Reset input value to allow re-uploading same file
    e.target.value = '';
  };

  return (
    <div
      className={`drop-zone ${isDragging ? 'drop-zone--dragging' : ''} ${
        disabled ? 'drop-zone--disabled' : ''
      }`}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={handleClick}
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label="Upload files"
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleFileInputChange}
        className="drop-zone__input"
        aria-hidden="true"
        tabIndex={-1}
      />

      <div className="drop-zone__content">
        <UploadIcon className="drop-zone__icon" />
        <p className="drop-zone__text">
          {isDragging
            ? 'Drop files here'
            : 'Drag and drop files here, or click to browse'}
        </p>
        <p className="drop-zone__hint">
          {formatAcceptedTypes(accept)} • Max {formatFileSize(maxSize)}
        </p>
      </div>
    </div>
  );
}
