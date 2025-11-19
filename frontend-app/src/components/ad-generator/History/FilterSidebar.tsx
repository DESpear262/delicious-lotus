import React from 'react';
import { Input } from '@/components/ad-generator/ui/Input';
import { Button } from '@/components/ad-generator/ui/Button';
import type { GenerationStatus } from '@/services/ad-generator/types';
import type { HistoryFilters } from '@/hooks/ad-generator/useGenerationHistory';

export interface FilterSidebarProps {
  filters: HistoryFilters;
  onFiltersChange: (filters: HistoryFilters) => void;
  resultCount?: number;
}

const STATUS_OPTIONS: { value: GenerationStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'All Status' },
  { value: 'completed', label: 'Completed' },
  { value: 'processing', label: 'Processing' },
  { value: 'composing', label: 'Composing' },
  { value: 'queued', label: 'Queued' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' },
];

const PIPELINE_OPTIONS: { value: 'all' | 'ad_creative' | 'music_video'; label: string }[] = [
  { value: 'all', label: 'All Types' },
  { value: 'ad_creative', label: 'Ad Creative' },
  { value: 'music_video', label: 'Music Video' },
];

export const FilterSidebar: React.FC<FilterSidebarProps> = ({
  filters,
  onFiltersChange,
  resultCount,
}) => {
  const handleStatusChange = (status: string) => {
    onFiltersChange({
      ...filters,
      status: status === 'all' ? undefined : (status as GenerationStatus),
    });
  };

  const handlePipelineChange = (pipeline: string) => {
    onFiltersChange({
      ...filters,
      pipelineType: pipeline === 'all' ? undefined : (pipeline as 'ad_creative' | 'music_video'),
    });
  };

  const handleDateFromChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({
      ...filters,
      dateFrom: e.target.value || undefined,
    });
  };

  const handleDateToChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({
      ...filters,
      dateTo: e.target.value || undefined,
    });
  };

  const handleClearFilters = () => {
    onFiltersChange({});
  };

  const hasActiveFilters = !!(
    filters.status ||
    filters.pipelineType ||
    filters.dateFrom ||
    filters.dateTo
  );

  return (
    <div className="w-full bg-background border-r border-border p-6 flex flex-col gap-6 md:border-r-0 md:border-b md:p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-foreground m-0">Filters</h3>
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearFilters}
            className="text-sm text-primary"
          >
            Clear All
          </Button>
        )}
      </div>

      {resultCount !== undefined && (
        <div className="p-3 bg-muted rounded-md text-sm text-muted-foreground text-center">
          {resultCount} {resultCount === 1 ? 'result' : 'results'}
        </div>
      )}

      {/* Status Filter */}
      <div className="flex flex-col gap-3 pb-6 border-b border-border md:pb-4">
        <label className="text-sm font-medium text-foreground">Status</label>
        <div className="flex flex-col gap-2">
          {STATUS_OPTIONS.map((option) => (
            <label key={option.value} className="flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors hover:bg-muted">
              <input
                type="radio"
                name="status"
                value={option.value}
                checked={
                  option.value === 'all'
                    ? !filters.status
                    : filters.status === option.value
                }
                onChange={(e) => handleStatusChange(e.target.value)}
                className="w-4 h-4 cursor-pointer accent-primary"
              />
              <span className="text-sm text-foreground cursor-pointer">{option.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Pipeline Type Filter */}
      <div className="flex flex-col gap-3 pb-6 border-b border-border md:pb-4">
        <label className="text-sm font-medium text-foreground">Pipeline Type</label>
        <div className="flex flex-col gap-2">
          {PIPELINE_OPTIONS.map((option) => (
            <label key={option.value} className="flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors hover:bg-muted">
              <input
                type="radio"
                name="pipelineType"
                value={option.value}
                checked={
                  option.value === 'all'
                    ? !filters.pipelineType
                    : filters.pipelineType === option.value
                }
                onChange={(e) => handlePipelineChange(e.target.value)}
                className="w-4 h-4 cursor-pointer accent-primary"
              />
              <span className="text-sm text-foreground cursor-pointer">{option.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Date Range Filter */}
      <div className="flex flex-col gap-3 pb-0 border-b-0">
        <label className="text-sm font-medium text-foreground">Date Range</label>
        <div className="flex flex-col gap-2">
          <Input
            type="date"
            placeholder="From"
            value={filters.dateFrom || ''}
            onChange={handleDateFromChange}
          />
          <span className="text-sm text-muted-foreground text-center py-1">to</span>
          <Input
            type="date"
            placeholder="To"
            value={filters.dateTo || ''}
            onChange={handleDateToChange}
          />
        </div>
      </div>
    </div>
  );
};
