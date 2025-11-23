import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import { X, Play, Film, ArrowRight } from 'lucide-react';
import type { MediaAsset } from '@/types/stores';
import { cn } from '@/lib/utils';

interface SimpleTimelineProps {
    clips: MediaAsset[];
    onDrop: (asset: MediaAsset) => void;
    onRemove: (index: number) => void;
    onExport: () => void;
    onAdvancedEdit: () => void;
    isExporting?: boolean;
}

export const SimpleTimeline: React.FC<SimpleTimelineProps> = ({
    clips,
    onDrop,
    onRemove,
    onExport,
    onAdvancedEdit,
    isExporting = false,
}) => {
    const [isDraggingOver, setIsDraggingOver] = useState(false);
    const [playingClipId, setPlayingClipId] = useState<string | null>(null);

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDraggingOver(true);
    };

    const handleDragLeave = () => {
        setIsDraggingOver(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDraggingOver(false);

        try {
            const assetData = e.dataTransfer.getData('application/json');
            if (assetData) {
                const asset = JSON.parse(assetData) as MediaAsset;
                onDrop(asset);
            }
        } catch (error) {
            console.error('Failed to parse dropped asset:', error);
        }
    };

    return (
        <div className="h-full flex flex-col bg-background border-t border-border">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-3 border-b border-border bg-muted/10">
                <div className="flex items-center gap-2">
                    <Film className="h-4 w-4 text-primary" />
                    <h3 className="font-semibold text-sm">Timeline</h3>
                    <span className="text-xs text-muted-foreground ml-2">
                        Drag and drop clips here to arrange
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    <Button
                        size="sm"
                        onClick={onExport}
                        disabled={clips.length === 0 || isExporting}
                        className="gap-2"
                    >
                        {isExporting ? (
                            <>
                                <div className="h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
                                Exporting...
                            </>
                        ) : (
                            'Quick Export'
                        )}
                    </Button>
                    <Button
                        size="sm"
                        variant="outline"
                        onClick={onAdvancedEdit}
                        className="gap-2"
                    >
                        Advanced Editor
                        <ArrowRight className="h-3 w-3" />
                    </Button>
                </div>
            </div>

            {/* Timeline Area */}
            <div
                className={cn(
                    "flex-1 relative transition-colors duration-200 min-h-0",
                    isDraggingOver ? "bg-primary/5" : "bg-muted/5"
                )}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                {clips.length === 0 ? (
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground pointer-events-none">
                        <Film className="h-8 w-8 mb-2 opacity-20" />
                        <p className="text-sm">Drag clips from Session Results here</p>
                    </div>
                ) : (
                    <ScrollArea className="h-full w-full whitespace-nowrap p-4">
                        <div className="flex gap-4 h-full items-center px-4 py-4">
                            {clips.map((clip, index) => {
                                const aspectRatio = clip.width && clip.height
                                    ? `${clip.width}/${clip.height}`
                                    : '16/9';

                                return (
                                    <div
                                        key={`${clip.id}-${index}`}
                                        className="relative group flex-shrink-0 h-full rounded-md overflow-hidden border border-border bg-background shadow-sm hover:ring-2 ring-primary/50 transition-all"
                                        style={{ aspectRatio }}
                                        onMouseEnter={() => clip.type === 'video' && setPlayingClipId(clip.id)}
                                        onMouseLeave={() => setPlayingClipId(null)}
                                    >
                                        {/* Remove Button */}
                                        <button
                                            onClick={() => onRemove(index)}
                                            className="absolute top-1 right-1 z-20 p-1 rounded-full bg-black/50 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-destructive"
                                        >
                                            <X className="h-3 w-3" />
                                        </button>

                                        {/* Content */}
                                        {clip.type === 'video' ? (
                                            playingClipId === clip.id ? (
                                                <video
                                                    src={clip.url}
                                                    className="w-full h-full object-cover"
                                                    autoPlay
                                                    muted
                                                    loop
                                                />
                                            ) : (
                                                <>
                                                    <img
                                                        src={clip.thumbnailUrl || clip.url}
                                                        alt="Clip thumbnail"
                                                        className="w-full h-full object-cover"
                                                    />
                                                    <div className="absolute inset-0 flex items-center justify-center bg-black/20 group-hover:bg-transparent transition-colors">
                                                        <Play className="h-6 w-6 text-white/80" fill="currentColor" />
                                                    </div>
                                                </>
                                            )
                                        ) : (
                                            <img
                                                src={clip.url}
                                                alt="Asset"
                                                className="w-full h-full object-cover"
                                            />
                                        )}

                                        {/* Index Badge */}
                                        <div className="absolute bottom-1 left-1 z-10 px-1.5 py-0.5 rounded bg-black/60 text-[10px] text-white font-mono">
                                            {index + 1}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                        <ScrollBar orientation="horizontal" />
                    </ScrollArea>
                )}
            </div>
        </div>
    );
};
