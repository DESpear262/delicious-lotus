/**
 * AssetUploader Component
 * Main upload component with drag-and-drop, validation, and progress tracking
 */

import { useState, useEffect } from 'react';
import { DropZone } from './DropZone';
import { FilePreview } from './FilePreview';
import { UploadProgress } from './UploadProgress';
import { useFileUpload, type UploadedAsset, type UploadState } from '@/hooks/useFileUpload';
import { validateFile } from '@/utils/fileValidation';
import './AssetUploader.css';

export interface AssetUploaderProps {
  accept?: string; // File types: 'image/*', 'audio/*'
  maxSize?: number; // Max file size in bytes (default: 50MB images, 100MB audio)
  maxFiles?: number; // Max number of files (default: 1)
  multiple?: boolean; // Allow multiple files
  onUploadComplete?: (assets: UploadedAsset[]) => void;
  onUploadError?: (error: Error) => void;
  onFilesSelected?: (files: File[]) => void;
  className?: string;
  existingAssets?: UploadedAsset[]; // Pre-populated assets
}

export { type UploadedAsset };

export function AssetUploader({
  accept = 'image/*',
  maxSize = 50 * 1024 * 1024, // 50MB default for images
  maxFiles = 1,
  multiple = false,
  onUploadComplete,
  onUploadError,
  onFilesSelected,
  className,
  existingAssets = [],
}: AssetUploaderProps) {
  const [assets, setAssets] = useState<UploadedAsset[]>(existingAssets);
  const [uploadsList, setUploadsList] = useState<UploadState[]>([]);

  const { uploadMultiple, cancelUpload, uploads } = useFileUpload();

  // Convert uploads Map to array for rendering
  useEffect(() => {
    setUploadsList(Array.from(uploads.values()));
  }, [uploads]);

  const handleFilesSelected = async (files: FileList | File[]) => {
    const fileArray = Array.from(files);

    // Validate files
    const validationResults = fileArray.map((file) =>
      validateFile(file, { accept, maxSize })
    );

    const validFiles = fileArray.filter((_, i) => validationResults[i].valid);
    const invalidFiles = fileArray.filter((_, i) => !validationResults[i].valid);

    // Show errors for invalid files
    invalidFiles.forEach((file) => {
      const result = validationResults[fileArray.indexOf(file)];
      onUploadError?.(new Error(result.error || 'Invalid file'));
    });

    // Enforce max files limit
    const filesToUpload = validFiles.slice(0, maxFiles - assets.length);

    if (filesToUpload.length === 0) return;

    onFilesSelected?.(filesToUpload);

    // Upload files
    try {
      const uploadedAssets = await uploadMultiple(filesToUpload, {
        onProgress: (progress, fileId) => {
          // Progress is handled by the hook's internal state
          console.log(`Upload ${fileId} progress: ${progress}%`);
        },
      });

      setAssets((prev) => [...prev, ...uploadedAssets]);
      onUploadComplete?.(uploadedAssets);
    } catch (error) {
      onUploadError?.(error as Error);
    }
  };

  const handleRemoveAsset = (assetId: string) => {
    setAssets((prev) => prev.filter((asset) => asset.id !== assetId));
  };

  return (
    <div className={`asset-uploader ${className || ''}`}>
      {/* Drag-and-drop zone */}
      {assets.length < maxFiles && (
        <DropZone
          accept={accept}
          maxSize={maxSize}
          multiple={multiple && assets.length < maxFiles}
          onFilesSelected={handleFilesSelected}
        />
      )}

      {/* Upload progress list */}
      {uploadsList.length > 0 && (
        <div className="asset-uploader__progress-list">
          {uploadsList.map((upload) => (
            <UploadProgress
              key={upload.id}
              upload={upload}
              onCancel={() => cancelUpload(upload.id)}
            />
          ))}
        </div>
      )}

      {/* Asset gallery */}
      {assets.length > 0 && (
        <div className="asset-uploader__gallery">
          {assets.map((asset) => (
            <FilePreview
              key={asset.id}
              asset={asset}
              onRemove={() => handleRemoveAsset(asset.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
