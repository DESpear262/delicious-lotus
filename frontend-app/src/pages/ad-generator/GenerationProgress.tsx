/**
 * GenerationProgress Page
 * Real-time progress tracking for video generation
 */

import React, { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ROUTES } from '../../types/routes';
import { useGenerationProgress } from '@/hooks/ad-generator/useGenerationProgress';
import { ProgressBar } from '@/components/ad-generator/Progress/ProgressBar';
import { StepIndicator } from '@/components/ad-generator/Progress/StepIndicator';
import type { Step, StepStatus } from '@/components/ad-generator/Progress/StepIndicator';
import { ClipPreview, ClipPreviewGrid } from '@/components/ad-generator/Progress/ClipPreview';
import { Card, CardHeader, CardBody } from '@/components/ad-generator/ui/Card';
import { Button } from '@/components/ad-generator/ui/Button';
import { Spinner } from '@/components/ad-generator/ui/Spinner';
import type { GenerationStatus } from '@/services/ad-generator/types';

/**
 * Map generation status to step states
 */
const getStepStatus = (
  stepIndex: number,
  currentStepName: string,
  generationStatus: GenerationStatus
): StepStatus => {
  const stepNames = [
    'validation',
    'analyzing',
    'planning',
    'decomposing',
    'micro',
    'building',
    'generation',
    'generating',
    'composition',
    'assembling',
    'rendering',
  ];

  const currentIndex = stepNames.findIndex((name) =>
    currentStepName.toLowerCase().includes(name)
  );

  if (generationStatus === 'failed' && stepIndex === currentIndex) {
    return 'error';
  }

  if (stepIndex < currentIndex) {
    return 'completed';
  }

  if (stepIndex === currentIndex) {
    return 'in_progress';
  }

  return 'pending';
};

/**
 * GenerationProgress page component
 */
