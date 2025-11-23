import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { FileText, Settings, Pencil, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { AdCreativeFormData } from '@/types/ad-generator/form';

interface ReviewStepProps {
  formData: AdCreativeFormData;
  onEdit: (step: 1 | 2 | 3) => void;
  isSubmitting: boolean;
  submitError?: string | null;
  onParallelizeChange?: (checked: boolean) => void;
  promptResult?: any; // Using any to avoid importing the type if not strictly needed here, or import VideoPromptResponse
}

export const ReviewStep: React.FC<ReviewStepProps> = ({
  formData,
  onEdit,
  isSubmitting,
  submitError,
  onParallelizeChange,
  promptResult,
}) => {

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">
          Review & Submit
        </h2>
        <p className="text-muted-foreground">
          Please review your settings before creating your video.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="space-y-4">
        {/* Prompt Summary */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Video Prompt
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onEdit(1)}
                disabled={isSubmitting}
                className="h-8 gap-1.5"
              >
                <Pencil className="h-3.5 w-3.5" />
                Edit
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <p className="text-sm text-foreground whitespace-pre-wrap line-clamp-4">
              {formData.prompt}
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              {formData.prompt.length} characters
            </p>
          </CardContent>
        </Card>



        {/* Video Config Summary */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Video Configuration
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onEdit(3)}
                disabled={isSubmitting}
                className="h-8 gap-1.5"
              >
                <Pencil className="h-3.5 w-3.5" />
                Edit
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Duration</Label>
                <p className="text-sm font-medium text-foreground">{formData.duration}s</p>
              </div>
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Aspect Ratio</Label>
                <p className="text-sm font-medium text-foreground">{formData.aspectRatio}</p>
              </div>
            </div>
          </CardContent>
        </Card>


      </div>

      {/* Error Message */}
      {submitError && (
        <div className="flex items-center gap-3 p-4 rounded-lg bg-destructive/10 border border-destructive/20">
          <AlertCircle className="h-5 w-5 text-destructive shrink-0" />
          <p className="text-sm text-destructive">{submitError}</p>
        </div>
      )}
    </div>
  );
};
