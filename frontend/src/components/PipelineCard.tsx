import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import type { Pipeline } from '../types/pipeline';
import styles from './PipelineCard.module.css';

export interface PipelineCardProps {
  pipeline: Pipeline;
}

/**
 * PipelineCard Component
 *
 * Displays a clickable card for a video generation pipeline.
 * Shows pipeline details, features, and availability status.
 */
export const PipelineCard: React.FC<PipelineCardProps> = ({ pipeline }) => {
  const navigate = useNavigate();
  const isAvailable = pipeline.status === 'available';
  const isComingSoon = pipeline.status === 'coming-soon';

  const handleCardClick = () => {
    if (isAvailable && pipeline.route) {
      navigate(pipeline.route);
    }
  };

  const handleButtonClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isAvailable && pipeline.route) {
      navigate(pipeline.route);
    }
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
  };

  return (
    <Card
      variant="elevated"
      padding="lg"
      hoverable={isAvailable}
      className={`${styles.pipelineCard} ${!isAvailable ? styles.disabled : ''}`}
      onClick={handleCardClick}
      role={isAvailable ? 'button' : 'article'}
      tabIndex={isAvailable ? 0 : undefined}
      onKeyDown={(e) => {
        if (isAvailable && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          handleCardClick();
        }
      }}
      aria-label={`${pipeline.title} pipeline${isComingSoon ? ' - Coming soon' : ''}`}
    >
      {isComingSoon && (
        <div className={styles.badge} aria-label="Coming soon">
          Coming Soon
        </div>
      )}

      <div className={styles.cardContent}>
        <div className={styles.iconWrapper}>
          <span className={styles.icon} role="img" aria-label={`${pipeline.title} icon`}>
            {pipeline.icon}
          </span>
        </div>

        <h2 className={styles.title}>{pipeline.title}</h2>

        <p className={styles.description}>{pipeline.description}</p>

        <div className={styles.duration}>
          <svg
            className={styles.durationIcon}
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span>
            {formatDuration(pipeline.durationRange.min)} -{' '}
            {formatDuration(pipeline.durationRange.max)}
          </span>
        </div>

        <div className={styles.features}>
          <h3 className={styles.featuresTitle}>Key Features</h3>
          <ul className={styles.featuresList}>
            {pipeline.features.map((feature, index) => (
              <li key={index} className={styles.featureItem}>
                <svg
                  className={styles.featureIcon}
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                <span>{feature}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className={styles.actions}>
          <Button
            variant="primary"
            size="lg"
            fullWidth
            disabled={!isAvailable}
            onClick={handleButtonClick}
            aria-label={
              isAvailable ? `Start creating ${pipeline.title}` : `${pipeline.title} coming soon`
            }
          >
            {isAvailable ? 'Start Creating' : 'Coming Soon'}
          </Button>
        </div>
      </div>
    </Card>
  );
};
