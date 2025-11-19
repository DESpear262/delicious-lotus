import React from 'react';
import { Button } from '../ui/Button';

interface FormContainerProps {
  children: React.ReactNode;
  currentStep: number;
  onNext: () => void;
  onPrevious: () => void;
  onSubmit: () => void;
  isSubmitting?: boolean;
  canGoNext?: boolean;
}

export const FormContainer: React.FC<FormContainerProps> = ({
  children,
  currentStep,
  onNext,
  onPrevious,
  onSubmit,
  isSubmitting = false,
  canGoNext = true,
}) => {
  const isFirstStep = currentStep === 1;
  const isLastStep = currentStep === 4; // Assuming 4 steps

  return (
    <div className="flex flex-col gap-8 w-full md:gap-4 sm:gap-3">
      <div className="bg-card rounded-lg p-8 shadow-md min-h-[400px] md:p-4 md:rounded-md md:min-h-[300px] sm:p-3 sm:min-h-[250px]">
        {children}
      </div>

      <div className="flex justify-between items-center gap-4 pt-4 border-t border-border md:flex-col-reverse md:gap-3 md:sticky md:bottom-0 md:bg-card md:p-4 md:-mx-4 md:border-t-2 md:z-20 md:shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.1)]">
        {!isFirstStep ? (
          <Button
            variant="outline"
            onClick={onPrevious}
            disabled={isSubmitting}
            className="min-w-[140px] md:w-full md:min-w-auto md:min-h-[44px]"
          >
            Back
          </Button>
        ) : (
          <div className="flex-1 md:hidden" />
        )}

        {isLastStep ? (
          <Button
            variant="primary"
            onClick={onSubmit}
            loading={isSubmitting}
            className="min-w-[140px] md:w-full md:min-w-auto md:min-h-[44px]"
          >
            Create Video
          </Button>
        ) : (
          <Button
            variant="primary"
            onClick={onNext}
            disabled={!canGoNext}
            className="min-w-[140px] md:w-full md:min-w-auto md:min-h-[44px]"
          >
            Next Step
          </Button>
        )}
      </div>
    </div>
  );
};
