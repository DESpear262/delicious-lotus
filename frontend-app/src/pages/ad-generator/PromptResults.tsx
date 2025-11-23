import { useEffect, useMemo, useState, useCallback, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ArrowLeft, Sparkles, ChevronRight, Download, Trash2, ExternalLink } from 'lucide-react';
import type { VideoPromptResponse } from '@/services/ad-generator/types';
import { generateImage, generateVideo, generateAudio } from '@/services/aiGenerationService';
import { PromptInput } from '@/components/ai-generation/PromptInput';
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from '@/components/ui/resizable';
import { useAIGenerationStore, useMediaStore, useProjectStore } from '@/contexts/StoreContext';
import { MediaGenerationSkeleton } from '@/components/media/MediaGenerationSkeleton';
import { MediaAssetCard } from '@/components/media/MediaAssetCard';
import { MediaPreviewModal } from '@/components/media/MediaPreviewModal';
import type { GenerationType, QualityTier, MediaAsset } from '@/types/stores';

interface LocationState {
  promptResult?: VideoPromptResponse;
  aspectRatio?: '16:9' | '9:16' | '1:1' | '4:3';
}

export function PromptResults() {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as LocationState | undefined;
  
  // Project Store
  const compositionConfig = useProjectStore((s) => s.compositionConfig);
  const updateCompositionConfig = useProjectStore((s) => s.updateCompositionConfig);
  const saveProject = useProjectStore((s) => s.saveProject);
  const lastAssetRefreshRef = useRef<number>(0);

  // Get stored prompt result from project config or fallback to local/session state
  const storedPromptResult = compositionConfig?.adWizard?.promptResult;
  const [promptResult, setPromptResult] = useState<VideoPromptResponse | null>(
    state?.promptResult || storedPromptResult || null
  );
  
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});
  const [previewAsset, setPreviewAsset] = useState<MediaAsset | null>(null);
  
  // Get generated assets list from project config
  // We use a Set for efficient lookup, but persist as array
  const generatedGenIds = useMemo(() => {
    return new Set<string>(compositionConfig?.generated_assets || []);
  }, [compositionConfig?.generated_assets]);

  // Stores
  const queueGeneration = useAIGenerationStore((s) => s.queueGeneration);
  const updateGenerationStatus = useAIGenerationStore((s) => s.updateGenerationStatus);
  const activeGenerationsMap = useAIGenerationStore((s) => s.activeGenerations);
  const completingGenerationsMap = useAIGenerationStore((s) => s.completingGenerations);
  const generationHistory = useAIGenerationStore((s) => s.generationHistory);
  const moveToCompleting = useAIGenerationStore((s) => s.moveToCompleting);
  const clearCompletingGeneration = useAIGenerationStore((s) => s.clearCompletingGeneration);
  const addToHistory = useAIGenerationStore((s) => s.addToHistory);
  
  const assets = useMediaStore((s) => s.assets);
  const loadAssets = useMediaStore((s) => s.loadAssets);
  const deleteAsset = useMediaStore((s) => s.deleteAsset);
  const updateAsset = useMediaStore((s) => s.updateAsset);
  const selectedAssetIds = useMediaStore((s) => s.selectedAssetIds);
  const selectAsset = useMediaStore((s) => s.selectAsset);

  // Restore prompt result from session storage if needed (legacy fallback)
  useEffect(() => {
    if (!promptResult) {
      const stored = sessionStorage.getItem('promptResult');
      if (stored) {
        try {
          setPromptResult(JSON.parse(stored));
        } catch (error) {
          console.warn('Failed to parse stored prompt result', error);
        }
      }
    }
  }, [promptResult]);

  const clips = useMemo(() => promptResult?.content || [], [promptResult]);
  
  // Get aspect ratio from project config or state or default
  const defaultAspectRatio = 
    state?.aspectRatio || 
    compositionConfig?.adWizard?.formData?.aspectRatio || 
    '16:9';

  // Handle Generation Logic
  const handleGenerate = useCallback(
    async (
      params: {
        prompt: string
        type: GenerationType
        qualityTier: QualityTier
        aspectRatio: '16:9' | '9:16' | '1:1' | '4:3'
        model: string
        duration?: number
        resolution?: string
        imageInput?: string | string[]
        audioInput?: string
        advancedParams?: Record<string, any>
      },
      index: number
    ) => {
      try {
        // Queue generation in store
        const generationId = queueGeneration({
          type: params.type,
          prompt: params.prompt,
          qualityTier: params.qualityTier,
          aspectRatio: params.aspectRatio,
          metadata: {
            source: 'prompt-results',
            clipIndex: index,
            model: params.model,
            duration: params.duration
          }
        });

        // Save generation ID to project config for persistence
        const currentGenerated = compositionConfig?.generated_assets || [];
        updateCompositionConfig({
            generated_assets: [...currentGenerated, generationId]
        });
        // Trigger save (autosave will pick it up)
        saveProject().catch(err => console.error("Failed to auto-save project:", err));

        // Update status to generating
        updateGenerationStatus(generationId, 'generating');

        // Call API
        let response;
        if (params.type === 'image') {
          response = await generateImage({
            prompt: params.prompt,
            qualityTier: params.qualityTier,
            aspectRatio: params.aspectRatio,
            model: params.model,
            image_input: params.imageInput,
            ...params.advancedParams,
          });
        } else if (params.type === 'video') {
           // Video generation params mapping (similar to AIGenerationPanel)
           let size = '1280*720';
           let resolution = params.resolution || '1080p';

           switch (params.aspectRatio) {
            case '16:9': size = '1280*720'; if(!params.resolution) resolution='1080p'; break;
            case '9:16': size = '720*1280'; if(!params.resolution) resolution='1080p'; break;
            case '1:1': size = '1280*720'; if(!params.resolution) resolution='1080p'; break; // Fallback
            case '4:3': size = '1280*720'; if(!params.resolution) resolution='1080p'; break; // Fallback
            default: size = '1280*720';
           }

          response = await generateVideo({
            prompt: params.prompt,
            size,
            duration: params.duration,
            model: params.model,
            aspectRatio: params.aspectRatio,
            resolution,
            image: Array.isArray(params.imageInput) ? params.imageInput[0] : params.imageInput,
            ...params.advancedParams,
          });
        } else if (params.type === 'audio') {
          response = await generateAudio({
            prompt: params.prompt,
            duration: params.duration,
            model: params.model,
            ...params.advancedParams,
          });
        }

        // Update with Job ID from API
        if (response?.job_id) {
          updateGenerationStatus(generationId, 'generating', { jobId: response.job_id });
        }

      } catch (error: any) {
        console.error('Generation failed:', error);
        // Store handles failure updates if needed, but we can also explicitly fail it here if we had the ID
        // Since we queueGeneration first, we rely on the UI/Store to handle state.
        // But if API call fails immediately, we should probably mark it failed in store.
        // We don't have the ID easily accessible in catch block unless we wrap it differently.
        // For now, rely on store timeout or manual error handling if needed.
      }
    },
    [queueGeneration, updateGenerationStatus, compositionConfig, updateCompositionConfig, saveProject]
  );

  // Check for completed generations to refresh assets
  useEffect(() => {
    const syncCompletedGenerations = async () => {
      const completedGens = Array.from(completingGenerationsMap.values()).filter((g) =>
        generatedGenIds.has(g.id)
      );

      if (completedGens.length === 0) return;

      let needsRefresh = false;

      completedGens.forEach((gen) => {
        const alreadyInHistory = generationHistory.some((h) => h.request.id === gen.id);
        if (alreadyInHistory) {
          clearCompletingGeneration(gen.id);
          return;
        }

        if (!gen.jobId) {
          needsRefresh = true;
          return;
        }

        const matchingAsset = Array.from(assets.values()).find(
          (asset) => asset.metadata?.replicate_job_id === gen.jobId
        );

        if (matchingAsset) {
          addToHistory(gen, matchingAsset.id);
          clearCompletingGeneration(gen.id);
        } else {
          needsRefresh = true;
        }
      });

      // Avoid spamming the API: only refresh if we still don't have matches and
      // we haven't refreshed very recently.
      if (needsRefresh && Date.now() - lastAssetRefreshRef.current > 1500) {
        lastAssetRefreshRef.current = Date.now();
        try {
          await loadAssets();
        } catch (error) {
          console.error('[PromptResults] Failed to refresh assets', error);
        }
      }
    };

    void syncCompletedGenerations();
  }, [
    assets,
    generationHistory,
    completingGenerationsMap,
    generatedGenIds,
    addToHistory,
    clearCompletingGeneration,
    loadAssets,
  ]);


  // Filter Content for Right Panel
  const activeSessionGens = useMemo(() => {
    return Array.from(activeGenerationsMap.values())
      .filter(g => generatedGenIds.has(g.id))
      .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
  }, [activeGenerationsMap, generatedGenIds]);

  const completingSessionGens = useMemo(() => {
    return Array.from(completingGenerationsMap.values())
       .filter(g => generatedGenIds.has(g.id));
  }, [completingGenerationsMap, generatedGenIds]);

  const completedSessionHistory = useMemo(() => {
    const filtered = generationHistory.filter(g => generatedGenIds.has(g.request.id));
    console.log('[PromptResults] History Debug:', {
        totalHistory: generationHistory.length,
        sessionIds: Array.from(generatedGenIds),
        filteredCount: filtered.length,
        firstMatch: filtered[0]
    });
    return filtered;
  }, [generationHistory, generatedGenIds]);

  // Map history items to assets
  const generatedAssets = useMemo(() => {
    const mapped = completedSessionHistory.map(h => {
       if (h.assetId) {
         const asset = assets.get(h.assetId);
         if (!asset) console.warn(`[PromptResults] Asset ${h.assetId} in history but not in store`);
         return asset;
       }
       console.warn(`[PromptResults] History item ${h.id} has no assetId`);
       return undefined;
    }).filter(Boolean) as MediaAsset[];

    // Deduplicate assets by ID to prevent duplicates in UI
    const uniqueAssets = Array.from(new Map(mapped.map(item => [item.id, item])).values());

    console.log('[PromptResults] Generated Assets:', uniqueAssets.length);
    return uniqueAssets;
  }, [completedSessionHistory, assets]);

  // Combine active skeletons and real assets
  // We show active/completing as Skeletons
  // We show generatedAssets as Cards
  const visibleGenerations = [...activeSessionGens, ...completingSessionGens];


  if (!promptResult) {
    return (
      <div className="min-h-screen bg-background pb-12">
         {/* Empty state ... same as before */}
         <div className="mx-auto max-w-4xl px-4 py-10">
           <Button variant="ghost" onClick={() => navigate(-1)} className="gap-2 mb-6">
              <ArrowLeft className="h-4 w-4" /> Back
            </Button>
            <Card>
              <CardContent className="py-10 text-center text-muted-foreground">
                No prompt results found.
              </CardContent>
            </Card>
         </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-background overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-background z-10">
        <div className="flex items-center gap-4">
           <Button variant="ghost" onClick={() => navigate(-1)} className="gap-2">
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
            <div>
              <h1 className="text-xl font-semibold text-foreground flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                Generated Clip Prompts
              </h1>
              <p className="text-xs text-muted-foreground">
                 {clips.length} clips • {defaultAspectRatio}
              </p>
            </div>
        </div>
        <div className="flex gap-2">
           {/* Actions like "Go to Media Library" could go here */}
           <Button variant="outline" size="sm" onClick={() => navigate('/media')}>
             Media Library
           </Button>
        </div>
      </header>

      <ResizablePanelGroup direction="horizontal" className="flex-1 h-full">
        {/* Left Panel: Prompts */}
        <ResizablePanel defaultSize={50} minSize={30} className="bg-background">
           <div className="h-full overflow-y-auto p-6 space-y-4">
              {clips.map((clip, index) => (
                <Collapsible
                  key={index}
                  open={expanded[index] || false}
                  onOpenChange={(open) => setExpanded((prev) => ({ ...prev, [index]: open }))}
                >
                  <CollapsibleTrigger asChild>
                    <Card className="w-full border-border text-left cursor-pointer hover:border-primary/50 transition-colors">
                      <CardHeader className="flex flex-row items-center justify-between gap-3 py-4">
                        <div className="space-y-1">
                          <CardTitle className="text-base text-foreground">Clip {index + 1}</CardTitle>
                          <div className="flex gap-2 text-xs text-muted-foreground">
                             <span>{clip.length}s</span>
                             <span className="bg-primary/10 text-primary px-1.5 rounded">
                               {defaultAspectRatio}
                             </span>
                          </div>
                        </div>
                        <ChevronRight
                          className={`h-4 w-4 text-muted-foreground transition-transform ${
                            expanded[index] ? 'rotate-90' : ''
                          }`}
                        />
                      </CardHeader>
                    </Card>
                  </CollapsibleTrigger>
                  <CollapsibleContent className="mt-2">
                    <Card className="border-border bg-muted/20">
                      <CardContent className="pt-4">
                        <PromptInput
                          defaultType="image"
                          defaultPrompt={clip.image_prompt}
                          defaultAspectRatio={defaultAspectRatio}
                          autoPrompts={{ image: clip.image_prompt, video: clip.video_prompt }}
                          isPending={false} // Pending state is handled by store/toast usually, but we could link it to activeGenerations
                          onGenerate={(params) => handleGenerate(params, index)}
                        />
                      </CardContent>
                    </Card>
                  </CollapsibleContent>
                </Collapsible>
              ))}

              {/* Raw Response Debug (optional/collapsed) */}
              <Collapsible>
                 <CollapsibleTrigger asChild>
                    <Button variant="ghost" size="sm" className="text-muted-foreground text-xs w-full justify-start">
                       Show Raw Prompt Data
                    </Button>
                 </CollapsibleTrigger>
                 <CollapsibleContent>
                    <pre className="mt-2 rounded-lg bg-muted/60 p-4 text-[10px] text-foreground overflow-x-auto border border-border">
                      {JSON.stringify(promptResult, null, 2)}
                    </pre>
                 </CollapsibleContent>
              </Collapsible>
           </div>
        </ResizablePanel>

        <ResizableHandle withHandle />

        {/* Right Panel: Generated Results */}
        <ResizablePanel defaultSize={50} minSize={30} className="bg-muted/10">
           <div className="h-full flex flex-col">
              <div className="p-4 border-b border-border bg-background/50 backdrop-blur">
                 <h2 className="font-semibold text-foreground">Session Results</h2>
                 <p className="text-xs text-muted-foreground">
                   Media generated in this session
                 </p>
              </div>
              
              <div className="flex-1 overflow-y-auto p-6">
                 {visibleGenerations.length === 0 && generatedAssets.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center text-muted-foreground p-8">
                       <Sparkles className="h-12 w-12 mb-4 opacity-20" />
                       <p>No content generated yet.</p>
                       <p className="text-sm">Select a clip on the left and click Generate.</p>
                    </div>
                 ) : (
                    <div className="grid grid-cols-2 gap-4">
                       {/* Active/Completing Skeletons */}
                       {visibleGenerations.map(gen => (
                          <MediaGenerationSkeleton key={gen.id} />
                       ))}
                       
                       {/* Completed Assets */}
                       {generatedAssets.map((asset) => {
                          if (!asset) return null;
                          return (
                            <MediaAssetCard
                              key={asset.id}
                              asset={asset}
                              isSelected={selectedAssetIds.includes(asset.id)}
                              onClick={() => selectAsset(asset.id, false)} // Basic selection
                              onDelete={() => deleteAsset(asset.id)}
                              onPreview={() => setPreviewAsset(asset)}
                            />
                          );
                       })}
                    </div>
                 )}
              </div>
           </div>
        </ResizablePanel>
      </ResizablePanelGroup>

      {/* Media Preview Modal */}
      <MediaPreviewModal
        asset={previewAsset}
        isOpen={!!previewAsset}
        onClose={() => setPreviewAsset(null)}
        onUpdate={(updatedAsset) => {
          updateAsset(updatedAsset.id, updatedAsset);
          setPreviewAsset(updatedAsset);
        }}
      />
    </div>
  );
}

export default PromptResults;
