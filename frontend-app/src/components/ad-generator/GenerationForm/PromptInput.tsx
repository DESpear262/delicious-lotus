import React from 'react';
import { Textarea } from '@/components/ad-generator/ui/Textarea';

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
  const isValid = charCount > 0 && charCount <= 2000;
  const isNearMax = charCount > 1800;

  const handleUseExample = (example: string) => {
    onChange(example);
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h2 className="text-2xl font-bold text-foreground m-0 sm:text-xl">Describe Your Video</h2>
        <p className="text-base text-muted-foreground leading-relaxed m-0">
          Provide a detailed description of the video you want to create. Include visual elements, transitions, messaging, and mood. The more specific you are, the better the results.
        </p>
      </div>

      <Textarea
        label="Video Prompt"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onBlur={(e) => onBlur(e.target.value)}
        error={error}
        placeholder="Describe your video in detail (max 2000 characters)..."
        maxLength={2000}
        showCounter
        fullWidth
        rows={8}
        helperText={
          isNearMax
            ? `${2000 - charCount} characters remaining`
            : undefined
        }
        className="min-h-[160px] text-base sm:min-h-[140px]"
      />

      {!isValid && charCount === 0 && (
        <div className="flex flex-col gap-3 p-4 bg-secondary rounded-lg">
          <h3 className="text-lg font-semibold text-foreground m-0">Example Prompts</h3>
          <p className="text-sm text-muted-foreground m-0">
            Not sure where to start? Try one of these examples:
          </p>
          <div className="flex flex-col gap-3">
            {EXAMPLE_PROMPTS.map((example, index) => (
              <button
                key={index}
                type="button"
                onClick={() => handleUseExample(example)}
                className="flex flex-col gap-2 p-4 bg-card border border-border rounded-md cursor-pointer text-left transition-all hover:border-primary hover:shadow-md hover:-translate-y-0.5 focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 group"
              >
                <div className="flex justify-between items-center w-full sm:flex-col sm:items-start sm:gap-2">
                  <span className="text-sm font-medium text-primary">Example {index + 1}</span>
                  <span className="text-sm text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100 sm:opacity-100 sm:min-h-[44px]">Use this prompt →</span>
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed m-0 sm:text-sm sm:leading-relaxed">{example}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="p-4 bg-secondary rounded-md border-l-4 border-primary">
        <h4 className="text-base font-semibold text-foreground m-0 mb-3">💡 Tips for effective prompts:</h4>
        <ul className="m-0 pl-5 flex flex-col gap-2">
          <li className="text-sm text-muted-foreground leading-relaxed">Be specific about visual elements, camera angles, and transitions</li>
          <li className="text-sm text-muted-foreground leading-relaxed">Describe the mood, tone, and pacing you want</li>
          <li className="text-sm text-muted-foreground leading-relaxed">Include details about colors, lighting, and aesthetic preferences</li>
          <li className="text-sm text-muted-foreground leading-relaxed">Mention any text overlays, captions, or key messages</li>
          <li className="text-sm text-muted-foreground leading-relaxed">Specify the target audience and desired emotional impact</li>
        </ul>
      </div>
    </div>
  );
};
