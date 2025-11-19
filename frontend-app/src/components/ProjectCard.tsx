import { memo } from 'react';
import { Trash2, Play } from 'lucide-react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import type { ProjectMetadata } from '../types/stores';

interface ProjectCardProps {
  project: ProjectMetadata;
  onOpen: (projectId: string) => void;
  onDelete: (projectId: string) => void;
}

const ProjectCard = memo(({ project, onOpen, onDelete }: ProjectCardProps) => {
  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    }).format(date);
  };

  const handleCardClick = (e: React.MouseEvent) => {
    // Prevent card click if clicking on buttons
    if ((e.target as HTMLElement).closest('button')) {
      return;
    }
    onOpen(project.id);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete(project.id);
  };

  const handleOpenClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onOpen(project.id);
  };

  return (
    <Card
      className="group cursor-pointer overflow-hidden border-zinc-800 bg-zinc-900 transition-all hover:border-zinc-700 hover:shadow-lg hover:shadow-blue-500/10"
      onClick={handleCardClick}
    >
      {/* Thumbnail */}
      <div className="relative aspect-video w-full overflow-hidden bg-zinc-800">
        {project.thumbnailUrl ? (
          <img
            src={project.thumbnailUrl}
            alt={project.name}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center">
            <Play className="h-12 w-12 text-zinc-600" />
          </div>
        )}

        {/* Overlay on hover */}
        <div className="absolute inset-0 bg-black/60 opacity-0 transition-opacity group-hover:opacity-100 flex items-center justify-center gap-2">
          <Button
            size="sm"
            onClick={handleOpenClick}
            className="gap-1"
          >
            <Play className="h-4 w-4" />
            Open
          </Button>
          <Button
            size="sm"
            variant="destructive"
            onClick={handleDelete}
            className="gap-1"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <h3 className="mb-1 truncate text-lg font-semibold text-zinc-100">
          {project.name}
        </h3>

        {project.description && (
          <p className="mb-3 line-clamp-2 text-sm text-zinc-400">
            {project.description}
          </p>
        )}

        <div className="flex items-center justify-between text-xs text-zinc-500">
          <span>Modified {formatDate(project.updatedAt)}</span>
          {/* Duration placeholder - would need to be stored in metadata */}
          {/* <span>{formatDuration(0)}</span> */}
        </div>
      </div>
    </Card>
  );
});

ProjectCard.displayName = 'ProjectCard';

export { ProjectCard };
