import React, { useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { PipelineCard } from '../../components/ad-generator/PipelineCard';
import { PIPELINES, type Pipeline } from '../../types/ad-generator/pipeline';
import { useProjectStore } from '@/contexts/StoreContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Clock, ArrowRight, History } from 'lucide-react';

/**
 * PipelineSelection Page Component
 *
 * Home page that displays available video generation pipelines.
 * Users can select between Ad Creative and Music Video pipelines.
 * Also lists recently modified projects for quick resumption.
 */
export const PipelineSelection: React.FC = () => {
  const navigate = useNavigate();
  const fetchProjects = useProjectStore((s) => s.fetchProjects);
  const projectsMap = useProjectStore((s) => s.projects);
  const addProject = useProjectStore((s) => s.addProject);
  
  const pipelines = Object.values(PIPELINES);

  useEffect(() => {
    // Fetch projects on mount to populate resume list
    // We fetch all for now, filtering in memory
    fetchProjects().catch(console.error);
  }, [fetchProjects]);

  const recentProjects = useMemo(() => {
    return Array.from(projectsMap.values())
      .filter(p => ['ad-creative', 'music-video'].includes(p.type))
      .sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime())
      .slice(0, 6); // Show top 6
  }, [projectsMap]);

  const handlePipelineSelect = async (pipeline: Pipeline) => {
    if (pipeline.id === 'ad-creative') {
      try {
        // Create new project immediately
        const projectId = await addProject({
          name: `Ad Campaign ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`,
          description: 'New ad creative campaign',
          type: 'ad-creative'
        });
        
        if (pipeline.route) {
           navigate(`${pipeline.route}?projectId=${projectId}`);
        }
      } catch (error) {
        console.error('Failed to create project:', error);
        // Fallback navigation if creation fails (though form handles creation too as fallback)
        if (pipeline.route) navigate(pipeline.route);
      }
    } else {
      // Default behavior for other pipelines
      if (pipeline.route) navigate(pipeline.route);
    }
  };

  const handleResume = (project: any) => {
    if (project.type === 'ad-creative') {
      navigate(`/ad-generator/create/ad-creative?projectId=${project.id}`);
    }
    // Handle other types as they are implemented
  };

  return (
    <div className="flex flex-col gap-8 p-8 max-w-[1400px] mx-auto min-h-[calc(100vh-200px)] md:p-6 md:gap-6 sm:p-4 sm:gap-5">
      <div className="text-center animate-in slide-in-from-top-5 duration-500 ease-out">
        <h1 className="text-4xl font-bold text-foreground mb-4 leading-tight md:text-3xl sm:text-2xl">
          Choose Your Video Pipeline
        </h1>
        <p className="text-lg text-muted-foreground m-0 leading-relaxed md:text-base sm:text-sm">
          Select a pipeline to start creating a new project, or resume a recent one.
        </p>
      </div>

      {/* Pipelines Grid */}
      <div className="grid grid-cols-[repeat(auto-fit,minmax(400px,1fr))] gap-8 animate-in fade-in slide-in-from-bottom-8 duration-700 delay-200 fill-mode-both lg:grid-cols-[repeat(auto-fit,minmax(350px,1fr))] lg:gap-6 md:grid-cols-1 md:gap-6 sm:gap-5">
        {pipelines.map((pipeline) => (
          <PipelineCard 
            key={pipeline.id} 
            pipeline={pipeline} 
            onClick={handlePipelineSelect}
          />
        ))}
      </div>

      {/* Recent Projects Section */}
      {recentProjects.length > 0 && (
        <div className="animate-in fade-in slide-in-from-bottom-12 duration-700 delay-300 fill-mode-both mt-8">
           <div className="flex items-center gap-2 mb-6">
              <History className="h-5 w-5 text-primary" />
              <h2 className="text-2xl font-bold text-foreground">Recent Projects</h2>
           </div>
           
           <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {recentProjects.map((project) => (
                <Card key={project.id} className="flex flex-col hover:border-primary/50 transition-colors group">
                    <CardHeader className="pb-3">
                        <div className="flex justify-between items-start gap-2">
                           <CardTitle className="line-clamp-1 text-base">{project.name}</CardTitle>
                           <span className="text-[10px] uppercase bg-muted px-1.5 py-0.5 rounded-sm text-muted-foreground whitespace-nowrap">
                             {project.type}
                           </span>
                        </div>
                        <CardDescription className="line-clamp-1 text-xs">
                            {project.description || 'No description'}
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="flex-1 py-2">
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Clock className="h-3 w-3" />
                            <span>{project.updatedAt.toLocaleDateString()}</span>
                        </div>
                    </CardContent>
                    <CardFooter className="pt-2 pb-4 px-4">
                        <Button 
                            variant="ghost" 
                            size="sm"
                            className="w-full justify-between group-hover:bg-primary group-hover:text-primary-foreground transition-colors"
                            onClick={() => handleResume(project)}
                        >
                            Resume
                            <ArrowRight className="h-4 w-4" />
                        </Button>
                    </CardFooter>
                </Card>
              ))}
           </div>
        </div>
      )}

      <div className="text-center pt-8 animate-in fade-in duration-1000 delay-500 fill-mode-both md:pt-4">
        <p className="text-sm text-muted-foreground/80 m-0 leading-relaxed">
          More pipelines coming soon! Each pipeline is optimized for specific video types and use
          cases.
        </p>
      </div>
    </div>
  );
};