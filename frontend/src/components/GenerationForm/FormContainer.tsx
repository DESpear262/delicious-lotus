import React from 'react';
import { Button } from '@/components/ui/Button';
import styles from './FormContainer.module.css';

interface FormContainerProps {
  children: React.ReactNode;
  currentStep: 1 | 2 | 3 | 4;
  onNext: () => void;
  onPrevious: () => void;
  onSubmit: () => void;
  isSubmitting: boolean;
  canGoNext: boolean;
}

export const FormContainer: React.FC<FormContainerProps> = ({
  children,
  currentStep,
  onNext,
  onPrevious,
  onSubmit,
  isSubmitting,
  canGoNext = true,
}) => {
  const isFirstStep = currentStep === 1;
  const isLastStep = currentStep === 4;

  return (
    <div className={styles.container}>
      <div className={styles.content}>{children}</div>

      <div className={styles.navigation}>
        {!isFirstStep && (
          <Button
            variant="outline"
            onClick={onPrevious}
            disabled={isSubmitting}
            className={styles.backButton}
          >
            ← Back
          </Button>
        )}

        <div className={styles.spacer} />

        {isLastStep ? (
          <Button
            variant="primary"
            onClick={onSubmit}
            loading={isSubmitting}
            disabled={isSubmitting}
            className={styles.submitButton}
          >
            {isSubmitting ? 'Creating Video...' : 'Create Video'}
          </Button>
        ) : (
          <Button
            variant="primary"
            onClick={onNext}
            disabled={!canGoNext || isSubmitting}
            className={styles.nextButton}
          >
            Continue →
          </Button>
        )}
      </div>
    </div>
  );
};
