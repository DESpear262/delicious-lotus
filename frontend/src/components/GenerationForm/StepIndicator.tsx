import React from 'react';
import styles from './StepIndicator.module.css';
import { STEP_INFO } from '@/utils/formValidation';

interface StepIndicatorProps {
  currentStep: 1 | 2 | 3 | 4;
  onStepClick?: (step: 1 | 2 | 3 | 4) => void;
  completedSteps: number[];
}

export const StepIndicator: React.FC<StepIndicatorProps> = ({
  currentStep,
  onStepClick,
  completedSteps,
}) => {
  const handleStepClick = (stepNumber: 1 | 2 | 3 | 4) => {
    // Only allow clicking on completed steps or current step
    if (stepNumber <= currentStep && onStepClick) {
      onStepClick(stepNumber);
    }
  };

  return (
    <div className={styles.container} role="progressbar" aria-valuenow={currentStep} aria-valuemin={1} aria-valuemax={4}>
      {STEP_INFO.map((step, index) => {
        const stepNumber = step.number as 1 | 2 | 3 | 4;
        const isActive = currentStep === stepNumber;
        const isComplete = completedSteps.includes(stepNumber);
        const isClickable = stepNumber <= currentStep;

        const stepClasses = [
          styles.step,
          isActive && styles.stepActive,
          isComplete && styles.stepComplete,
          isClickable && styles.stepClickable,
        ]
          .filter(Boolean)
          .join(' ');

        const numberClasses = [
          styles.stepNumber,
          isActive && styles.stepNumberActive,
          isComplete && styles.stepNumberComplete,
        ]
          .filter(Boolean)
          .join(' ');

        return (
          <div key={stepNumber} className={stepClasses}>
            <button
              type="button"
              onClick={() => handleStepClick(stepNumber)}
              disabled={!isClickable}
              className={styles.stepButton}
              aria-label={`Step ${stepNumber}: ${step.title}`}
              aria-current={isActive ? 'step' : undefined}
            >
              <div className={numberClasses}>
                {isComplete ? (
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path
                      d="M13.3333 4L6 11.3333L2.66666 8"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                ) : (
                  stepNumber
                )}
              </div>
              <div className={styles.stepContent}>
                <div className={styles.stepTitle}>{step.title}</div>
                <div className={styles.stepDescription}>{step.description}</div>
              </div>
            </button>
            {index < STEP_INFO.length - 1 && (
              <div className={styles.connector} aria-hidden="true" />
            )}
          </div>
        );
      })}
    </div>
  );
};