export const GenerationProgress: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [showCancelDialog, setShowCancelDialog] = useState(false);

  // Generation progress hook
  const {
    status,
    progress,
    clips,
    error,
    isLoading,
    isConnected,
    isPolling,
    currentStep,
    estimatedTimeRemaining,
    cancel,
    retry,
  } = useGenerationProgress({
    generationId: id || '',
    autoStart: true,
    onComplete: () => {
      // Redirect to preview page on completion
      setTimeout(() => {
        navigate(`${ROUTES.AD_GENERATOR}/history`);
      }, 2000);
    },
    onError: (errorData) => {
      console.error('Generation error:', errorData);
    },
  });

  /**
   * Build steps array from current progress (matching CLI format)
   */
  const steps: Step[] = useMemo(() => {
    const baseSteps = [
      {
        id: 'validation',
        label: 'Step 1: Analyzing Prompt',
        description: 'Analyzing prompt and parameters...',
      },
      {
        id: 'planning',
        label: 'Step 2: Decomposing into Scenes',
        description: 'Planning scenes and structure...',
      },
      {
        id: 'micro_prompts',
        label: 'Step 3: Building Micro-Prompts',
        description: 'Creating detailed prompts for each scene...',
      },
      {
        id: 'generation',
        label: 'Step 4: Generating Videos',
        description: 'Generating video clips from prompts...',
        info:
          progress?.current_clip && progress?.total_clips
            ? `Clip ${progress.current_clip} of ${progress.total_clips}`
            : progress?.total_clips
              ? `${progress.total_clips} clips to generate`
              : undefined,
      },
      {
        id: 'composition',
        label: 'Step 5: Video Composition',
        description: 'Assembling final video from clips...',
      },
      {
        id: 'rendering',
        label: 'Step 6: Final Rendering',
        description: 'Rendering and encoding final video...',
      },
    ];

    return baseSteps.map((step, index) => {
      // Map step IDs to indices for status checking
      const stepIdToIndex: Record<string, number> = {
        'validation': 0,
        'planning': 1,
        'micro_prompts': 2,
        'generation': 3,
        'composition': 4,
        'rendering': 5,
      };

      const stepIndex = stepIdToIndex[step.id] ?? index;
      const stepStatus = getStepStatus(stepIndex, currentStep, status);

      return {
        ...step,
        status: stepStatus,
        progress:
          stepStatus === 'in_progress' && (step.id === 'generation' || step.id === 'micro_prompts')
            ? progress?.percentage
            : undefined,
      };
    });
  }, [currentStep, status, progress]);

  /**
   * Handle cancel confirmation
   */
  const handleCancelClick = () => {
    setShowCancelDialog(true);
  };

  /**
   * Confirm cancellation
   */
  const handleCancelConfirm = async () => {
    try {
      await cancel();
      setShowCancelDialog(false);
      // Redirect to history after cancellation
      setTimeout(() => {
        navigate(`${ROUTES.AD_GENERATOR}/history`);
      }, 1000);
    } catch (err) {
      console.error('Failed to cancel generation:', err);
    }
  };

  /**
   * Get progress bar variant based on status
   */
  const getProgressVariant = (): 'primary' | 'success' | 'error' | 'warning' => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'cancelled':
        return 'warning';
      default:
        return 'primary';
    }
  };

  // Loading state
  if (isLoading && clips.length === 0) {
    return (
      <div className="max-w-7xl mx-auto p-6 flex flex-col gap-6 md:p-4">
        <div className="flex flex-col items-center justify-center gap-4 py-16 px-4">
          <Spinner size="xl" />
          <p className="text-lg text-muted-foreground m-0">Loading generation status...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error && !isLoading) {
    return (
      <div className="max-w-7xl mx-auto p-6 flex flex-col gap-6 md:p-4">
        <Card variant="elevated" className="mt-8">
          <CardBody>
            <div className="flex flex-col items-center gap-4 py-8 px-4 text-center">
              <svg
                className="w-16 h-16 text-red-500"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <h2 className="text-2xl font-semibold text-foreground m-0">Error Loading Progress</h2>
              <p className="text-base text-muted-foreground m-0 max-w-md">{error}</p>
              <div className="flex gap-3 mt-4 md:flex-col md:w-full">
                <Button onClick={retry} variant="primary" className="md:w-full">
                  Retry
                </Button>
                <Button onClick={() => navigate(`${ROUTES.AD_GENERATOR}/history`)} variant="outline" className="md:w-full">
                  Back to History
                </Button>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-full bg-background p-8 md:p-4">
      {/* Header */}
      <div className="flex justify-between items-start gap-4 flex-wrap md:flex-col md:items-stretch">
        <div className="flex-1 min-w-0">
          <h1 className="text-3xl font-bold text-foreground mb-2 md:text-2xl">Generating Your Video</h1>
          <div className="flex items-center gap-2">
            {isConnected ? (
              <span className="flex items-center gap-2 text-sm font-medium text-green-500">
                <span className="w-2 h-2 rounded-full bg-current animate-pulse" />
                Real-time updates
              </span>
            ) : isPolling ? (
              <span className="flex items-center gap-2 text-sm font-medium text-yellow-500">
                <span className="w-2 h-2 rounded-full bg-current animate-pulse" />
                Polling for updates
              </span>
            ) : (
              <span className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <span className="w-2 h-2 rounded-full bg-current animate-pulse" />
                Disconnected
              </span>
            )}
          </div>
        </div>

        {/* Actions */}
        {status !== 'completed' && status !== 'failed' && status !== 'cancelled' && (
          <Button
            variant="danger"
            size="md"
            onClick={handleCancelClick}
            disabled={showCancelDialog}
          >
            Cancel Generation
          </Button>
        )}
      </div>

      {/* Overall Progress */}
      <Card variant="elevated" className="animate-in fade-in slide-in-from-bottom-4 duration-500">
        <CardBody>
          <ProgressBar
            percentage={progress?.percentage || 0}
            status={currentStep}
            estimatedTime={estimatedTimeRemaining}
            variant={getProgressVariant()}
            showPercentage
            indeterminate={status === 'queued'}
          />
        </CardBody>
      </Card>

      {/* Step Indicator */}
      <Card variant="elevated" className="animate-in fade-in slide-in-from-bottom-4 duration-500 delay-100">
        <CardHeader title="Generation Progress" subtitle="Following the same steps as the CLI" />
        <CardBody>
          <StepIndicator steps={steps} orientation="vertical" />
          {/* Current Step Details */}
          {currentStep && (
            <div className="mt-4 pt-4 border-t border-border">
              <p className="text-base text-foreground mb-2">
                <strong className="text-primary font-semibold">Current:</strong> {currentStep}
              </p>
              {progress?.percentage !== undefined && (
                <p className="text-sm text-muted-foreground m-0">
                  {progress.percentage.toFixed(1)}% complete
                </p>
              )}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Clip Previews */}
      {clips.length > 0 && (
        <Card variant="elevated" className="animate-in fade-in slide-in-from-bottom-4 duration-500 delay-200">
          <CardHeader
            title="Generated Clips"
            subtitle={`${clips.length} clip${clips.length !== 1 ? 's' : ''} ready`}
          />
          <CardBody>
            <ClipPreviewGrid>
              {clips.map((clip, index) => (
                <ClipPreview
                  key={clip.clip_id}
                  clipId={clip.clip_id}
                  thumbnailUrl={clip.thumbnail_url}
                  duration={clip.duration}
                  clipNumber={index + 1}
                  status="completed"
                />
              ))}

              {/* Show placeholders for pending clips */}
              {progress?.total_clips &&
                progress.current_clip &&
                progress.current_clip < progress.total_clips &&
                Array.from(
                  { length: progress.total_clips - clips.length },
                  (_, i) => (
                    <ClipPreview
                      key={`pending-${i}`}
                      clipId={`pending-${i}`}
                      duration={0}
                      clipNumber={clips.length + i + 1}
                      status="generating"
                    />
                  )
                )}
            </ClipPreviewGrid>
          </CardBody>
        </Card>
      )}

      {/* Completion Message */}
      {status === 'completed' && (
        <Card variant="elevated" className="animate-in fade-in slide-in-from-bottom-4 duration-500 bg-gradient-to-br from-blue-500/5 to-emerald-500/5">
          <CardBody>
            <div className="flex flex-col items-center gap-4 py-8 px-4 text-center">
              <svg
                className="w-16 h-16 text-green-500 animate-in zoom-in duration-500"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
              <h2 className="text-2xl font-semibold text-foreground m-0">Generation Complete!</h2>
              <p className="text-base text-muted-foreground m-0">Your video has been successfully generated.</p>
              <Button onClick={() => navigate(`${ROUTES.AD_GENERATOR}/history`)} variant="primary" size="lg">
                View in History
              </Button>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Cancellation Dialog */}
      {showCancelDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 animate-in fade-in duration-200" onClick={() => setShowCancelDialog(false)}>
          <Card
            variant="elevated"
            className="w-full max-w-[500px] animate-in slide-in-from-bottom-4 duration-300"
            onClick={(e) => e.stopPropagation()}
          >
            <CardHeader title="Cancel Generation?" />
            <CardBody>
              <p className="text-base text-muted-foreground leading-relaxed mb-6">
                Are you sure you want to cancel this generation? This action cannot be undone
                and any progress will be lost.
              </p>
              <div className="flex gap-3 md:flex-col">
                <Button
                  onClick={() => setShowCancelDialog(false)}
                  variant="outline"
                  fullWidth
                >
                  Keep Generating
                </Button>
                <Button onClick={handleCancelConfirm} variant="danger" fullWidth>
                  Yes, Cancel
                </Button>
              </div>
            </CardBody>
          </Card>
        </div>
      )}
    </div>
  );
};

export default GenerationProgress;
