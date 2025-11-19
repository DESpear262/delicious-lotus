/**
 * Video Preview & Download Page
 * Displays completed video with metadata and action buttons
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ROUTES } from '../../types/routes';
import { VideoPlayer } from '@/components/ad-generator/VideoPlayer';
import { VideoActions } from '@/components/ad-generator/VideoActions';
import { Card, CardHeader, CardBody } from '@/components/ad-generator/ui/Card';
import { Spinner } from '@/components/ad-generator/ui/Spinner';
import { getGeneration, getGenerationAssets } from '@/services/ad-generator/services/generation';
import {
  getComposition,
  getCompositionMetadata,
} from '@/services/ad-generator/services/composition';
import { formatTime, formatFileSize } from '@/utils/ad-generator/video';
import type {
  GetGenerationResponse,
  GetAssetsResponse,
  GetCompositionResponse,
  GetCompositionMetadataResponse,
} from '@/services/ad-generator/types';

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
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-6 p-8">
        <Spinner size="lg" label="Loading video..." />
      </div>
    );
  }

  // Error state
  if (error || !generation) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-6 p-8">
        <h1 className="text-2xl font-bold text-foreground m-0">Failed to Load Video</h1>
        <p className="text-lg text-muted-foreground text-center max-w-xl m-0">{error || 'Video not found'}</p>
        <button
          className="px-6 py-3 text-base font-medium text-primary-foreground bg-primary rounded-md hover:bg-primary/90 transition-all hover:-translate-y-0.5 hover:shadow-md active:translate-y-0"
          onClick={() => navigate(`${ROUTES.AD_GENERATOR}/history`)}
        >
          Return to History
        </button>
      </div>
    );
  }

  // No video URL available
  if (!videoUrl) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-6 p-8">
        <h1 className="text-2xl font-bold text-foreground m-0">Video Not Ready</h1>
        <p className="text-lg text-muted-foreground text-center max-w-xl m-0">
          This video is still being processed. Please check back later.
        </p>
        <button
          className="px-6 py-3 text-base font-medium text-primary-foreground bg-primary rounded-md hover:bg-primary/90 transition-all hover:-translate-y-0.5 hover:shadow-md active:translate-y-0"
          onClick={() => navigate(`${ROUTES.AD_GENERATOR}/history`)}
        >
          Return to History
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-full p-8 max-w-[1400px] mx-auto md:p-4">
      {/* Success/Error Notifications */}
      {showSuccess && (
        <div className="fixed top-8 right-8 px-6 py-3 rounded-md font-medium shadow-lg z-50 animate-in slide-in-from-right bg-green-500 text-white md:top-4 md:right-4 md:left-4">
          Video downloaded successfully!
        </div>
      )}
      {downloadError && (
        <div className="fixed top-8 right-8 px-6 py-3 rounded-md font-medium shadow-lg z-50 animate-in slide-in-from-right bg-red-500 text-white md:top-4 md:right-4 md:left-4">
          Download failed: {downloadError}
        </div>
      )}

      {/* Page Header */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-foreground mb-2 md:text-2xl">Video Preview</h1>
        <p className="text-base text-muted-foreground md:text-sm">
          Generation ID: <code className="bg-muted px-2 py-1 rounded text-sm font-mono text-primary">{id}</code>
        </p>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 gap-8 md:grid-cols-[2fr_1fr] md:gap-4">
        {/* Video Player Section */}
        <div className="col-span-full">
          <VideoPlayer
            src={videoUrl}
            poster={posterUrl}
            title={generation.metadata.prompt}
            className="w-full max-w-6xl mx-auto rounded-lg overflow-hidden shadow-lg"
            showDownload={false} // We have our own download button
          />
        </div>

        {/* Actions Section */}
        <div className="col-span-full max-w-2xl mx-auto w-full">
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
        <div className="col-span-full">
          <Card variant="bordered">
            <CardHeader title="Video Information" />
            <CardBody>
              <dl className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-6 m-0 lg:grid-cols-3 md:grid-cols-1">
                <div className="flex flex-col gap-1">
                  <dt className="text-sm font-medium text-muted-foreground uppercase tracking-wide">Duration</dt>
                  <dd className="text-lg font-semibold text-foreground m-0">
                    {metadata?.file_info?.duration_seconds
                      ? formatTime(metadata.file_info.duration_seconds)
                      : composition?.output?.duration
                        ? formatTime(composition.output.duration)
                        : 'N/A'}
                  </dd>
                </div>

                <div className="flex flex-col gap-1">
                  <dt className="text-sm font-medium text-muted-foreground uppercase tracking-wide">Resolution</dt>
                  <dd className="text-lg font-semibold text-foreground m-0">
                    {metadata?.file_info?.resolution ||
                      generation.metadata.parameters.aspect_ratio}
                  </dd>
                </div>

                <div className="flex flex-col gap-1">
                  <dt className="text-sm font-medium text-muted-foreground uppercase tracking-wide">File Size</dt>
                  <dd className="text-lg font-semibold text-foreground m-0">
                    {metadata?.file_info?.size_bytes
                      ? formatFileSize(metadata.file_info.size_bytes)
                      : composition?.output?.size_bytes
                        ? formatFileSize(composition.output.size_bytes)
                        : 'N/A'}
                  </dd>
                </div>

                <div className="flex flex-col gap-1">
                  <dt className="text-sm font-medium text-muted-foreground uppercase tracking-wide">Created</dt>
                  <dd className="text-lg font-semibold text-foreground m-0">
                    {formatDate(generation.metadata.created_at)}
                  </dd>
                </div>

                {metadata?.file_info?.codec && (
                  <div className="flex flex-col gap-1">
                    <dt className="text-sm font-medium text-muted-foreground uppercase tracking-wide">Codec</dt>
                    <dd className="text-lg font-semibold text-foreground m-0">
                      {metadata.file_info.codec}
                    </dd>
                  </div>
                )}

                {metadata?.file_info?.fps && (
                  <div className="flex flex-col gap-1">
                    <dt className="text-sm font-medium text-muted-foreground uppercase tracking-wide">Frame Rate</dt>
                    <dd className="text-lg font-semibold text-foreground m-0">
                      {metadata.file_info.fps} fps
                    </dd>
                  </div>
                )}
              </dl>
            </CardBody>
          </Card>
        </div>

        {/* Generation Parameters Section */}
        <div className="col-span-full">
          <Card variant="bordered">
            <CardHeader title="Generation Parameters" />
            <CardBody>
              <div className="mb-6 pb-6 border-b border-border">
                <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-2">Original Prompt</h4>
                <p className="text-base text-foreground leading-relaxed m-0 p-4 bg-muted rounded-md border-l-4 border-primary">{generation.metadata.prompt}</p>
              </div>

              <dl className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-4 m-0 lg:grid-cols-3 md:grid-cols-1">
                <div className="flex flex-col gap-1">
                  <dt className="text-sm font-medium text-muted-foreground">Duration</dt>
                  <dd className="text-base text-foreground m-0">
                    {generation.metadata.parameters.duration_seconds} seconds
                  </dd>
                </div>

                <div className="flex flex-col gap-1">
                  <dt className="text-sm font-medium text-muted-foreground">Aspect Ratio</dt>
                  <dd className="text-base text-foreground m-0">
                    {generation.metadata.parameters.aspect_ratio}
                  </dd>
                </div>

                <div className="flex flex-col gap-1">
                  <dt className="text-sm font-medium text-muted-foreground">Style</dt>
                  <dd className="text-base text-foreground m-0">
                    {generation.metadata.parameters.style}
                  </dd>
                </div>

                {generation.metadata.parameters.brand && (
                  <div className="flex flex-col gap-1">
                    <dt className="text-sm font-medium text-muted-foreground">Brand</dt>
                    <dd className="text-base text-foreground m-0">
                      {generation.metadata.parameters.brand.name}
                    </dd>
                  </div>
                )}

                {generation.metadata.parameters.music_style && (
                  <div className="flex flex-col gap-1">
                    <dt className="text-sm font-medium text-muted-foreground">Music Style</dt>
                    <dd className="text-base text-foreground m-0">
                      {generation.metadata.parameters.music_style}
                    </dd>
                  </div>
                )}

                {generation.metadata.parameters.include_cta && (
                  <div className="flex flex-col gap-1">
                    <dt className="text-sm font-medium text-muted-foreground">Call to Action</dt>
                    <dd className="text-base text-foreground m-0">
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
