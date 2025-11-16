import React from 'react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Switch } from '@/components/ui/Switch';
import type { AdCreativeFormData } from '@/types/form';
import styles from './ReviewStep.module.css';

interface ReviewStepProps {
  formData: AdCreativeFormData;
  onEdit: (step: 1 | 2 | 3) => void;
  isSubmitting: boolean;
  submitError?: string | null;
  onParallelizeChange?: (checked: boolean) => void;
}

export const ReviewStep: React.FC<ReviewStepProps> = ({
  formData,
  onEdit,
  isSubmitting,
  submitError,
  onParallelizeChange,
}) => {
  const estimatedTime = formData.duration <= 30 ? '3-5 minutes' : formData.duration <= 45 ? '5-7 minutes' : '7-10 minutes';

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Review & Submit</h2>
        <p className={styles.description}>
          Please review your settings before creating your video. You can edit any section by clicking the edit button.
        </p>
      </div>

      <div className={styles.sections}>
        {/* Prompt Summary */}
        <Card className={styles.card}>
          <div className={styles.cardHeader}>
            <h3 className={styles.cardTitle}>Video Prompt</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onEdit(1)}
              disabled={isSubmitting}
            >
              Edit
            </Button>
          </div>
          <div className={styles.cardContent}>
            <p className={styles.promptText}>{formData.prompt}</p>
            <div className={styles.metaInfo}>
              {formData.prompt.length} characters
            </div>
          </div>
        </Card>

        {/* Brand Settings Summary */}
        <Card className={styles.card}>
          <div className={styles.cardHeader}>
            <h3 className={styles.cardTitle}>Brand Identity</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onEdit(2)}
              disabled={isSubmitting}
            >
              Edit
            </Button>
          </div>
          <div className={styles.cardContent}>
            <div className={styles.summaryGrid}>
              <div className={styles.summaryItem}>
                <span className={styles.summaryLabel}>Brand Name:</span>
                <span className={styles.summaryValue}>
                  {formData.brandName || 'Not specified'}
                </span>
              </div>

              <div className={styles.summaryItem}>
                <span className={styles.summaryLabel}>Logo:</span>
                <span className={styles.summaryValue}>
                  {formData.brandLogo ? (
                    <div className={styles.logoPreview}>
                      <img src={formData.brandLogo.url} alt="Brand logo" />
                      <span>{formData.brandLogo.filename}</span>
                    </div>
                  ) : (
                    'No logo uploaded'
                  )}
                </span>
              </div>

              <div className={styles.summaryItem}>
                <span className={styles.summaryLabel}>Brand Colors:</span>
                <span className={styles.summaryValue}>
                  <div className={styles.colorSwatches}>
                    <div className={styles.colorSwatch}>
                      <div
                        className={styles.colorBox}
                        style={{ backgroundColor: formData.brandColors.primary }}
                      />
                      <span>{formData.brandColors.primary}</span>
                    </div>
                    <div className={styles.colorSwatch}>
                      <div
                        className={styles.colorBox}
                        style={{ backgroundColor: formData.brandColors.secondary }}
                      />
                      <span>{formData.brandColors.secondary}</span>
                    </div>
                  </div>
                </span>
              </div>

              <div className={styles.summaryItem}>
                <span className={styles.summaryLabel}>Call-to-Action:</span>
                <span className={styles.summaryValue}>
                  {formData.includeCta ? (
                    <>
                      <span className={styles.ctaBadge}>Enabled</span>
                      <span className={styles.ctaText}>"{formData.ctaText}"</span>
                    </>
                  ) : (
                    'Not included'
                  )}
                </span>
              </div>
            </div>
          </div>
        </Card>

        {/* Video Parameters Summary */}
        <Card className={styles.card}>
          <div className={styles.cardHeader}>
            <h3 className={styles.cardTitle}>Video Configuration</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onEdit(3)}
              disabled={isSubmitting}
            >
              Edit
            </Button>
          </div>
          <div className={styles.cardContent}>
            <div className={styles.summaryGrid}>
              <div className={styles.summaryItem}>
                <span className={styles.summaryLabel}>Duration:</span>
                <span className={styles.summaryValue}>{formData.duration} seconds</span>
              </div>

              <div className={styles.summaryItem}>
                <span className={styles.summaryLabel}>Aspect Ratio:</span>
                <span className={styles.summaryValue}>{formData.aspectRatio}</span>
              </div>

              <div className={styles.summaryItem}>
                <span className={styles.summaryLabel}>Visual Style:</span>
                <span className={styles.summaryValue}>
                  {formData.style.charAt(0).toUpperCase() + formData.style.slice(1)}
                </span>
              </div>

              <div className={styles.summaryItem}>
                <span className={styles.summaryLabel}>Music Style:</span>
                <span className={styles.summaryValue}>
                  {formData.musicStyle.charAt(0).toUpperCase() + formData.musicStyle.slice(1)}
                </span>
              </div>
            </div>
          </div>
        </Card>

        {/* Estimated Time */}
        <Card className={styles.estimateCard}>
          <div className={styles.estimateContent}>
            <svg
              width="48"
              height="48"
              viewBox="0 0 48 48"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className={styles.estimateIcon}
            >
              <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="2" />
              <path d="M24 12v12l8 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <div className={styles.estimateText}>
              <h4 className={styles.estimateTitle}>Estimated Generation Time</h4>
              <p className={styles.estimateTime}>{estimatedTime}</p>
              <p className={styles.estimateDescription}>
                You'll be redirected to the progress page where you can monitor the generation in real-time.
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Parallelization Switch */}
      <Card className={styles.optionsCard}>
        <Switch
          id="parallelize-generations"
          checked={formData.parallelizeGenerations}
          onChange={(checked) => onParallelizeChange?.(checked)}
          disabled={isSubmitting}
          label="Parallelize Generation"
          description="Generate video clips in parallel for faster processing. This will be faster but clips may be less consistent with each other."
        />
      </Card>

      {submitError && (
        <div className={styles.errorBox} role="alert">
          <svg
            width="20"
            height="20"
            viewBox="0 0 20 20"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className={styles.errorIcon}
          >
            <path
              fillRule="evenodd"
              clipRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              fill="currentColor"
            />
          </svg>
          <span>{submitError}</span>
        </div>
      )}
    </div>
  );
};
