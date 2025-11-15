# PR-F012: Asset Upload Manager Implementation Plan

## Overview
Build a drag-and-drop file upload component for brand assets (logos, product images) and audio files with validation, progress tracking, and preview features.

**Estimated Time:** 3 hours  
**Dependencies:** PR-F002 ✅, PR-F003 ✅  
**Priority:** MEDIUM - Blocks PR-F007 (Generation Form)

## Goals
- Create intuitive drag-and-drop upload interface
- Validate files before upload (type, size, dimensions)
- Track upload progress for each file
- Display previews for images and audio
- Handle multiple files efficiently
- Provide clear error messages for validation failures

---

## Files to Create

### 1. `/home/user/delicious-lotus/frontend/src/components/AssetUploader/AssetUploader.tsx`
**Purpose:** Main upload component with drag-and-drop

**Component Interface:**
```typescript
export interface AssetUploaderProps {
  accept?: string;                    // File types: 'image/*', 'audio/*'
  maxSize?: number;                   // Max file size in bytes (default: 50MB images, 100MB audio)
  maxFiles?: number;                  // Max number of files (default: 1)
  multiple?: boolean;                 // Allow multiple files
  onUploadComplete?: (assets: UploadedAsset[]) => void;
  onUploadError?: (error: Error) => void;
  onFilesSelected?: (files: File[]) => void;
  className?: string;
  existingAssets?: UploadedAsset[];  // Pre-populated assets
}

export interface UploadedAsset {
  id: string;
  url: string;
  filename: string;
  size: number;
  type: string;
  thumbnail?: string;
  metadata?: Record<string, any>;
}

export function AssetUploader({
  accept = 'image/*',
  maxSize = 50 * 1024 * 1024,  // 50MB default for images
  maxFiles = 1,
  multiple = false,
  onUploadComplete,
  onUploadError,
  onFilesSelected,
  className,
  existingAssets = [],
}: AssetUploaderProps): JSX.Element {
  const [uploads, setUploads] = useState<UploadState[]>([]);
  const [assets, setAssets] = useState<UploadedAsset[]>(existingAssets);
  
  const {
    uploadFile,
    uploadMultiple,
    cancelUpload,
  } = useFileUpload();
  
  const handleFilesSelected = async (files: FileList | File[]) => {
    const fileArray = Array.from(files);
    
    // Validate files
    const validationResults = fileArray.map(file => 
      validateFile(file, { accept, maxSize })
    );
    
    const validFiles = fileArray.filter((_, i) => validationResults[i].valid);
    const invalidFiles = fileArray.filter((_, i) => !validationResults[i].valid);
    
    // Show errors for invalid files
    invalidFiles.forEach((file, i) => {
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
          setUploads(prev => prev.map(u => 
            u.id === fileId ? { ...u, progress } : u
          ));
        },
      });
      
      setAssets(prev => [...prev, ...uploadedAssets]);
      onUploadComplete?.(uploadedAssets);
      
    } catch (error) {
      onUploadError?.(error as Error);
    }
  };
  
  return (
    <div className={`asset-uploader ${className}`}>
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
      {uploads.length > 0 && (
        <div className="asset-uploader__progress-list">
          {uploads.map(upload => (
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
          {assets.map(asset => (
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
```

**Features:**
- Drag-and-drop zone when under max files
- Upload progress tracking
- Asset gallery for uploaded files
- File validation before upload
- Error handling and display

---

### 2. `/home/user/delicious-lotus/frontend/src/components/AssetUploader/DropZone.tsx`
**Purpose:** Drag-and-drop zone component

**Component Interface:**
```typescript
interface DropZoneProps {
  accept: string;
  maxSize: number;
  multiple: boolean;
  onFilesSelected: (files: FileList | File[]) => void;
  disabled?: boolean;
}

export function DropZone({
  accept,
  maxSize,
  multiple,
  onFilesSelected,
  disabled = false,
}: DropZoneProps): JSX.Element {
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
      className={`drop-zone ${isDragging ? 'drop-zone--dragging' : ''} ${disabled ? 'drop-zone--disabled' : ''}`}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={handleClick}
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label="Upload files"
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

function formatAcceptedTypes(accept: string): string {
  if (accept === 'image/*') return 'JPEG, PNG';
  if (accept === 'audio/*') return 'MP3, WAV';
  if (accept.includes('image') && accept.includes('audio')) return 'Images, Audio';
  return accept;
}
```

