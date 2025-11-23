import { useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProjectStore } from '@/contexts/StoreContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus, Clock, ArrowRight, Film } from 'lucide-react';

export function Home() {
  const navigate = useNavigate();
  const fetchProjects = useProjectStore((s) => s.fetchProjects);
  const projectsMap = useProjectStore((s) => s.projects);
  const addProject = useProjectStore((s) => s.addProject);
  const isLoading = useProjectStore((s) => s.isLoading);

  useEffect(() => {
    fetchProjects({ type: 'ad-creative' });
  }, [fetchProjects]);

  const adProjects = useMemo(() => {
    return Array.from(projectsMap.values())
      .filter((p) => p.type === 'ad-creative')
      .sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime());
  }, [projectsMap]);

  const handleCreateNew = async () => {
    try {
      const projectId = await addProject({
        name: `Ad Campaign ${new Date().toLocaleDateString()}`,
        description: 'New ad creative campaign',
        type: 'ad-creative',
      });
      navigate(`/ad-generator/create/ad-creative?projectId=${projectId}`);
    } catch (error) {
      console.error('Failed to create project', error);
    }
  };

  const handleResume = (projectId: string) => {
    navigate(`/ad-generator/create/ad-creative?projectId=${projectId}`);
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-5xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">Ad Generator</h1>
            <p className="text-muted-foreground mt-1">
              Create and manage your video ad campaigns.
            </p>
          </div>
          <Button onClick={handleCreateNew} size="lg" className="gap-2">
            <Plus className="h-4 w-4" />
            New Campaign
          </Button>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {/* Create New Card (Alternative) */}
            <Card 
                className="flex flex-col items-center justify-center border-dashed border-2 border-muted-foreground/20 hover:border-primary/50 hover:bg-accent/5 cursor-pointer transition-all min-h-[200px]"
                onClick={handleCreateNew}
            >
                <div className="rounded-full bg-primary/10 p-4 mb-4">
                    <Plus className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-semibold text-lg">Create New Campaign</h3>
                <p className="text-sm text-muted-foreground">Start from scratch</p>
            </Card>

            {/* Project List */}
            {adProjects.map((project) => (
                <Card key={project.id} className="flex flex-col hover:border-primary/50 transition-colors group">
                    <CardHeader>
                        <CardTitle className="line-clamp-1">{project.name}</CardTitle>
                        <CardDescription className="line-clamp-2 min-h-[2.5em]">
                            {project.description || 'No description'}
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="flex-1">
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Clock className="h-3 w-3" />
                            <span>Last updated {project.updatedAt.toLocaleDateString()}</span>
                        </div>
                    </CardContent>
                    <CardFooter className="border-t bg-muted/10 p-4">
                        <Button 
                            variant="ghost" 
                            className="w-full justify-between group-hover:bg-primary group-hover:text-primary-foreground transition-colors"
                            onClick={() => handleResume(project.id)}
                        >
                            Resume
                            <ArrowRight className="h-4 w-4" />
                        </Button>
                    </CardFooter>
                </Card>
            ))}

            {!isLoading && adProjects.length === 0 && (
                <div className="col-span-full text-center py-12 text-muted-foreground">
                    <Film className="h-12 w-12 mx-auto mb-4 opacity-20" />
                    <p>No ad campaigns found. Create one to get started.</p>
                </div>
            )}
        </div>
      </div>
    </div>
  );
}