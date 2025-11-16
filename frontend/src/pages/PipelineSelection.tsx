import React from 'react';
import { PipelineCard } from '../components/PipelineCard';
import { PIPELINES } from '../types/pipeline';
import styles from './PipelineSelection.module.css';

/**
 * PipelineSelection Page Component
 *
 * Home page that displays available video generation pipelines.
 * Users can select between Ad Creative and Music Video pipelines.
 */
export const PipelineSelection: React.FC = () => {
  const pipelines = Object.values(PIPELINES);

  return (
    <div className={styles.pipelineSelectionPage}>
      <div className={styles.header}>
        <h1 className={styles.title}>Choose Your Video Pipeline</h1>
        <p className={styles.subtitle}>
          Select a pipeline to start creating AI-generated videos
        </p>
      </div>

      <div className={styles.pipelineGrid}>
        {pipelines.map((pipeline) => (
          <PipelineCard key={pipeline.id} pipeline={pipeline} />
        ))}
      </div>

      <div className={styles.footer}>
        <p className={styles.footerText}>
          More pipelines coming soon! Each pipeline is optimized for specific video types and use
          cases.
        </p>
      </div>
    </div>
  );
};