**Features:**
- Drag-and-drop interaction
- Click to browse fallback
- Visual feedback on drag over
- Disabled state
- Hidden file input
- Keyboard accessible

**Styling:**
```css
.drop-zone {
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-2xl);
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--color-surface);
}

.drop-zone:hover:not(.drop-zone--disabled) {
  border-color: var(--color-primary);
  background: var(--color-surface-hover);
}

.drop-zone--dragging {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

.drop-zone--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.drop-zone__input {
  display: none;
}

.drop-zone__icon {
  width: 48px;
  height: 48px;
  color: var(--color-text-secondary);
  margin: 0 auto var(--spacing-md);
}

.drop-zone__text {
  font-size: 16px;
  margin: 0 0 var(--spacing-sm);
  color: var(--color-text);
}

.drop-zone__hint {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}
```

---

### 3. `/home/user/delicious-lotus/frontend/src/components/AssetUploader/FilePreview.tsx`
**Purpose:** Preview component for uploaded files

**Component Interface:**
```typescript
interface FilePreviewProps {
  asset: UploadedAsset;
  onRemove: () => void;
  onClick?: () => void;
}

export function FilePreview({
  asset,
  onRemove,
  onClick,
}: FilePreviewProps): JSX.Element {
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
            <audio
              src={asset.url}
              controls
              className="file-preview__audio-player"
            />
          </div>
        )}
      </div>
      
      {/* File info */}
      <div className="file-preview__info">
        <p className="file-preview__filename" title={asset.filename}>
          {truncateFilename(asset.filename, 20)}
        </p>
        <p className="file-preview__size">
          {formatFileSize(asset.size)}
        </p>
        {asset.metadata?.dimensions && (
          <p className="file-preview__dimensions">
            {asset.metadata.dimensions.width} × {asset.metadata.dimensions.height}
          </p>
        )}
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

function truncateFilename(filename: string, maxLength: number): string {
  if (filename.length <= maxLength) return filename;
  
  const ext = filename.split('.').pop() || '';
  const name = filename.slice(0, filename.length - ext.length - 1);
  const truncated = name.slice(0, maxLength - ext.length - 4);
  return `${truncated}...${ext}`;
}
```

**Features:**
- Image preview with thumbnail
- Audio player with controls
- File metadata (name, size, dimensions)
- Remove button
- Click to enlarge/play
- Truncated filename with tooltip

**Styling:**
```css
.file-preview {
  position: relative;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  background: var(--color-surface);
}

.file-preview__content {
  margin-bottom: var(--spacing-sm);
}

.file-preview__image {
  width: 100%;
  height: 150px;
  object-fit: cover;
  border-radius: var(--radius-sm);
}

.file-preview__audio {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
}

.file-preview__audio-icon {
  width: 48px;
  height: 48px;
  color: var(--color-primary);
}

.file-preview__audio-player {
  width: 100%;
}

.file-preview__info {
  margin-bottom: var(--spacing-sm);
}

.file-preview__filename {
  font-size: 14px;
  font-weight: 500;
  margin: 0 0 4px;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-preview__size,
.file-preview__dimensions {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin: 0;
}

.file-preview__remove {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  border: none;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.file-preview__remove:hover {
  background: rgba(0, 0, 0, 0.8);
}
```

---

### 4. `/home/user/delicious-lotus/frontend/src/components/AssetUploader/UploadProgress.tsx`
**Purpose:** Upload progress indicator

