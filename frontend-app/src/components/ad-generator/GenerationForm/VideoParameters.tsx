import React from 'react';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Clock, Monitor } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { VideoStyle, MusicStyle } from '@/types/ad-generator/form';

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

const DURATION_OPTIONS = [
  { value: 15, label: '15 seconds', description: 'Quick, punchy ads for social media' },
  { value: 30, label: '30 seconds', description: 'Standard ad length, balanced content' },
  { value: 45, label: '45 seconds', description: 'Extended storytelling opportunity' },
  { value: 60, label: '60 seconds', description: 'Full-length ad with detailed narrative' },
];

const ASPECT_RATIO_OPTIONS = [
  { value: '16:9', label: '16:9 Landscape', description: 'YouTube, websites', icon: '▬' },
  { value: '9:16', label: '9:16 Portrait', description: 'TikTok, Reels', icon: '▮' },
  { value: '1:1', label: '1:1 Square', description: 'Instagram, Facebook', icon: '■' },
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
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">
          Video Configuration
        </h2>
        <p className="text-muted-foreground">
          Choose the technical parameters for your video.
        </p>
      </div>

      {/* Duration Selection */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Duration
          </CardTitle>
          <CardDescription>
            Choose how long your video should be
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {DURATION_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => onDurationChange(option.value as 15 | 30 | 45 | 60)}
                className={cn(
                  'flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all text-center',
                  duration === option.value
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/50 hover:bg-muted/50'
                )}
              >
                <span className={cn(
                  'text-2xl font-bold',
                  duration === option.value ? 'text-primary' : 'text-foreground'
                )}>
                  {option.value}s
                </span>
                <span className="text-xs text-muted-foreground">{option.description}</span>
              </button>
            ))}
          </div>
          {errors.duration && (
            <p className="text-sm text-destructive mt-2">{errors.duration}</p>
          )}
        </CardContent>
      </Card>

      {/* Aspect Ratio Selection */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <Monitor className="h-4 w-4" />
            Aspect Ratio
          </CardTitle>
          <CardDescription>
            Choose the format that matches your distribution platform
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-3">
            {ASPECT_RATIO_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => onAspectRatioChange(option.value as '16:9' | '9:16' | '1:1')}
                className={cn(
                  'flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all',
                  aspectRatio === option.value
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/50 hover:bg-muted/50'
                )}
              >
                <span className={cn(
                  'text-2xl',
                  aspectRatio === option.value ? 'text-primary' : 'text-muted-foreground'
                )}>
                  {option.icon}
                </span>
                <span className={cn(
                  'font-medium',
                  aspectRatio === option.value ? 'text-primary' : 'text-foreground'
                )}>
                  {option.label}
                </span>
                <span className="text-xs text-muted-foreground">{option.description}</span>
              </button>
            ))}
          </div>
          {errors.aspectRatio && (
            <p className="text-sm text-destructive mt-2">{errors.aspectRatio}</p>
          )}
        </CardContent>
      </Card>

    </div>
  );
};
