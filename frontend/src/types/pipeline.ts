/**
 * Pipeline Type Definitions
 *
 * Types for the video generation pipeline selection interface.
 */

/**
 * Supported pipeline types for video generation
 */
export type PipelineType = 'ad-creative' | 'music-video';

/**
 * Pipeline status for MVP rollout
 */
export type PipelineStatus = 'available' | 'coming-soon' | 'disabled';

/**
 * Pipeline configuration and metadata
 */
export interface Pipeline {
  id: PipelineType;
  title: string;
  description: string;
  features: string[];
  durationRange: {
    min: number; // in seconds
    max: number; // in seconds
  };
  status: PipelineStatus;
  icon: string; // emoji or icon identifier
  route?: string; // navigation route when available
}

/**
 * Pre-configured pipelines for the application
 */
export const PIPELINES: Record<PipelineType, Pipeline> = {
  'ad-creative': {
    id: 'ad-creative',
    title: 'Ad Creative',
    description: 'Create engaging short-form video advertisements',
    features: [
      'AI-powered scene generation',
      'Professional templates',
      'Brand-safe content',
      'Quick turnaround time',
    ],
    durationRange: {
      min: 15,
      max: 60,
    },
    status: 'available',
    icon: '🎬',
    route: '/create/ad-creative',
  },
  'music-video': {
    id: 'music-video',
    title: 'Music Video',
    description: 'Generate artistic music videos with synchronized visuals',
    features: [
      'Beat-synchronized visuals',
      'Artistic style transfer',
      'Audio-reactive effects',
      'Extended duration support',
    ],
    durationRange: {
      min: 60,
      max: 180,
    },
    status: 'coming-soon',
    icon: '🎵',
  },
};
