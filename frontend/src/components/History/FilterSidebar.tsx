/**
 * Filter Sidebar Component
 * Provides filtering controls for generation history
 */

import React from 'react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import type { GenerationStatus } from '@/api/types';
import type { HistoryFilters } from '@/hooks/useGenerationHistory';
import styles from './FilterSidebar.module.css';

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
    <div className={styles.filterSidebar}>
      <div className={styles.header}>
        <h3 className={styles.title}>Filters</h3>
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearFilters}
            className={styles.clearButton}
          >
            Clear All
          </Button>
        )}
      </div>

      {resultCount !== undefined && (
        <div className={styles.resultCount}>
          {resultCount} {resultCount === 1 ? 'result' : 'results'}
        </div>
      )}

      {/* Status Filter */}
      <div className={styles.filterSection}>
        <label className={styles.filterLabel}>Status</label>
        <div className={styles.radioGroup}>
          {STATUS_OPTIONS.map((option) => (
            <label key={option.value} className={styles.radioOption}>
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
                className={styles.radioInput}
              />
              <span className={styles.radioLabel}>{option.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Pipeline Type Filter */}
      <div className={styles.filterSection}>
        <label className={styles.filterLabel}>Pipeline Type</label>
        <div className={styles.radioGroup}>
          {PIPELINE_OPTIONS.map((option) => (
            <label key={option.value} className={styles.radioOption}>
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
                className={styles.radioInput}
              />
              <span className={styles.radioLabel}>{option.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Date Range Filter */}
      <div className={styles.filterSection}>
        <label className={styles.filterLabel}>Date Range</label>
        <div className={styles.dateRange}>
          <Input
            type="date"
            placeholder="From"
            value={filters.dateFrom || ''}
            onChange={handleDateFromChange}
          />
          <span className={styles.dateSeparator}>to</span>
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
