import { Card } from '../ui/card';
import { Skeleton } from '../ui/skeleton';
import { Loader2 } from 'lucide-react';

export function MediaGenerationSkeleton() {
    return (
        <Card className="bg-zinc-900 border-zinc-800 overflow-hidden">
            {/* Thumbnail Skeleton */}
            <div className="aspect-square relative bg-zinc-950 flex items-center justify-center">
                <Skeleton className="w-full h-full absolute inset-0 bg-zinc-800/50" />
                <div className="relative z-10 flex flex-col items-center gap-2 text-zinc-500">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
                    <span className="text-xs font-medium">Generating...</span>
                </div>
            </div>

            {/* Metadata Skeleton */}
            <div className="p-3 space-y-2">
                <div className="flex items-center justify-between gap-2">
                    <Skeleton className="h-4 w-24 bg-zinc-800" />
                    <Skeleton className="h-4 w-12 rounded-full bg-zinc-800" />
                </div>
                <div className="flex items-center justify-between">
                    <Skeleton className="h-3 w-16 bg-zinc-800" />
                    <Skeleton className="h-3 w-16 bg-zinc-800" />
                </div>
            </div>
        </Card>
    );
}
