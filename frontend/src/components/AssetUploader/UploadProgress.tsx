/**
 * UploadProgress Component
 * Display upload progress for individual files
 */

import { formatFileSize } from '@/api/services/assets';
import type { UploadState } from '@/hooks/useFileUpload';
import './UploadProgress.css';

interface UploadProgressProps {
  upload: UploadState;
  onCancel: () => void;
}

// Simple check icon component
function CheckIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M13.3334 4L6.00002 11.3333L2.66669 8"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// Simple error icon component
function ErrorIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M8 2L2 13.5H14L8 2Z"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M8 7V9"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
      />
      <circle cx="8" cy="11.5" r="0.5" fill="currentColor" />
    </svg>
  );
}

export function UploadProgress({
  upload,
  onCancel,
}: UploadProgressProps) {
  const isUploading = upload.status === 'uploading';
  const isSuccess = upload.status === 'success';
  const isError = upload.status === 'error';

  return (
    <div className="upload-progress">
      <div className="upload-progress__info">
        <p className="upload-progress__filename">{upload.file.name}</p>
        <p className="upload-progress__size">
          {formatFileSize(upload.file.size)}
        </p>
      </div>

      <div className="upload-progress__bar-container">
        <div
          className={`upload-progress__bar ${
            isSuccess
              ? 'upload-progress__bar--success'
              : isError
              ? 'upload-progress__bar--error'
              : ''
          }`}
          style={{ width: `${upload.progress}%` }}
        />
      </div>

      <div className="upload-progress__status">
        {isUploading && (
          <>
            <span>{upload.progress}%</span>
            <button
              className="upload-progress__cancel"
              onClick={onCancel}
              aria-label="Cancel upload"
            >
              Cancel
            </button>
          </>
        )}

        {isSuccess && (
          <span className="upload-progress__success">
            <CheckIcon /> Uploaded
          </span>
        )}

        {isError && (
          <span className="upload-progress__error">
            <ErrorIcon /> {upload.error || 'Upload failed'}
          </span>
        )}
      </div>
    </div>
  );
}
