/**
 * SubmissionProgressScreen
 * Displays the generation progress experience while the create generation
 * request is still running (pre-flight / OpenAI preprocessing).
 */

import React, { useEffect, useMemo, useState } from 'react';
import { ProgressBar } from '@/components/Progress/ProgressBar';
import { StepIndicator, type Step } from '@/components/Progress/StepIndicator';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import styles from './SubmissionProgressScreen.module.css';

const PREPROCESS_STEPS = [
  {
    id: 'validation',
    label: 'Step 1: Validating Prompt',
    description: 'Running safety checks and formatting your request...',
  },
  {
    id: 'analysis',
    label: 'Step 2: Analyzing Prompt',
    description: 'Parsing objectives, tone, and key themes...',
  },
  {
    id: 'planning',
    label: 'Step 3: Decomposing into Scenes',
    description: 'Designing narrative beats and transitions...',
  },
  {
    id: 'micro',
    label: 'Step 4: Building Micro-Prompts',
    description: 'Crafting detailed instructions for each scene...',
  },
  {
    id: 'generating',
    label: 'Step 5: Preparing Generation Pipeline',
    description: 'Queuing clip jobs and warming models...',
  },
  {
    id: 'handoff',
    label: 'Step 6: Handing Off to Clip Generation',
    description: 'Connecting to the realtime progress service...',
  },
];

const STEP_INTERVAL_MS = 1600;

export const SubmissionProgressScreen: React.FC = () => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStepIndex((prev) =>
        prev < PREPROCESS_STEPS.length - 1 ? prev + 1 : prev
      );
    }, STEP_INTERVAL_MS);

    return () => clearInterval(interval);
  }, []);

  const overallPercentage = useMemo(() => {
    if (PREPROCESS_STEPS.length === 1) {
      return 95;
    }
    const progressPerStep = 90 / (PREPROCESS_STEPS.length - 1);
    const percentage = 5 + currentStepIndex * progressPerStep;
    return Math.min(Math.round(percentage), 95);
  }, [currentStepIndex]);

  const steps: Step[] = useMemo(
    () =>
      PREPROCESS_STEPS.map((step, index) => {
        let status: Step['status'] = 'pending';
        if (index < currentStepIndex) {
          status = 'completed';
        } else if (index === currentStepIndex) {
          status = 'in_progress';
        }

        return {
          ...step,
          status,
        };
      }),
    [currentStepIndex]
  );

  return (
    <div className={styles.wrapper}>
      <div className={styles.container}>
        <header className={styles.header}>
          <p className={styles.status}>Initializing generation pipeline...</p>
          <h1 className={styles.title}>Preparing Your Video</h1>
          <p className={styles.subtitle}>
            Hang tight! We’re validating the prompt and setting up the AI pipeline.
            You’ll move to live clip generation in just a moment.
          </p>
        </header>

        <Card variant="elevated" className={styles.progressCard}>
          <CardBody>
            <ProgressBar
              percentage={overallPercentage}
              status="preprocessing"
              showPercentage
            />
          </CardBody>
        </Card>

        <Card variant="elevated" className={styles.stepsCard}>
          <CardHeader
            title="Generation Progress"
            subtitle="Following the same steps as the CLI"
          />
          <CardBody>
            <StepIndicator steps={steps} currentStepIndex={currentStepIndex} />
            <div className={styles.currentStep}>
              <span>Current:</span>
              <strong>{PREPROCESS_STEPS[currentStepIndex].label}</strong>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
};

SubmissionProgressScreen.displayName = 'SubmissionProgressScreen';

