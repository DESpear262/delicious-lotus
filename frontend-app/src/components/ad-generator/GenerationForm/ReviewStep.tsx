import React from 'react';
import { Button } from '@/components/ad-generator/ui/Button';
import { Card } from '@/components/ad-generator/ui/Card';
import { Switch } from '@/components/ad-generator/ui/Switch';
import type { AdCreativeFormData } from '@/types/ad-generator/form';

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
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h2 className="text-2xl font-bold text-foreground m-0 sm:text-xl">Review & Submit</h2>
        <p className="text-base text-muted-foreground leading-relaxed m-0">
          Please review your settings before creating your video. You can edit any section by clicking the edit button.
        </p>
      </div>

      <div className="flex flex-col gap-4">
        {/* Prompt Summary */}
        <Card className="p-5">
          <div className="flex justify-between items-center mb-4 pb-3 border-b border-border sm:flex-col sm:items-start sm:gap-3">
            <h3 className="text-lg font-semibold text-foreground m-0">Video Prompt</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onEdit(1)}
              disabled={isSubmitting}
              className="min-h-[44px] min-w-[44px] py-2 px-4"
            >
              Edit
            </Button>
          </div>
          <div className="flex flex-col gap-3">
            <p className="text-base text-foreground leading-relaxed m-0 whitespace-pre-wrap">{formData.prompt}</p>
            <div className="text-sm text-muted-foreground">
              {formData.prompt.length} characters
            </div>
          </div>
        </Card>

        {/* Brand Settings Summary */}
        <Card className="p-5">
          <div className="flex justify-between items-center mb-4 pb-3 border-b border-border sm:flex-col sm:items-start sm:gap-3">
            <h3 className="text-lg font-semibold text-foreground m-0">Brand Identity</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onEdit(2)}
              disabled={isSubmitting}
              className="min-h-[44px] min-w-[44px] py-2 px-4"
            >
              Edit
            </Button>
          </div>
          <div className="flex flex-col gap-3">
            <div className="flex flex-col gap-3">
              <div className="flex flex-col gap-1">
                <span className="text-sm font-medium text-muted-foreground">Brand Name:</span>
                <span className="text-base text-foreground flex items-center gap-2 flex-wrap sm:text-base">
                  {formData.brandName || 'Not specified'}
                </span>
              </div>

              <div className="flex flex-col gap-1">
                <span className="text-sm font-medium text-muted-foreground">Logo:</span>
                <span className="text-base text-foreground flex items-center gap-2 flex-wrap sm:text-base">
                  {formData.brandLogo ? (
                    <div className="flex items-center gap-2">
                      <img src={formData.brandLogo.url} alt="Brand logo" className="w-8 h-8 object-contain border border-border rounded-sm" />
                      <span>{formData.brandLogo.filename}</span>
                    </div>
                  ) : (
                    'No logo uploaded'
                  )}
                </span>
              </div>

              <div className="flex flex-col gap-1">
                <span className="text-sm font-medium text-muted-foreground">Brand Colors:</span>
                <span className="text-base text-foreground flex items-center gap-2 flex-wrap sm:text-base">
                  <div className="flex gap-3">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-6 h-6 border border-border rounded-sm"
                        style={{ backgroundColor: formData.brandColors.primary }}
                      />
                      <span>{formData.brandColors.primary}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div
                        className="w-6 h-6 border border-border rounded-sm"
                        style={{ backgroundColor: formData.brandColors.secondary }}
                      />
                      <span>{formData.brandColors.secondary}</span>
                    </div>
                  </div>
                </span>
              </div>

              <div className="flex flex-col gap-1">
                <span className="text-sm font-medium text-muted-foreground">Call-to-Action:</span>
                <span className="text-base text-foreground flex items-center gap-2 flex-wrap sm:text-base">
                  {formData.includeCta ? (
                    <>
                      <span className="inline-block px-2 py-1 bg-green-500 text-white text-xs font-medium rounded-sm">Enabled</span>
                      <span className="italic">"{formData.ctaText}"</span>
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
        <Card className="p-5">
          <div className="flex justify-between items-center mb-4 pb-3 border-b border-border sm:flex-col sm:items-start sm:gap-3">
            <h3 className="text-lg font-semibold text-foreground m-0">Video Configuration</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onEdit(3)}
              disabled={isSubmitting}
              className="min-h-[44px] min-w-[44px] py-2 px-4"
            >
              Edit
            </Button>
          </div>
          <div className="flex flex-col gap-3">
            <div className="flex flex-col gap-3">
              <div className="flex flex-col gap-1">
                <span className="text-sm font-medium text-muted-foreground">Duration:</span>
                <span className="text-base text-foreground flex items-center gap-2 flex-wrap sm:text-base">{formData.duration} seconds</span>
              </div>

              <div className="flex flex-col gap-1">
                <span className="text-sm font-medium text-muted-foreground">Aspect Ratio:</span>
                <span className="text-base text-foreground flex items-center gap-2 flex-wrap sm:text-base">{formData.aspectRatio}</span>
              </div>

              <div className="flex flex-col gap-1">
                <span className="text-sm font-medium text-muted-foreground">Visual Style:</span>
                <span className="text-base text-foreground flex items-center gap-2 flex-wrap sm:text-base">
                  {formData.style.charAt(0).toUpperCase() + formData.style.slice(1)}
                </span>
              </div>

              <div className="flex flex-col gap-1">
                <span className="text-sm font-medium text-muted-foreground">Music Style:</span>
                <span className="text-base text-foreground flex items-center gap-2 flex-wrap sm:text-base">
                  {formData.musicStyle.charAt(0).toUpperCase() + formData.musicStyle.slice(1)}
                </span>
              </div>
            </div>
          </div>
        </Card>

        {/* Estimated Time */}
        <Card className="bg-gradient-to-br from-blue-500/10 to-emerald-500/10 border-2 border-primary p-5">
          <div className="flex gap-4 items-center sm:flex-col sm:items-start sm:gap-2">
            <svg
              width="48"
              height="48"
              viewBox="0 0 48 48"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="shrink-0 text-primary"
            >
              <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="2" />
              <path d="M24 12v12l8 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <div className="flex flex-col gap-2">
              <h4 className="text-lg font-semibold text-foreground m-0">Estimated Generation Time</h4>
              <p className="text-2xl font-bold text-primary m-0 sm:text-2xl">{estimatedTime}</p>
              <p className="text-sm text-muted-foreground leading-normal m-0">
                You'll be redirected to the progress page where you can monitor the generation in real-time.
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Parallelization Switch */}
      <Card className="p-5 border border-border">
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
        <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500 rounded-md text-red-500 text-sm" role="alert">
          <svg
            width="20"
            height="20"
            viewBox="0 0 20 20"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="shrink-0"
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
