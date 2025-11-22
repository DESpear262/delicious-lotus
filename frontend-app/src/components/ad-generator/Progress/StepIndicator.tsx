/**
 * StepIndicator Component
 * Displays step-by-step progress with visual indicators
 */

import React from 'react';
import styles from './StepIndicator.module.css';

export type StepStatus = 'completed' | 'in_progress' | 'pending' | 'error';

export interface Step {
  /** Step identifier */
  id: string;
  /** Step label */
  label: string;
  /** Step description */
  description?: string;
  /** Step status */
  status: StepStatus;
  /** Progress within the step (0-100) */
  progress?: number;
  /** Additional info (e.g., "5/10 clips") */
  info?: string;
}

export interface StepIndicatorProps {
  /** Array of steps */
  steps: Step[];
  /** Current active step index */
  currentStepIndex?: number;
  /** Vertical or horizontal layout */
  orientation?: 'vertical' | 'horizontal';
  /** Additional CSS classes */
  className?: string;
}

/**
 * Icon for step status
 */
const StepIcon: React.FC<{ status: StepStatus }> = ({ status }) => {
  switch (status) {
    case 'completed':
      return (
        <svg
          className={styles.icon}
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="20 6 9 17 4 12" />
        </svg>
      );

    case 'in_progress':
      return (
        <svg
          className={`${styles.icon} ${styles.spinning}`}
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="12" cy="12" r="10" opacity="0.25" />
          <path d="M12 2a10 10 0 0 1 10 10" />
        </svg>
      );

    case 'error':
      return (
        <svg
          className={styles.icon}
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="15" y1="9" x2="9" y2="15" />
          <line x1="9" y1="9" x2="15" y2="15" />
        </svg>
      );

    case 'pending':
    default:
      return <div className={styles.iconDot} />;
  }
};

/**
 * StepIndicator component for displaying generation steps
 */
export const StepIndicator: React.FC<StepIndicatorProps> = ({
  steps,
  currentStepIndex,
  orientation = 'vertical',
  className = '',
}) => {
  const containerClasses = [
    styles.container,
    styles[`container-${orientation}`],
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={containerClasses}>
      {steps.map((step, index) => {
        const isActive = currentStepIndex === index;
        const isLast = index === steps.length - 1;

        const stepClasses = [
          styles.step,
          styles[`step-${step.status}`],
          isActive && styles.stepActive,
        ]
          .filter(Boolean)
          .join(' ');

        return (
          <div key={step.id} className={stepClasses}>
            {/* Step indicator */}
            <div className={styles.stepIndicator}>
              <div className={styles.iconContainer}>
                <StepIcon status={step.status} />
              </div>

              {/* Connector line */}
              {!isLast && (
                <div
                  className={`${styles.connector} ${
                    step.status === 'completed' ? styles.connectorCompleted : ''
                  }`}
                />
              )}
            </div>

            {/* Step content */}
            <div className={styles.stepContent}>
              <div className={styles.stepHeader}>
                <h4 className={styles.stepLabel}>{step.label}</h4>
                {step.info && <span className={styles.stepInfo}>{step.info}</span>}
              </div>

              {step.description && (
                <p className={styles.stepDescription}>{step.description}</p>
              )}

              {/* Progress bar for in-progress steps */}
              {step.status === 'in_progress' && step.progress !== undefined && (
                <div className={styles.stepProgressContainer}>
                  <div className={styles.stepProgressTrack}>
                    <div
                      className={styles.stepProgressBar}
                      style={{ width: `${step.progress}%` }}
                    />
                  </div>
                  <span className={styles.stepProgressLabel}>{step.progress}%</span>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

StepIndicator.displayName = 'StepIndicator';
