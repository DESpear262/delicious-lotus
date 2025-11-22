import { useState } from 'react';
import { z } from 'zod';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Input } from './ui/input';
import { Label } from './ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { Button } from './ui/button';

// Validation schema
const projectFormSchema = z.object({
  name: z.string().min(1, 'Project name is required').max(100, 'Name must be less than 100 characters'),
  description: z.string().max(500, 'Description must be less than 500 characters').optional(),
  fps: z.number().int().positive(),
  resolution: z.object({
    width: z.number().int().positive(),
    height: z.number().int().positive(),
  }),
  aspectRatio: z.enum(['16:9', '9:16', '1:1', '4:3']),
});

export type ProjectFormData = z.infer<typeof projectFormSchema>;

interface NewProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreateProject: (data: ProjectFormData) => void;
}

const resolutionOptions = [
  { label: '1920x1080 (Full HD)', value: '1920x1080', width: 1920, height: 1080 },
  { label: '1280x720 (HD)', value: '1280x720', width: 1280, height: 720 },
  { label: '3840x2160 (4K)', value: '3840x2160', width: 3840, height: 2160 },
];

const fpsOptions = [
  { label: '24 fps', value: 24 },
  { label: '30 fps', value: 30 },
  { label: '60 fps', value: 60 },
];

const aspectRatioOptions = [
  { label: '16:9 (Widescreen)', value: '16:9' as const },
  { label: '9:16 (Vertical)', value: '9:16' as const },
  { label: '1:1 (Square)', value: '1:1' as const },
  { label: '4:3 (Standard)', value: '4:3' as const },
];

export function NewProjectDialog({ open, onOpenChange, onCreateProject }: NewProjectDialogProps) {
  const [formData, setFormData] = useState<ProjectFormData>({
    name: '',
    description: '',
    fps: 30,
    resolution: { width: 1920, height: 1080 },
    aspectRatio: '16:9',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Validate form data
    const result = projectFormSchema.safeParse(formData);

    if (!result.success) {
      const fieldErrors: Record<string, string> = {};
      result.error.issues.forEach((err) => {
        if (err.path[0]) {
          fieldErrors[err.path[0] as string] = err.message;
        }
      });
      setErrors(fieldErrors);
      return;
    }

    // Clear errors and call create handler
    setErrors({});
    onCreateProject(result.data);

    // Reset form
    setFormData({
      name: '',
      description: '',
      fps: 30,
      resolution: { width: 1920, height: 1080 },
      aspectRatio: '16:9',
    });
  };

  const handleCancel = () => {
    // Reset form and errors
    setFormData({
      name: '',
      description: '',
      fps: 30,
      resolution: { width: 1920, height: 1080 },
      aspectRatio: '16:9',
    });
    setErrors({});
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create New Project</DialogTitle>
            <DialogDescription>
              Set up your video editing project with custom settings.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Project Name */}
            <div className="grid gap-2">
              <Label htmlFor="name">
                Project Name <span className="text-red-500">*</span>
              </Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="My Awesome Video"
                className={errors.name ? 'border-red-500' : ''}
              />
              {errors.name && <p className="text-sm text-red-500">{errors.name}</p>}
            </div>

            {/* Description */}
            <div className="grid gap-2">
              <Label htmlFor="description">Description</Label>
              <textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Describe your project..."
                rows={3}
                className="flex w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm ring-offset-zinc-950 placeholder:text-zinc-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              />
              {errors.description && <p className="text-sm text-red-500">{errors.description}</p>}
            </div>

            {/* FPS */}
            <div className="grid gap-2">
              <Label htmlFor="fps">Frame Rate</Label>
              <Select
                value={formData.fps.toString()}
                onValueChange={(value) => setFormData({ ...formData, fps: parseInt(value) })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select frame rate" />
                </SelectTrigger>
                <SelectContent>
                  {fpsOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value.toString()}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Resolution */}
            <div className="grid gap-2">
              <Label htmlFor="resolution">Resolution</Label>
              <Select
                value={`${formData.resolution.width}x${formData.resolution.height}`}
                onValueChange={(value) => {
                  const option = resolutionOptions.find((opt) => opt.value === value);
                  if (option) {
                    setFormData({
                      ...formData,
                      resolution: { width: option.width, height: option.height },
                    });
                  }
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select resolution" />
                </SelectTrigger>
                <SelectContent>
                  {resolutionOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Aspect Ratio */}
            <div className="grid gap-2">
              <Label htmlFor="aspectRatio">Aspect Ratio</Label>
              <Select
                value={formData.aspectRatio}
                onValueChange={(value) =>
                  setFormData({ ...formData, aspectRatio: value as ProjectFormData['aspectRatio'] })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select aspect ratio" />
                </SelectTrigger>
                <SelectContent>
                  {aspectRatioOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleCancel}>
              Cancel
            </Button>
            <Button type="submit">Create Project</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