**Component Interface:**
```typescript
interface UploadProgressProps {
  upload: UploadState;
  onCancel: () => void;
}

export interface UploadState {
  id: string;
  file: File;
  progress: number;      // 0-100
  status: 'uploading' | 'success' | 'error';
  error?: string;
}

export function UploadProgress({
  upload,
  onCancel,
}: UploadProgressProps): JSX.Element {
  const isUploading = upload.status === 'uploading';
  const isSuccess = upload.status === 'success';
  const isError = upload.status === 'error';
  
  return (
    <div className="upload-progress">
      <div className="upload-progress__info">
        <p className="upload-progress__filename">
          {upload.file.name}
        </p>
        <p className="upload-progress__size">
          {formatFileSize(upload.file.size)}
        </p>
      </div>
      
      <div className="upload-progress__bar-container">
        <div
          className={`upload-progress__bar ${
            isSuccess ? 'upload-progress__bar--success' :
            isError ? 'upload-progress__bar--error' : ''
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
```

**Features:**
- Progress bar (0-100%)
- File name and size
- Cancel button during upload
- Success/error states
- Percentage display

---

### 5. `/home/user/delicious-lotus/frontend/src/hooks/useFileUpload.ts`
**Purpose:** File upload state management and API integration

**Hook Interface:**
```typescript
export interface UseFileUploadReturn {
  uploadFile: (
    file: File,
    options?: UploadOptions
  ) => Promise<UploadedAsset>;
  
  uploadMultiple: (
    files: File[],
    options?: UploadOptions
  ) => Promise<UploadedAsset[]>;
  
  cancelUpload: (uploadId: string) => void;
  
  uploads: Map<string, UploadState>;
}

export interface UploadOptions {
  onProgress?: (progress: number, uploadId: string) => void;
  onSuccess?: (asset: UploadedAsset, uploadId: string) => void;
  onError?: (error: Error, uploadId: string) => void;
}

export function useFileUpload(): UseFileUploadReturn {
  const [uploads, setUploads] = useState<Map<string, UploadState>>(new Map());
  const abortControllers = useRef<Map<string, AbortController>>(new Map());
  
  const uploadFile = useCallback(async (
    file: File,
    options?: UploadOptions
  ): Promise<UploadedAsset> => {
    const uploadId = generateId();
    const abortController = new AbortController();
    abortControllers.current.set(uploadId, abortController);
    
    // Initialize upload state
    setUploads(prev => new Map(prev).set(uploadId, {
      id: uploadId,
      file,
      progress: 0,
      status: 'uploading',
    }));
    
    try {
      // Create FormData
      const formData = new FormData();
      formData.append('file', file);
      
      // Upload with progress tracking
      const asset = await assetsService.uploadAsset(formData, {
        signal: abortController.signal,
        onUploadProgress: (progressEvent) => {
          const progress = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 100)
          );
          
          setUploads(prev => new Map(prev).set(uploadId, {
            ...prev.get(uploadId)!,
            progress,
          }));
          
          options?.onProgress?.(progress, uploadId);
        },
      });
      
      // Update to success state
      setUploads(prev => new Map(prev).set(uploadId, {
        ...prev.get(uploadId)!,
        progress: 100,
        status: 'success',
      }));
      
      options?.onSuccess?.(asset, uploadId);
      
      // Clean up after 2 seconds
      setTimeout(() => {
        setUploads(prev => {
          const next = new Map(prev);
          next.delete(uploadId);
          return next;
        });
        abortControllers.current.delete(uploadId);
      }, 2000);
      
      return asset;
      
    } catch (error) {
      // Update to error state
      setUploads(prev => new Map(prev).set(uploadId, {
        ...prev.get(uploadId)!,
        status: 'error',
        error: (error as Error).message,
      }));
      
      options?.onError?.(error as Error, uploadId);
      
      throw error;
    }
  }, []);
  
  const uploadMultiple = useCallback(async (
    files: File[],
    options?: UploadOptions
  ): Promise<UploadedAsset[]> => {
    const promises = files.map(file => uploadFile(file, options));
    return Promise.all(promises);
  }, [uploadFile]);
  
  const cancelUpload = useCallback((uploadId: string) => {
    const controller = abortControllers.current.get(uploadId);
    if (controller) {
      controller.abort();
      abortControllers.current.delete(uploadId);
    }
    
    setUploads(prev => {
      const next = new Map(prev);
      next.delete(uploadId);
      return next;
    });
  }, []);
  
  return {
    uploadFile,
    uploadMultiple,
    cancelUpload,
    uploads,
  };
}
```

**Features:**
- Upload single or multiple files
- Track progress for each upload
- Cancel uploads
- Handle errors
- Clean up completed uploads
- Integrate with assetsService from API client

---

### 6. `/home/user/delicious-lotus/frontend/src/utils/fileValidation.ts`
**Purpose:** File validation utilities

**Functions:**
```typescript
export interface ValidationResult {
  valid: boolean;
  error?: string;
}

export interface ValidationOptions {
  accept?: string;
  maxSize?: number;
  minDimensions?: { width: number; height: number };
  maxDimensions?: { width: number; height: number };
  maxDuration?: number;  // For audio/video
}

/**
 * Validate file type, size, and other constraints
 */
