import React from 'react';
import { Radio } from '@/components/ui/Radio';
import { Select } from '@/components/ui/Select';
import { VideoStyle, MusicStyle } from '@/types/form';
import styles from './VideoParameters.module.css';

interface VideoParametersProps {
  duration: 15 | 30 | 45 | 60;
  aspectRatio: '16:9' | '9:16' | '1:1';
  style: VideoStyle;
  musicStyle: MusicStyle;
  errors: Record<string, string>;
  onDurationChange: (duration: 15 | 30 | 45 | 60) => void;
  onAspectRatioChange: (ratio: '16:9' | '9:16' | '1:1') => void;
  onStyleChange: (style: VideoStyle) => void;
  onMusicStyleChange: (style: MusicStyle) => void;
}

const STYLE_OPTIONS = [
  { value: 'professional', label: 'Professional' },
  { value: 'casual', label: 'Casual' },
  { value: 'modern', label: 'Modern' },
  { value: 'luxury', label: 'Luxury' },
  { value: 'minimal', label: 'Minimal' },
  { value: 'energetic', label: 'Energetic' },
  { value: 'elegant', label: 'Elegant' },
];

const MUSIC_STYLE_OPTIONS = [
  { value: 'corporate', label: 'Corporate' },
  { value: 'upbeat', label: 'Upbeat' },
  { value: 'cinematic', label: 'Cinematic' },
  { value: 'ambient', label: 'Ambient' },
  { value: 'electronic', label: 'Electronic' },
  { value: 'none', label: 'No Music' },
];

export const VideoParameters: React.FC<VideoParametersProps> = ({
  duration,
  aspectRatio,
  style,
  musicStyle,
  errors,
  onDurationChange,
  onAspectRatioChange,
  onStyleChange,
  onMusicStyleChange,
}) => {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Video Configuration</h2>
        <p className={styles.description}>
          Choose the technical parameters for your video.
        </p>
      </div>

      <div className={styles.section}>
        <Radio
          label="Duration"
          options={[
            {
              value: '15',
              label: '15 seconds',
              description: 'Quick, punchy ads for social media',
            },
            {
              value: '30',
              label: '30 seconds',
              description: 'Standard ad length, balanced content',
            },
            {
              value: '45',
              label: '45 seconds',
              description: 'Extended storytelling opportunity',
            },
            {
              value: '60',
              label: '60 seconds',
              description: 'Full-length ad with detailed narrative',
            },
          ]}
          value={String(duration)}
          onChange={(value) => onDurationChange(Number(value) as 15 | 30 | 45 | 60)}
          name="duration"
          error={errors.duration}
          helperText="Longer videos allow for more detailed storytelling but may require more generation time"
        />
      </div>

      <div className={styles.section}>
        <Radio
          label="Aspect Ratio"
          options={[
            {
              value: '16:9',
              label: '16:9 (Landscape)',
              description: 'YouTube, websites, traditional platforms',
            },
            {
              value: '9:16',
              label: '9:16 (Portrait)',
              description: 'Instagram Stories, TikTok, Reels',
            },
            {
              value: '1:1',
              label: '1:1 (Square)',
              description: 'Instagram feed, Facebook, versatile format',
            },
          ]}
          value={aspectRatio}
          onChange={(value) => onAspectRatioChange(value as '16:9' | '9:16' | '1:1')}
          name="aspectRatio"
          error={errors.aspectRatio}
          helperText="Choose the format that matches your distribution platform"
        />
      </div>

      <div className={styles.section}>
        <Select
          label="Visual Style"
          options={STYLE_OPTIONS}
          value={style}
          onChange={(e) => onStyleChange(e.target.value as VideoStyle)}
          error={errors.style}
          helperText="The overall aesthetic and mood of your video"
          fullWidth
        />
      </div>

      <div className={styles.section}>
        <Select
          label="Music Style"
          options={MUSIC_STYLE_OPTIONS}
          value={musicStyle}
          onChange={(e) => onMusicStyleChange(e.target.value as MusicStyle)}
          error={errors.musicStyle}
          helperText="Background music to complement your video"
          fullWidth
        />
      </div>

      <div className={styles.estimateBox}>
        <div className={styles.estimateHeader}>
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className={styles.estimateIcon}
          >
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
            <path d="M12 6v6l4 2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
          <h4 className={styles.estimateTitle}>Estimated Generation Time</h4>
        </div>
        <p className={styles.estimateTime}>
          {duration <= 30 ? '3-5 minutes' : duration <= 45 ? '5-7 minutes' : '7-10 minutes'}
        </p>
        <p className={styles.estimateDescription}>
          Actual time may vary based on system load and complexity of your prompt.
        </p>
      </div>
    </div>
  );
};
