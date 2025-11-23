import { useEffect, useMemo, useState, useCallback, useRef, useContext } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ArrowLeft, Sparkles, ChevronRight, Download, Trash2, ExternalLink } from 'lucide-react';
import type { VideoPromptResponse } from '@/services/ad-generator/types';
import { generateImage, generateVideo, generateAudio } from '@/services/aiGenerationService';
import { PromptInput, MODEL_CONFIGS, MODELS_BY_TYPE } from '@/components/ai-generation/PromptInput';
import { Input } from '@/components/ui/input';
import { Search, Filter } from 'lucide-react';
import { SimpleTimeline, type TimelineItem } from '@/components/ad-generator/SimpleTimeline';
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from '@/components/ui/resizable';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useAIGenerationStore, useMediaStore, useProjectStore, useUiStore, TimelineStoreContext } from '@/contexts/StoreContext';
import axios from 'axios';
import { MediaGenerationSkeleton } from '@/components/media/MediaGenerationSkeleton';
import { MediaAssetCard } from '@/components/media/MediaAssetCard';
import { MediaPreviewModal } from '@/components/media/MediaPreviewModal';
import type { GenerationType, QualityTier, MediaAsset, Clip } from '@/types/stores';
import { generateUUID } from '@/utils/uuid';

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
  
  // Access Timeline Store directly for advanced editor handoff
  const timelineStore = useContext(TimelineStoreContext);

  // Get stored prompt result from project config or fallback to local/session state
  const storedPromptResult = compositionConfig?.adWizard?.promptResult;
  const [promptResult, setPromptResult] = useState<VideoPromptResponse | null>(
    state?.promptResult || storedPromptResult || null
  );

  const [expanded, setExpanded] = useState<Record<number, boolean>>({});
  const [previewAsset, setPreviewAsset] = useState<MediaAsset | null>(null);
  const [activeTab, setActiveTab] = useState<'image' | 'video'>('image');
  const [selectedModelId, setSelectedModelId] = useState<string>('flux-schnell');

  // Timeline State
  const [timelineClips, setTimelineClips] = useState<TimelineItem[]>(() => {
      // Initialize from persisted config
      const saved = compositionConfig?.adWizard?.timelineClips;
      if (Array.isArray(saved)) {
          return saved;
      }
      return [];
  });
  
  const [isExporting, setIsExporting] = useState(false);

  // Filter State
  const [filterType, setFilterType] = useState<'all' | 'image' | 'video'>('all');
  const [filterText, setFilterText] = useState<string>('');
  
  // Persist timeline changes to project store
  useEffect(() => {
      // Only update if changed to avoid loops, although object ref check might trigger.
      // We rely on zustand/immer to handle diffs or just overwrite.
      // We only want to update if the content is actually different than what's in store.
      // But checking deep equality is expensive.
      // Given this runs on setTimelineClips which is user interaction, it's fine.
      
      if (compositionConfig?.adWizard?.timelineClips === timelineClips) return;
      
      updateCompositionConfig({
          adWizard: {
              ...compositionConfig?.adWizard,
              timelineClips
          }
      });
      
      // Note: We don't auto-save to backend on every drag for performance, 
      // allowing the global autosave timer to pick it up (ProjectStore has debounced autosave).
      // However, explicit save is safer if user navigates away immediately.
      // projectStore handles debounce.
  }, [timelineClips, updateCompositionConfig, compositionConfig?.adWizard]);

  // Update selected model when tab changes
  useEffect(() => {
    if (activeTab === 'image') {
      setSelectedModelId('flux-schnell');
    } else {
      setSelectedModelId('wan-video-t2v');
    }
  }, [activeTab]);

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

  const addToast = useUiStore((s) => s.addToast);

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
        skipStoreUpdate?: boolean
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
        if (!params.skipStoreUpdate) {
          const currentGenerated = compositionConfig?.generated_assets || [];
          updateCompositionConfig({
            generated_assets: [...currentGenerated, generationId]
          });
          // Trigger save (autosave will pick it up)
          saveProject().catch(err => console.error("Failed to auto-save project:", err));
        }

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
            case '16:9': size = '1280*720'; if (!params.resolution) resolution = '1080p'; break;
            case '9:16': size = '720*1280'; if (!params.resolution) resolution = '1080p'; break;
            case '1:1': size = '1280*720'; if (!params.resolution) resolution = '1080p'; break; // Fallback
            case '4:3': size = '1280*720'; if (!params.resolution) resolution = '1080p'; break; // Fallback
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

        return generationId;
      } catch (error: any) {
        console.error('Generation failed:', error);
        return undefined;
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

  // Filter Logic for Results
  const filteredAssets = useMemo(() => {
    return generatedAssets.filter(asset => {
      // Type Filter
      if (filterType !== 'all' && asset.type !== filterType) return false;

      // Text Filter
      if (filterText) {
        const searchLower = filterText.toLowerCase();
        const prompt = (asset.metadata?.prompt as string)?.toLowerCase() || '';
        const id = asset.id.toLowerCase();
        return prompt.includes(searchLower) || id.includes(searchLower);
      }

      return true;
    });
  }, [generatedAssets, filterType, filterText]);


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

        <div className="flex gap-2 items-center">
          <Select value={selectedModelId} onValueChange={setSelectedModelId}>
            <SelectTrigger className="w-[180px] h-9">
              <SelectValue placeholder="Select Model" />
            </SelectTrigger>
            <SelectContent>
              {MODELS_BY_TYPE[activeTab].map((modelId) => (
                <SelectItem key={modelId} value={modelId}>
                  {MODEL_CONFIGS[modelId].name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button
            onClick={async () => {
              // Generate all clips for current tab
              const newGenerationIds: string[] = [];

              for (let i = 0; i < clips.length; i++) {
                const clip = clips[i];
                const prompt = activeTab === 'image' ? clip.image_prompt : clip.video_prompt;
                if (!prompt) continue;

                const genId = await handleGenerate({
                  prompt,
                  type: activeTab,
                  qualityTier: 'draft',
                  aspectRatio: defaultAspectRatio,
                  model: selectedModelId,
                  duration: activeTab === 'video' ? 5 : undefined,
                  resolution: '1080p',
                  skipStoreUpdate: true
                }, i);

                if (genId) newGenerationIds.push(genId);
              }

              if (newGenerationIds.length > 0) {
                const currentGenerated = compositionConfig?.generated_assets || [];
                updateCompositionConfig({
                  generated_assets: [...currentGenerated, ...newGenerationIds]
                });
                saveProject().catch(err => console.error("Failed to save project:", err));
              }
            }}
            className="gap-2"
          >
            <Sparkles className="h-4 w-4" />
            Generate All {activeTab === 'image' ? 'Images' : 'Videos'}
          </Button>
          {/* Actions like "Go to Media Library" could go here */}
          <Button variant="outline" size="sm" onClick={() => navigate('/media')}>
            Media Library
          </Button>
        </div>
      </header >

      <ResizablePanelGroup direction="vertical" className="flex-1 min-h-0">
        {/* Top Section (2/3 height) */}
        <ResizablePanel defaultSize={65} minSize={30}>
          <ResizablePanelGroup direction="horizontal" className="h-full">
            {/* Left Panel: Prompts (1/3 width) */}
            <ResizablePanel defaultSize={30} minSize={20} className="bg-background">
              <div className="h-full flex flex-col">
                <div className="flex items-center gap-1 p-2 border-b border-border">
                  <Button
                    variant={activeTab === 'image' ? 'secondary' : 'ghost'}
                    size="sm"
                    onClick={() => setActiveTab('image')}
                    className="flex-1"
                  >
                    Images
                  </Button>
                  <Button
                    variant={activeTab === 'video' ? 'secondary' : 'ghost'}
                    size="sm"
                    onClick={() => setActiveTab('video')}
                    className="flex-1"
                  >
                    Videos
                  </Button>
                </div>
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {clips.map((clip, index) => (
                    <Collapsible
                      key={index}
                      open={expanded[index] || false}
                      onOpenChange={(open) => setExpanded((prev) => ({ ...prev, [index]: open }))}
                    >
                      <CollapsibleTrigger asChild>
                        <Card className="w-full border-border text-left cursor-pointer hover:border-primary/50 transition-colors">
                          <CardHeader className="flex flex-row items-center justify-between gap-3 py-4">
                            <div className="space-y-1 overflow-hidden">
                              <CardTitle className="text-base text-foreground truncate pr-4">
                                {activeTab === 'image' ? 'Image' : 'Clip'} {index + 1}: <span className="font-normal text-muted-foreground">{activeTab === 'image' ? clip.image_prompt : clip.video_prompt}</span>
                              </CardTitle>
                              <div className="flex gap-2 text-xs text-muted-foreground">
                                <span>{clip.length}s</span>
                                <span className="bg-primary/10 text-primary px-1.5 rounded">
                                  {defaultAspectRatio}
                                </span>
                              </div>
                            </div>
                            <ChevronRight
                              className={`h-4 w-4 text-muted-foreground transition-transform flex-shrink-0 ${expanded[index] ? 'rotate-90' : ''
                                }`}
                            />
                          </CardHeader>
                        </Card>
                      </CollapsibleTrigger>
                      <CollapsibleContent className="mt-2">
                        <Card className="border-border bg-muted/20">
                          <CardContent className="pt-4">
                            <PromptInput
                              defaultType={activeTab}
                              allowedTypes={['image', 'video']}
                              selectedModelId={selectedModelId}
                              defaultPrompt={activeTab === 'image' ? clip.image_prompt : clip.video_prompt}
                              defaultAspectRatio={defaultAspectRatio}
                              autoPrompts={{ image: clip.image_prompt, video: clip.video_prompt }}
                              isPending={false}
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
              </div>
            </ResizablePanel>

            <ResizableHandle withHandle />

            {/* Right Panel: Generated Results (2/3 width) */}
            <ResizablePanel defaultSize={70} minSize={30} className="bg-muted/10">
              <div className="h-full flex flex-col">
                <div className="p-4 border-b border-border bg-background/50 backdrop-blur flex items-center justify-between gap-4">
                  <div>
                    <h2 className="font-semibold text-foreground">Session Results</h2>
                    <p className="text-xs text-muted-foreground">
                      Media generated in this session
                    </p>
                  </div>

                  {/* Filters */}
                  <div className="flex items-center gap-2">
                    <div className="relative w-[200px]">
                      <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        placeholder="Search prompts..."
                        value={filterText}
                        onChange={(e) => setFilterText(e.target.value)}
                        className="h-8 pl-8"
                      />
                    </div>
                    <Select value={filterType} onValueChange={(v: any) => setFilterType(v)}>
                      <SelectTrigger className="w-[130px] h-8">
                        <div className="flex items-center gap-2">
                          <Filter className="h-3.5 w-3.5" />
                          <SelectValue />
                        </div>
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Types</SelectItem>
                        <SelectItem value="image">Images</SelectItem>
                        <SelectItem value="video">Videos</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto p-6">
                  {visibleGenerations.length === 0 && filteredAssets.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center text-muted-foreground p-8">
                      <Sparkles className="h-12 w-12 mb-4 opacity-20" />
                      <p>No content generated yet.</p>
                      <p className="text-sm">Select a clip on the left and click Generate.</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-3 gap-4">
                      {/* Active/Completing Skeletons */}
                      {visibleGenerations.map(gen => (
                        <MediaGenerationSkeleton key={gen.id} />
                      ))}

                      {/* Completed Assets */}
                      {filteredAssets.map((asset) => {
                        if (!asset) return null;
                        return (
                          <div
                            key={asset.id}
                            draggable
                            onDragStart={(e) => {
                              e.dataTransfer.setData('application/json', JSON.stringify(asset));
                              e.dataTransfer.effectAllowed = 'copy';
                            }}
                            className="cursor-grab active:cursor-grabbing"
                          >
                            <MediaAssetCard
                              asset={asset}
                              isSelected={selectedAssetIds.includes(asset.id)}
                              onClick={() => selectAsset(asset.id, false)}
                              onDelete={() => deleteAsset(asset.id)}
                              onPreview={() => setPreviewAsset(asset)}
                            />
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            </ResizablePanel>
          </ResizablePanelGroup>
        </ResizablePanel>

        <ResizableHandle withHandle />

        {/* Bottom Section: Timeline (1/3 height) */}
        <ResizablePanel defaultSize={35} minSize={15}>
          <div className="h-full flex flex-col">
            <SimpleTimeline
              clips={timelineClips}
              onDrop={(asset) => {
                  // Add new item to timeline
                  const newItem: TimelineItem = {
                      id: generateUUID(),
                      asset
                  };
                  setTimelineClips(prev => [...prev, newItem]);
              }}
              onReorder={setTimelineClips}
              onRemove={(id) => setTimelineClips(prev => prev.filter(c => c.id !== id))}
              onExport={async () => {
                if (timelineClips.length === 0) return;

                setIsExporting(true);
                try {
                  const videoUrls = timelineClips
                    .filter(c => c.asset.type === 'video')
                    .map(c => c.asset.url);

                  if (videoUrls.length === 0) {
                    addToast({
                      message: 'No videos to export',
                      type: 'warning',
                      duration: 3000
                    });
                    setIsExporting(false);
                    return;
                  }

                  const response = await axios.post('/api/v1/test/concat', {
                    video_urls: videoUrls
                  }, {
                    responseType: 'blob'
                  });

                  // Create download link
                  const url = window.URL.createObjectURL(new Blob([response.data]));
                  const link = document.createElement('a');
                  link.href = url;
                  link.setAttribute('download', 'concatenated_video.mp4');
                  document.body.appendChild(link);
                  link.click();
                  link.remove();
                  window.URL.revokeObjectURL(url);

                  addToast({
                    message: 'Export successful',
                    type: 'success',
                    duration: 3000
                  });
                } catch (error) {
                  console.error('Export failed:', error);
                  addToast({
                    message: 'Export failed',
                    description: 'Please try again later',
                    type: 'error',
                    duration: 5000
                  });
                } finally {
                  setIsExporting(false);
                }
              }}
              isExporting={isExporting}
              onAdvancedEdit={() => {
                // Get project ID
                const projectId = compositionConfig?.id || 'new'; // Fallback
                
                // Prepare Advanced Editor State
                if (timelineStore && timelineClips.length > 0) {
                    const store = timelineStore.getState();
                    store.reset();
                    
                    // Create default track
                    store.addTrack({
                        type: 'video',
                        name: 'Main Track',
                        height: 80,
                        locked: false,
                        hidden: false,
                        muted: false,
                        order: 0
                    });
                    
                    // We assume the added track is the first/only one
                    // Since we just reset, tracks is empty before add.
                    // Wait, addTrack is async? No, Zustand actions are sync.
                    // But reading back state immediately might rely on closure.
                    // Let's check state again.
                    const freshState = timelineStore.getState();
                    const trackId = freshState.tracks[0]?.id;
                    
                    if (trackId) {
                        const fps = freshState.fps || 30;
                        let currentFrame = 0;
                        
                        timelineClips.forEach(item => {
                            const durationInSeconds = item.asset.duration || 5; // Default 5s
                            const durationFrames = Math.floor(durationInSeconds * fps);
                            
                            const newClip: Clip = {
                                id: `clip-${item.id}`, // Use stable ID from timeline item
                                trackId: trackId,
                                assetId: item.asset.id,
                                startTime: currentFrame,
                                duration: durationFrames,
                                inPoint: 0,
                                outPoint: durationFrames,
                                layer: 0,
                                opacity: 1,
                                scale: { x: 1, y: 1 },
                                position: { x: 0, y: 0 },
                                rotation: 0
                            };
                            
                            store.addClip(newClip);
                            currentFrame += durationFrames;
                        });
                    }
                }
                
                navigate(`/projects/${projectId}/editor`);
              }}
            />
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
    </div >
  );
}

export default PromptResults;