export function validateFile(
  file: File,
  options: ValidationOptions
): ValidationResult {
  // Check file type
  if (options.accept) {
    const accepted = isAcceptedType(file.type, options.accept);
    if (!accepted) {
      return {
        valid: false,
        error: `File type not accepted. Expected: ${options.accept}`,
      };
    }
  }
  
  // Check file size
  if (options.maxSize && file.size > options.maxSize) {
    return {
      valid: false,
      error: `File too large. Max size: ${formatFileSize(options.maxSize)}`,
    };
  }
  
  return { valid: true };
}

/**
 * Check if file type matches accept string
 */
function isAcceptedType(fileType: string, accept: string): boolean {
  const acceptTypes = accept.split(',').map(t => t.trim());
  
  return acceptTypes.some(acceptType => {
    if (acceptType.endsWith('/*')) {
      const category = acceptType.replace('/*', '');
      return fileType.startsWith(category + '/');
    }
    return fileType === acceptType;
  });
}

/**
 * Validate image dimensions
 */
export async function validateImageDimensions(
  file: File,
  options: {
    minDimensions?: { width: number; height: number };
    maxDimensions?: { width: number; height: number };
  }
): Promise<ValidationResult> {
  try {
    const dimensions = await getImageDimensions(file);
    
    if (options.minDimensions) {
      if (
        dimensions.width < options.minDimensions.width ||
        dimensions.height < options.minDimensions.height
      ) {
        return {
          valid: false,
          error: `Image too small. Min: ${options.minDimensions.width}×${options.minDimensions.height}`,
        };
      }
    }
    
    if (options.maxDimensions) {
      if (
        dimensions.width > options.maxDimensions.width ||
        dimensions.height > options.maxDimensions.height
      ) {
        return {
          valid: false,
          error: `Image too large. Max: ${options.maxDimensions.width}×${options.maxDimensions.height}`,
        };
      }
    }
    
    return { valid: true };
    
  } catch (error) {
    return {
      valid: false,
      error: 'Failed to read image dimensions',
    };
  }
}

/**
 * Get image dimensions
 */
function getImageDimensions(file: File): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    
    img.onload = () => {
      URL.revokeObjectURL(url);
      resolve({
        width: img.naturalWidth,
        height: img.naturalHeight,
      });
    };
    
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('Failed to load image'));
    };
    
    img.src = url;
  });
}

/**
 * Validate audio duration
 */
export async function validateAudioDuration(
  file: File,
  maxDuration: number
): Promise<ValidationResult> {
  try {
    const duration = await getAudioDuration(file);
    
    if (duration > maxDuration) {
      return {
        valid: false,
        error: `Audio too long. Max: ${maxDuration}s`,
      };
    }
    
    return { valid: true };
    
  } catch (error) {
    return {
      valid: false,
      error: 'Failed to read audio duration',
    };
  }
}

/**
 * Get audio duration
 */
function getAudioDuration(file: File): Promise<number> {
  return new Promise((resolve, reject) => {
    const audio = new Audio();
    const url = URL.createObjectURL(file);
    
    audio.onloadedmetadata = () => {
      URL.revokeObjectURL(url);
      resolve(audio.duration);
    };
    
    audio.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('Failed to load audio'));
    };
    
    audio.src = url;
  });
}

/**
 * Generate thumbnail from image file
 */
