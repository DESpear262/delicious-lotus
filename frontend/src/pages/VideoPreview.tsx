/**
 * Video Preview & Download Page
 * Displays completed video with metadata and action buttons
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { VideoPlayer } from '@/components/VideoPlayer';
import { VideoActions } from '@/components/VideoActions';
import { Card, CardHeader, CardBody } from '@/components/ui/Card';
import { Spinner } from '@/components/ui/Spinner';
import { getGeneration, getGenerationAssets } from '@/api/services/generation';
import {
  getComposition,
  getCompositionMetadata,
} from '@/api/services/composition';
import { formatTime, formatFileSize } from '@/utils/video';
import type {
  GetGenerationResponse,
  GetAssetsResponse,
  GetCompositionResponse,
  GetCompositionMetadataResponse,
} from '@/api/types';
import styles from './VideoPreview.module.css';

export function VideoPreview() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // State
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generation, setGeneration] = useState<GetGenerationResponse | null>(
    null
  );
  const [assets, setAssets] = useState<GetAssetsResponse | null>(null);
  const [composition, setComposition] = useState<GetCompositionResponse | null>(
    null
  );
  const [metadata, setMetadata] =
    useState<GetCompositionMetadataResponse | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  // Fetch data on mount
  useEffect(() => {
    const fetchData = async () => {
      if (!id) {
        setError('No generation ID provided');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);

        // Fetch generation data
        const generationData = await getGeneration(id);
        setGeneration(generationData);

        // Fetch assets
        const assetsData = await getGenerationAssets(id);
        setAssets(assetsData);

        // If there's a composition, fetch it
        // Note: We assume the composition ID is the same as generation ID for now
        // In a real app, you'd get the composition ID from the generation data
        try {
          const compositionData = await getComposition(id);
          setComposition(compositionData);

          // Fetch composition metadata
          const metadataData = await getCompositionMetadata(id);
          setMetadata(metadataData);
        } catch (compositionError) {
          // Composition might not exist yet, that's okay
          console.warn('No composition found:', compositionError);
        }

        setIsLoading(false);
      } catch (err) {
        console.error('Failed to fetch video data:', err);
        setError(
          err instanceof Error ? err.message : 'Failed to load video data'
        );
        setIsLoading(false);
      }
    };

    fetchData();
  }, [id]);

  // Get video URL (prefer composition output, fallback to first asset)
  const videoUrl =
    composition?.output?.url ||
    assets?.assets?.clips?.[0]?.url ||
    null;

  const posterUrl =
    generation?.clips_generated?.[0]?.thumbnail_url ||
    assets?.assets?.clips?.[0]?.thumbnail_url ||
    undefined;

  // Handle download success
  const handleDownloadSuccess = () => {
    setShowSuccess(true);
    setDownloadError(null);
    setTimeout(() => setShowSuccess(false), 3000);
  };

  // Handle download error
  const handleDownloadError = (error: Error) => {
    setDownloadError(error.message);
    setTimeout(() => setDownloadError(null), 5000);
  };

  // Format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Loading state
  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <Spinner size="lg" label="Loading video..." />
      </div>
    );
  }

  // Error state
  if (error || !generation) {
    return (
      <div className={styles.errorContainer}>
        <h1 className={styles.errorTitle}>Failed to Load Video</h1>
        <p className={styles.errorMessage}>{error || 'Video not found'}</p>
        <button
          className={styles.backButton}
          onClick={() => navigate('/history')}
        >
          Return to History
        </button>
      </div>
    );
  }

  // No video URL available
  if (!videoUrl) {
    return (
      <div className={styles.errorContainer}>
        <h1 className={styles.errorTitle}>Video Not Ready</h1>
        <p className={styles.errorMessage}>
          This video is still being processed. Please check back later.
        </p>
        <button
          className={styles.backButton}
          onClick={() => navigate('/history')}
        >
          Return to History
        </button>
      </div>
    );
  }

  return (
    <div className={styles.videoPreview}>
      {/* Success/Error Notifications */}
      {showSuccess && (
        <div className={styles.notification} data-type="success">
          Video downloaded successfully!
        </div>
      )}
      {downloadError && (
        <div className={styles.notification} data-type="error">
          Download failed: {downloadError}
        </div>
      )}

      {/* Page Header */}
      <div className={styles.header}>
        <h1 className={styles.title}>Video Preview</h1>
        <p className={styles.subtitle}>
          Generation ID: <code className={styles.code}>{id}</code>
        </p>
      </div>

      {/* Main Content */}
      <div className={styles.content}>
        {/* Video Player Section */}
        <div className={styles.playerSection}>
          <VideoPlayer
            src={videoUrl}
            poster={posterUrl}
            title={generation.metadata.prompt}
            className={styles.player}
            showDownload={false} // We have our own download button
          />
        </div>

        {/* Actions Section */}
        <div className={styles.actionsSection}>
          <VideoActions
            compositionId={id || ''}
            generationId={id || ''}
            filename={`video_${id}.mp4`}
            generationParameters={generation.metadata.parameters}
            onDownloadSuccess={handleDownloadSuccess}
            onDownloadError={handleDownloadError}
          />
        </div>

        {/* Metadata Section */}
        <div className={styles.metadataSection}>
          <Card variant="bordered">
            <CardHeader title="Video Information" />
            <CardBody>
              <dl className={styles.metadataList}>
                <div className={styles.metadataItem}>
                  <dt className={styles.metadataLabel}>Duration</dt>
                  <dd className={styles.metadataValue}>
                    {metadata?.file_info?.duration_seconds
                      ? formatTime(metadata.file_info.duration_seconds)
                      : composition?.output?.duration
                        ? formatTime(composition.output.duration)
                        : 'N/A'}
                  </dd>
                </div>

                <div className={styles.metadataItem}>
                  <dt className={styles.metadataLabel}>Resolution</dt>
                  <dd className={styles.metadataValue}>
                    {metadata?.file_info?.resolution ||
                      generation.metadata.parameters.aspect_ratio}
                  </dd>
                </div>

                <div className={styles.metadataItem}>
                  <dt className={styles.metadataLabel}>File Size</dt>
                  <dd className={styles.metadataValue}>
                    {metadata?.file_info?.size_bytes
                      ? formatFileSize(metadata.file_info.size_bytes)
                      : composition?.output?.size_bytes
                        ? formatFileSize(composition.output.size_bytes)
                        : 'N/A'}
                  </dd>
                </div>

                <div className={styles.metadataItem}>
                  <dt className={styles.metadataLabel}>Created</dt>
                  <dd className={styles.metadataValue}>
                    {formatDate(generation.metadata.created_at)}
                  </dd>
                </div>

                {metadata?.file_info?.codec && (
                  <div className={styles.metadataItem}>
                    <dt className={styles.metadataLabel}>Codec</dt>
                    <dd className={styles.metadataValue}>
                      {metadata.file_info.codec}
                    </dd>
                  </div>
                )}

                {metadata?.file_info?.fps && (
                  <div className={styles.metadataItem}>
                    <dt className={styles.metadataLabel}>Frame Rate</dt>
                    <dd className={styles.metadataValue}>
                      {metadata.file_info.fps} fps
                    </dd>
                  </div>
                )}
              </dl>
            </CardBody>
          </Card>
        </div>

        {/* Generation Parameters Section */}
        <div className={styles.parametersSection}>
          <Card variant="bordered">
            <CardHeader title="Generation Parameters" />
            <CardBody>
              <div className={styles.promptSection}>
                <h4 className={styles.promptLabel}>Original Prompt</h4>
                <p className={styles.promptText}>{generation.metadata.prompt}</p>
              </div>

              <dl className={styles.parametersList}>
                <div className={styles.parameterItem}>
                  <dt className={styles.parameterLabel}>Duration</dt>
                  <dd className={styles.parameterValue}>
                    {generation.metadata.parameters.duration_seconds} seconds
                  </dd>
                </div>

                <div className={styles.parameterItem}>
                  <dt className={styles.parameterLabel}>Aspect Ratio</dt>
                  <dd className={styles.parameterValue}>
                    {generation.metadata.parameters.aspect_ratio}
                  </dd>
                </div>

                <div className={styles.parameterItem}>
                  <dt className={styles.parameterLabel}>Style</dt>
                  <dd className={styles.parameterValue}>
                    {generation.metadata.parameters.style}
                  </dd>
                </div>

                {generation.metadata.parameters.brand && (
                  <div className={styles.parameterItem}>
                    <dt className={styles.parameterLabel}>Brand</dt>
                    <dd className={styles.parameterValue}>
                      {generation.metadata.parameters.brand.name}
                    </dd>
                  </div>
                )}

                {generation.metadata.parameters.music_style && (
                  <div className={styles.parameterItem}>
                    <dt className={styles.parameterLabel}>Music Style</dt>
                    <dd className={styles.parameterValue}>
                      {generation.metadata.parameters.music_style}
                    </dd>
                  </div>
                )}

                {generation.metadata.parameters.include_cta && (
                  <div className={styles.parameterItem}>
                    <dt className={styles.parameterLabel}>Call to Action</dt>
                    <dd className={styles.parameterValue}>
                      {generation.metadata.parameters.cta_text || 'Enabled'}
                    </dd>
                  </div>
                )}
              </dl>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}
