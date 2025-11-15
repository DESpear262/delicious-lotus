/**
 * GenerationProgress Page
 * Real-time progress tracking for video generation
 */

import React, { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useGenerationProgress } from '@/hooks/useGenerationProgress';
import { ProgressBar } from '@/components/Progress/ProgressBar';
import { StepIndicator } from '@/components/Progress/StepIndicator';
import type { Step, StepStatus } from '@/components/Progress/StepIndicator';
import { ClipPreview, ClipPreviewGrid } from '@/components/Progress/ClipPreview';
import { Card, CardHeader, CardBody } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import styles from './GenerationProgress.module.css';
import type { GenerationStatus } from '@/api/types';

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
    'planning',
    'generation',
    'composition',
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
        navigate(`/history`);
      }, 2000);
    },
    onError: (errorData) => {
      console.error('Generation error:', errorData);
    },
  });

  /**
   * Build steps array from current progress
   */
  const steps: Step[] = useMemo(() => {
    const baseSteps = [
      {
        id: 'validation',
        label: 'Input Validation',
        description: 'Validating prompt and parameters',
      },
      {
        id: 'planning',
        label: 'Content Planning',
        description: 'Planning scenes and structure',
      },
      {
        id: 'generation',
        label: 'Asset Generation',
        description: 'Generating video clips',
        info:
          progress?.current_clip && progress?.total_clips
            ? `${progress.current_clip}/${progress.total_clips} clips`
            : undefined,
      },
      {
        id: 'composition',
        label: 'Video Composition',
        description: 'Assembling final video',
      },
      {
        id: 'rendering',
        label: 'Final Rendering',
        description: 'Rendering and encoding',
      },
    ];

    return baseSteps.map((step, index) => {
      const stepStatus = getStepStatus(index, currentStep, status);

      return {
        ...step,
        status: stepStatus,
        progress:
          stepStatus === 'in_progress' && step.id === 'generation'
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
        navigate('/history');
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
      <div className={styles.container}>
        <div className={styles.loadingContainer}>
          <Spinner size="xl" />
          <p className={styles.loadingText}>Loading generation status...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error && !isLoading) {
    return (
      <div className={styles.container}>
        <Card variant="elevated" className={styles.errorCard}>
          <CardBody>
            <div className={styles.errorContent}>
              <svg
                className={styles.errorIcon}
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
              <h2>Error Loading Progress</h2>
              <p>{error}</p>
              <div className={styles.errorActions}>
                <Button onClick={retry} variant="primary">
                  Retry
                </Button>
                <Button onClick={() => navigate('/history')} variant="outline">
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
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.title}>Generating Your Video</h1>
          <div className={styles.connectionStatus}>
            {isConnected ? (
              <span className={styles.statusConnected}>
                <span className={styles.statusDot} />
                Real-time updates
              </span>
            ) : isPolling ? (
              <span className={styles.statusPolling}>
                <span className={styles.statusDot} />
                Polling for updates
              </span>
            ) : (
              <span className={styles.statusDisconnected}>
                <span className={styles.statusDot} />
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
      <Card variant="elevated" className={styles.progressCard}>
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
      <Card variant="elevated" className={styles.stepsCard}>
        <CardHeader title="Progress Steps" />
        <CardBody>
          <StepIndicator steps={steps} orientation="vertical" />
        </CardBody>
      </Card>

      {/* Clip Previews */}
      {clips.length > 0 && (
        <Card variant="elevated" className={styles.clipsCard}>
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
        <Card variant="elevated" className={styles.completionCard}>
          <CardBody>
            <div className={styles.completionContent}>
              <svg
                className={styles.completionIcon}
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
              <h2>Generation Complete!</h2>
              <p>Your video has been successfully generated.</p>
              <Button onClick={() => navigate('/history')} variant="primary" size="lg">
                View in History
              </Button>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Cancellation Dialog */}
      {showCancelDialog && (
        <div className={styles.dialogOverlay} onClick={() => setShowCancelDialog(false)}>
          <Card
            variant="elevated"
            className={styles.dialog}
            onClick={(e) => e.stopPropagation()}
          >
            <CardHeader title="Cancel Generation?" />
            <CardBody>
              <p className={styles.dialogText}>
                Are you sure you want to cancel this generation? This action cannot be undone
                and any progress will be lost.
              </p>
              <div className={styles.dialogActions}>
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
