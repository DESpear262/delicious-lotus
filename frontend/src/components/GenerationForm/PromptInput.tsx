import React from 'react';
import { Textarea } from '@/components/ui/Textarea';
import styles from './PromptInput.module.css';

interface PromptInputProps {
  value: string;
  onChange: (value: string) => void;
  onBlur: (value: string) => void;
  error?: string;
}

const EXAMPLE_PROMPTS = [
  'Create a dynamic 30-second ad showcasing our new eco-friendly water bottle. Start with a close-up of morning dew on leaves, transition to an active lifestyle montage (hiking, yoga, cycling), and end with the product against a natural backdrop. Emphasize sustainability and health.',
  'Produce an upbeat advertisement for a productivity app. Begin with a chaotic desk scene, then show the app interface organizing tasks smoothly. Include testimonials from diverse users, and conclude with a clear call-to-action. Modern, professional aesthetic with vibrant colors.',
  'Design a luxury car commercial featuring sleek cityscapes at night. Highlight the vehicle\'s elegant lines with cinematic camera movements, showcase advanced tech features through UI overlays, and emphasize premium craftsmanship. Sophisticated, aspirational tone throughout.',
];

export const PromptInput: React.FC<PromptInputProps> = ({
  value,
  onChange,
  onBlur,
  error,
}) => {
  const charCount = value.length;
  const isValid = charCount >= 500 && charCount <= 2000;
  const isNearMin = charCount > 0 && charCount < 500;
  const isNearMax = charCount > 1800;

  const handleUseExample = (example: string) => {
    onChange(example);
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Describe Your Video</h2>
        <p className={styles.description}>
          Provide a detailed description of the video you want to create. Include visual elements, transitions, messaging, and mood. The more specific you are, the better the results.
        </p>
      </div>

      <Textarea
        label="Video Prompt"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onBlur={(e) => onBlur(e.target.value)}
        error={error}
        placeholder="Describe your video in detail (500-2000 characters)..."
        minLength={500}
        maxLength={2000}
        showCounter
        fullWidth
        rows={8}
        helperText={
          isNearMin
            ? `${500 - charCount} more characters needed`
            : isNearMax
            ? `${2000 - charCount} characters remaining`
            : undefined
        }
      />

      {!isValid && charCount === 0 && (
        <div className={styles.examplesSection}>
          <h3 className={styles.examplesTitle}>Example Prompts</h3>
          <p className={styles.examplesDescription}>
            Not sure where to start? Try one of these examples:
          </p>
          <div className={styles.examples}>
            {EXAMPLE_PROMPTS.map((example, index) => (
              <button
                key={index}
                type="button"
                onClick={() => handleUseExample(example)}
                className={styles.exampleButton}
              >
                <div className={styles.exampleHeader}>
                  <span className={styles.exampleLabel}>Example {index + 1}</span>
                  <span className={styles.exampleAction}>Use this prompt →</span>
                </div>
                <p className={styles.exampleText}>{example}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className={styles.tips}>
        <h4 className={styles.tipsTitle}>💡 Tips for effective prompts:</h4>
        <ul className={styles.tipsList}>
          <li>Be specific about visual elements, camera angles, and transitions</li>
          <li>Describe the mood, tone, and pacing you want</li>
          <li>Include details about colors, lighting, and aesthetic preferences</li>
          <li>Mention any text overlays, captions, or key messages</li>
          <li>Specify the target audience and desired emotional impact</li>
        </ul>
      </div>
    </div>
  );
};
