import React from 'react';
import { PipelineCard } from '../../components/ad-generator/PipelineCard';
import { PIPELINES } from '../../types/ad-generator/pipeline';

/**
 * PipelineSelection Page Component
 *
 * Home page that displays available video generation pipelines.
 * Users can select between Ad Creative and Music Video pipelines.
 */
export const PipelineSelection: React.FC = () => {
  const pipelines = Object.values(PIPELINES);

  return (
    <div className="flex flex-col gap-8 p-8 max-w-[1400px] mx-auto min-h-[calc(100vh-200px)] md:p-6 md:gap-6 sm:p-4 sm:gap-5">
      <div className="text-center animate-in slide-in-from-top-5 duration-500 ease-out">
        <h1 className="text-4xl font-bold text-foreground mb-4 leading-tight md:text-3xl sm:text-2xl">
          Choose Your Video Pipeline
        </h1>
        <p className="text-lg text-muted-foreground m-0 leading-relaxed md:text-base sm:text-sm">
          Select a pipeline to start creating AI-generated videos
        </p>
      </div>

      <div className="grid grid-cols-[repeat(auto-fit,minmax(400px,1fr))] gap-8 animate-in fade-in slide-in-from-bottom-8 duration-700 delay-200 fill-mode-both lg:grid-cols-[repeat(auto-fit,minmax(350px,1fr))] lg:gap-6 md:grid-cols-1 md:gap-6 sm:gap-5">
        {pipelines.map((pipeline) => (
          <PipelineCard key={pipeline.id} pipeline={pipeline} />
        ))}
      </div>

      <div className="text-center pt-4 animate-in fade-in duration-1000 delay-300 fill-mode-both md:pt-2">
        <p className="text-sm text-muted-foreground/80 m-0 leading-relaxed">
          More pipelines coming soon! Each pipeline is optimized for specific video types and use
          cases.
        </p>
      </div>
    </div>
  );
};
