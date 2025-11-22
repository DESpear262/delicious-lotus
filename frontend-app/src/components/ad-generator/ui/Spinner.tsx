import React from 'react';
import styles from './Spinner.module.css';

export interface SpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'primary' | 'secondary' | 'white';
  label?: string;
}

export const Spinner = React.forwardRef<HTMLDivElement, SpinnerProps>(
  (
    {
      size = 'md',
      variant = 'primary',
      label = 'Loading...',
      className = '',
      ...props
    },
    ref
  ) => {
    const spinnerClasses = [
      styles.spinner,
      styles[`spinner-${size}`],
      styles[`spinner-${variant}`],
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <div ref={ref} className={spinnerClasses} role="status" aria-live="polite" {...props}>
        <svg
          className={styles.spinnerSvg}
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className={styles.spinnerCircle}
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className={styles.spinnerPath}
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
        <span className="sr-only">{label}</span>
      </div>
    );
  }
);

Spinner.displayName = 'Spinner';

export interface SpinnerOverlayProps {
  visible: boolean;
  label?: string;
}

export const SpinnerOverlay: React.FC<SpinnerOverlayProps> = ({
  visible,
  label = 'Loading...',
}) => {
  if (!visible) return null;

  return (
    <div className={styles.overlay} aria-live="assertive">
      <div className={styles.overlayContent}>
        <Spinner size="xl" variant="white" label={label} />
        {label && <p className={styles.overlayLabel}>{label}</p>}
      </div>
    </div>
  );
};

SpinnerOverlay.displayName = 'SpinnerOverlay';
