import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import type { Pipeline } from '../../types/ad-generator/pipeline';

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
      className={`relative cursor-pointer transition-all duration-200 min-h-[500px] flex flex-col md:min-h-auto group
        ${isAvailable
          ? 'hover:-translate-y-1 hover:shadow-xl active:-translate-y-0.5 focus-visible:outline-2 focus-visible:outline-primary focus-visible:outline-offset-2'
          : 'cursor-not-allowed opacity-70 hover:shadow-lg'
        }`}
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
        <div className="absolute top-4 right-4 bg-gradient-to-br from-yellow-500 to-orange-500 text-white px-4 py-2 rounded-full text-sm font-semibold shadow-md z-10 animate-pulse md:top-3 md:right-3 md:px-3 md:py-1 md:text-xs" aria-label="Coming soon">
          Coming Soon
        </div>
      )}

      <div className="flex flex-col gap-4 h-full">
        <div className="flex justify-center items-center mb-2">
          <span className="text-6xl leading-none animate-in fade-in zoom-in-90 duration-500 md:text-5xl group-hover:scale-110 transition-transform duration-200" role="img" aria-label={`${pipeline.title} icon`}>
            {pipeline.icon}
          </span>
        </div>

        <h2 className="text-2xl font-bold text-foreground text-center m-0 leading-tight md:text-xl">{pipeline.title}</h2>

        <p className="text-base text-muted-foreground text-center m-0 leading-relaxed">{pipeline.description}</p>

        <div className="flex items-center justify-center gap-2 px-4 py-3 bg-muted rounded-lg text-sm font-medium text-muted-foreground">
          <svg
            className="w-5 h-5 text-primary"
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

        <div className="flex-1 flex flex-col gap-3">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider m-0 text-left">Key Features</h3>
          <ul className="list-none p-0 m-0 flex flex-col gap-3">
            {pipeline.features.map((feature, index) => (
              <li key={index} className="flex items-start gap-3 text-sm text-foreground leading-relaxed">
                <svg
                  className="w-5 h-5 text-green-500 shrink-0 mt-0.5"
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

        <div className="mt-auto pt-4">
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