export async function generateImageThumbnail(
  file: File,
  maxSize: number = 200
): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    
    img.onload = () => {
      URL.revokeObjectURL(url);
      
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      if (!ctx) {
        reject(new Error('Canvas context not available'));
        return;
      }
      
      const scale = Math.min(
        maxSize / img.width,
        maxSize / img.height,
        1
      );
      
      canvas.width = img.width * scale;
      canvas.height = img.height * scale;
      
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      
      canvas.toBlob(
        (blob) => {
          if (blob) {
            resolve(URL.createObjectURL(blob));
          } else {
            reject(new Error('Failed to create thumbnail'));
          }
        },
        'image/jpeg',
        0.8
      );
    };
    
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('Failed to load image'));
    };
    
    img.src = url;
  });
}
```

---

## Files to Modify

### 1. `/home/user/delicious-lotus/frontend/src/api/services/assets.ts`
**Changes:** Ensure uploadAsset method supports progress tracking

**Expected Method:**
```typescript
export class AssetsService {
  static async uploadAsset(
    formData: FormData,
    options?: {
      signal?: AbortSignal;
      onUploadProgress?: (progressEvent: ProgressEvent) => void;
    }
  ): Promise<UploadedAsset> {
    // Implementation with XMLHttpRequest for progress tracking
    // Or use axios which supports onUploadProgress natively
  }
}
```

---

## Dependencies

### NPM Packages
None - using native browser APIs

### Internal Dependencies
- `/frontend/src/api/services/assets.ts` - Asset upload API
- `/frontend/src/api/client.ts` - API client
- `/frontend/src/components/ui/Button.tsx` - Design system button
- `/frontend/src/components/ui/Spinner.tsx` - Design system spinner
- `/frontend/src/utils/errors.ts` - Error handling
- `/frontend/src/utils/video.ts` - formatFileSize function

### Icons
- Upload icon (⬆)
- Audio icon (🎵)
- Close/Remove icon (✕)
- Check icon (✓)
- Error icon (⚠)

---

## API Integration

### Upload Asset Endpoint
**POST** `/api/v1/assets/upload`

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with `file` field

**Response (201 Created):**
```json
{
  "asset_id": "asset_abc123",
  "url": "https://storage.example.com/assets/asset_abc123.jpg",
  "thumbnail_url": "https://storage.example.com/thumbnails/asset_abc123.jpg",
  "filename": "logo.jpg",
  "size": 245760,
  "type": "image/jpeg",
  "metadata": {
    "dimensions": {
      "width": 1920,
      "height": 1080
    }
  }
}
```

**Error Responses:**
- 400: Invalid file type or size
- 413: File too large
- 500: Upload failed

---

## Implementation Details

### Step 1: Create Validation Utilities (30 minutes)
1. Create `utils/fileValidation.ts`
2. Implement validateFile()
3. Implement validateImageDimensions()
4. Implement validateAudioDuration()
5. Implement thumbnail generation
6. Add tests for validation functions

### Step 2: Build Upload Hook (45 minutes)
1. Create `hooks/useFileUpload.ts`
2. Implement uploadFile() with progress tracking
3. Implement uploadMultiple()
4. Add cancel functionality
5. Handle errors and retries
6. Clean up state after completion

### Step 3: Create DropZone Component (30 minutes)
1. Create `components/AssetUploader/DropZone.tsx`
2. Implement drag-and-drop handlers
3. Add click-to-browse functionality
4. Style drag states
5. Add accessibility attributes

### Step 4: Build FilePreview Component (30 minutes)
1. Create `components/AssetUploader/FilePreview.tsx`
2. Add image preview
3. Add audio player
4. Display file metadata
5. Add remove button
6. Style with grid layout

### Step 5: Create UploadProgress Component (20 minutes)
1. Create `components/AssetUploader/UploadProgress.tsx`
2. Build progress bar
3. Add cancel button
4. Show success/error states
5. Style with animations

### Step 6: Build Main AssetUploader Component (25 minutes)
1. Create `components/AssetUploader/AssetUploader.tsx`
2. Integrate all sub-components
3. Handle file selection
4. Manage upload state
5. Handle validation and errors

---

## State Management Approach

### Local Component State
- Upload progress: `Map<uploadId, UploadState>`
- Uploaded assets: `UploadedAsset[]`
- Drag state: `boolean`

### No Global State
- All state local to AssetUploader and child components
- Upload state managed in useFileUpload hook
- Asset list passed via props or lifted to parent

---

## Error Handling Strategy

### Validation Errors
1. **Invalid File Type:**
   - Show error toast
   - Highlight accepted types
   - Don't start upload

2. **File Too Large:**
   - Show error toast with max size
   - Don't start upload

3. **Invalid Dimensions:**
   - Show error with min/max dimensions
   - Don't start upload

4. **Invalid Duration:**
   - Show error with max duration
   - Don't start upload

### Upload Errors
1. **Network Error:**
   - Show error in progress bar
   - Allow retry
   - Keep file in list

2. **Server Error:**
   - Show error message from server
   - Allow retry
   - Log error for debugging

3. **Cancelled Upload:**
   - Remove from progress list
   - No error message
   - Clean up resources

---

## Acceptance Criteria

- [ ] Drag-and-drop upload zone:
  - [ ] Visual feedback on drag over
  - [ ] Click to browse files
  - [ ] Multiple file selection support (if enabled)
- [ ] File validation:
  - [ ] Image files: JPEG, PNG, max 50MB
  - [ ] Audio files: MP3, WAV, max 100MB
  - [ ] Minimum dimensions for images (512x512)
  - [ ] Maximum dimensions for images (4096x4096)
  - [ ] Audio duration validation (max 180s)
  - [ ] Error messages for invalid files
- [ ] Upload progress:
  - [ ] Individual progress bar per file (0-100%)
  - [ ] Percentage complete
  - [ ] Cancel upload button
  - [ ] Success/error states
- [ ] File preview:
  - [ ] Thumbnail for images
  - [ ] Audio player with controls
  - [ ] File name and size display
  - [ ] Remove button
- [ ] Asset gallery:
  - [ ] Grid of uploaded files
  - [ ] Click to enlarge/play
  - [ ] Delete confirmation dialog (optional)
- [ ] API Integration:
  - [ ] POST `/api/v1/assets/upload` with multipart/form-data
  - [ ] Handle upload progress events
  - [ ] Error handling for upload failures

---

## Testing Approach

### Unit Tests
1. **Validation Functions:**
   - Test validateFile() with various file types
   - Test size validation
   - Test dimension validation
   - Test duration validation

2. **useFileUpload Hook:**
   - Test single file upload
   - Test multiple file upload
   - Test cancel upload
   - Test error handling

### Component Tests
1. **DropZone:**
   - Test drag-and-drop
   - Test click-to-browse
   - Test file input change
   - Test disabled state

2. **FilePreview:**
   - Test image preview
   - Test audio preview
   - Test remove button
   - Test metadata display

3. **UploadProgress:**
   - Test progress bar updates
   - Test cancel button
   - Test success/error states

4. **AssetUploader:**
   - Test complete upload flow
   - Test validation
   - Test error handling
   - Test max files limit

### Integration Tests
1. **Upload Flow:**
   - Select files
   - Validate files
   - Upload files
   - Display preview
   - Remove files

2. **Error Scenarios:**
   - Invalid file type
   - File too large
   - Upload failure
   - Network error

### Manual Testing
1. **File Types:**
   - JPEG images
   - PNG images
   - MP3 audio
   - WAV audio
   - Invalid types

2. **File Sizes:**
   - Small files (< 1MB)
   - Medium files (1-10MB)
   - Large files (10-50MB)
   - Too large files (> 50MB)

3. **Multiple Files:**
   - Upload 1 file
   - Upload multiple files
   - Exceed max files limit

4. **Cancel:**
   - Cancel during upload
   - Verify resources cleaned up

---

## Responsive Design

### Desktop (≥ 1024px)
- Large drop zone (300px height)
- Grid layout for previews (3 columns)
- Hover effects

### Tablet (768px - 1023px)
- Medium drop zone (250px height)
- Grid layout (2 columns)

### Mobile (< 768px)
- Compact drop zone (200px height)
- Single column layout
- Touch-friendly buttons
- Native file picker (optional)

---

## Performance Considerations

1. **Large Files:**
   - Show progress bar
   - Use chunked upload (if backend supports)
   - Limit concurrent uploads (max 3)

2. **Thumbnails:**
   - Generate client-side for preview
   - Use backend thumbnails when available
   - Cache thumbnails

3. **Memory:**
   - Revoke object URLs when done
   - Clean up event listeners
   - Limit file preview size

---

## Security Considerations

1. **File Validation:**
   - Validate on client AND server
   - Check MIME type and file extension
   - Scan for malware (server-side)

2. **File Size:**
   - Enforce size limits
   - Prevent DoS with large files

3. **File Content:**
   - Sanitize filenames
   - No executable files
   - Validate image dimensions

---

## Follow-up Tasks

1. **PR-F007:** Use AssetUploader in Generation Form (logo upload)
2. **PR-F017:** Use AssetUploader for audio files (Music Video)
3. **Enhancement:** Add drag-and-drop reordering
4. **Enhancement:** Add image cropping/editing
5. **Enhancement:** Add batch operations

---

## Success Criteria

This PR is successful when:
1. Drag-and-drop works smoothly
2. File validation prevents invalid uploads
3. Upload progress updates in real-time
4. Previews display correctly
5. Files can be removed
6. Errors are handled gracefully
7. Mobile responsive
8. Accessible with keyboard and screen reader
9. All acceptance criteria met
10. Code passes TypeScript strict mode
