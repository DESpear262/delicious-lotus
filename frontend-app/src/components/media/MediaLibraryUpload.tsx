/**
 * Media Library Upload
 * Complete upload interface with drag-and-drop, queue management, and progress tracking
 */

import { MediaUpload } from './MediaUpload'
import { UploadQueue } from './UploadProgress'
import { useUpload } from '../../hooks/useUpload'

export function MediaLibraryUpload() {
  const {
    uploadFiles,
    cancelUpload,
    retryUpload,
    removeUpload,
    clearCompleted,
    uploads,
    uploadSpeeds,
  } = useUpload()

  const handleFilesSelected = async (files: File[]) => {
    await uploadFiles(files)
  }

  return (
    <div className="space-y-4">
      {/* Upload drop zone */}
      <MediaUpload onFilesSelected={handleFilesSelected} />

      {/* Upload queue with progress tracking */}
      {uploads.length > 0 && (
        <UploadQueue
          uploads={uploads}
          onCancel={cancelUpload}
          onRetry={retryUpload}
          onRemove={removeUpload}
          onClearCompleted={clearCompleted}
          uploadSpeeds={uploadSpeeds}
        />
      )}
    </div>
  )
}
