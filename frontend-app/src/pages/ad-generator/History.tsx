
/**
 * History Page Component
 * Displays paginated list of user's generation jobs with filtering and search
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { ROUTES } from '../../types/routes';
import { Input } from '@/components/ad-generator/ui/Input';
import { Button } from '@/components/ad-generator/ui/Button';
import { GenerationCard } from '@/components/ad-generator/History/GenerationCard';
import { FilterSidebar } from '@/components/ad-generator/History/FilterSidebar';
import { Pagination } from '@/components/ad-generator/Pagination';
import { useGenerationHistory } from '@/hooks/ad-generator/useGenerationHistory';
import { download } from '@/services/ad-generator/client';

const DEBOUNCE_DELAY = 400; // ms

export function History() {
  const navigate = useNavigate();
  const {
    generations,
    pagination,
    isLoading,
    error,
    filters,
    sort,
    page,
    limit,
    setFilters,
    setSort,
    setPage,
    setLimit,
    refresh,
    deleteGeneration,
  } = useGenerationHistory();

  const [searchInput, setSearchInput] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchInput);
    }, DEBOUNCE_DELAY);

    return () => clearTimeout(timer);
  }, [searchInput]);

  // Update filters when debounced search changes
  useEffect(() => {
    setFilters({
      ...filters,
      search: debouncedSearch || undefined,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchInput(e.target.value);
  };

  const handleClearSearch = () => {
    setSearchInput('');
  };

  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const [sortBy, sortOrder] = e.target.value.split('_');
    setSort({
      sortBy: sortBy as 'date' | 'duration' | 'status',
      sortOrder: sortOrder as 'asc' | 'desc',
    });
  };

  const handleView = useCallback(
    (generationId: string) => {
      navigate(`${ROUTES.AD_GENERATOR}/generation/${generationId}`);
    },
    [navigate]
  );

  const handleDownload = useCallback(async (generationId: string) => {
    try {
      await download(
        `/v1/generations/${generationId}/download`,
        `generation-${generationId}.mp4`
      );
    } catch (err) {
      console.error('Failed to download generation:', err);
    }
  }, []);

  const handleDelete = useCallback(
    async (generationId: string) => {
      try {
        await deleteGeneration(generationId);
      } catch (err) {
        console.error('Failed to delete generation:', err);
      }
    },
    [deleteGeneration]
  );

  const sortValue = `${sort.sortBy}_${sort.sortOrder}`;

  return (
    <div className="flex min-h-full bg-background md:flex-col">
      <div className="w-[280px] shrink-0 bg-background border-r border-border md:w-full md:border-r-0 md:border-b">
        <FilterSidebar
          filters={filters}
          onFiltersChange={setFilters}
          resultCount={pagination?.total}
        />
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="bg-background border-b border-border p-6 md:p-4">
          <div className="flex items-center justify-between mb-4 md:flex-col md:gap-3 md:items-start">
            <h1 className="text-3xl font-bold text-foreground m-0 md:text-2xl">Generation History</h1>
            <Button
              variant="ghost"
              size="sm"
              onClick={refresh}
              disabled={isLoading}
              leftIcon={
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
              }
            >
              Refresh
            </Button>
          </div>

          {/* Search and Sort */}
          <div className="flex gap-4 items-end lg:flex-col lg:items-stretch">
            <div className="flex-1 max-w-[500px] lg:max-w-none lg:w-full">
              <Input
                type="text"
                placeholder="Search by prompt or generation ID..."
                value={searchInput}
                onChange={handleSearchChange}
                fullWidth
                leftIcon={
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                }
                rightIcon={
                  searchInput ? (
                    <button
                      onClick={handleClearSearch}
                      className="bg-none border-none p-0 cursor-pointer text-muted-foreground flex items-center justify-center transition-colors hover:text-foreground"
                      aria-label="Clear search"
                    >
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M6 18L18 6M6 6l12 12"
                        />
                      </svg>
                    </button>
                  ) : null
                }
              />
            </div>

            <div className="flex items-center gap-2 lg:justify-between">
              <label htmlFor="sort" className="text-sm text-muted-foreground whitespace-nowrap">
                Sort by:
              </label>
              <select
                id="sort"
                value={sortValue}
                onChange={handleSortChange}
                className="py-2 px-3 border border-border rounded-md text-sm text-foreground bg-background cursor-pointer transition-colors hover:border-primary focus:outline-none focus:border-primary focus:ring-2 focus:ring-blue-500/10"
              >
                <option value="date_desc">Newest First</option>
                <option value="date_asc">Oldest First</option>
                <option value="duration_desc">Duration (High to Low)</option>
                <option value="duration_asc">Duration (Low to High)</option>
                <option value="status_asc">Status (A-Z)</option>
                <option value="status_desc">Status (Z-A)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 flex flex-col">
          {isLoading && (!generations || generations.length === 0) ? (
            <LoadingSkeleton />
          ) : error ? (
            <ErrorState error={error} onRetry={refresh} />
          ) : !generations || generations.length === 0 ? (
            <EmptyState hasFilters={!!debouncedSearch || Object.keys(filters).length > 0} />
          ) : (
            <>
              <div className="p-6 flex flex-col gap-4 md:p-4">
                {generations.map((generation) => (
                  <GenerationCard
                    key={generation.generation_id}
                    generation={generation}
                    onView={handleView}
                    onDownload={handleDownload}
                    onDelete={handleDelete}
                  />
                ))}
              </div>

              {pagination && pagination.pages > 1 && (
                <Pagination
                  currentPage={page}
                  totalPages={pagination.pages}
                  totalItems={pagination.total}
                  itemsPerPage={limit}
                  onPageChange={setPage}
                  onItemsPerPageChange={setLimit}
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// Loading Skeleton Component
function LoadingSkeleton() {
  return (
    <div className="p-6 flex flex-col gap-4 md:p-4">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex gap-4 p-4 bg-background border border-border rounded-lg">
          <div className="w-[160px] h-[90px] bg-gradient-to-r from-muted via-muted/50 to-muted bg-[length:200%_100%] animate-[skeleton-loading_1.5s_ease-in-out_infinite] rounded-md shrink-0" />
          <div className="flex-1 flex flex-col gap-3">
            <div className="h-5 w-[70%] bg-gradient-to-r from-muted via-muted/50 to-muted bg-[length:200%_100%] animate-[skeleton-loading_1.5s_ease-in-out_infinite] rounded-sm" />
            <div className="h-3.5 w-[40%] bg-gradient-to-r from-muted via-muted/50 to-muted bg-[length:200%_100%] animate-[skeleton-loading_1.5s_ease-in-out_infinite] rounded-sm" />
            <div className="h-8 w-[200px] bg-gradient-to-r from-muted via-muted/50 to-muted bg-[length:200%_100%] animate-[skeleton-loading_1.5s_ease-in-out_infinite] rounded-md mt-auto" />
          </div>
        </div>
      ))}
    </div>
  );
}

// Empty State Component
interface EmptyStateProps {
  hasFilters: boolean;
}

function EmptyState({ hasFilters }: EmptyStateProps) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-12 text-center md:p-8">
      <svg
        className="w-20 h-20 text-muted-foreground mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
        />
      </svg>
      <h2 className="text-2xl font-semibold text-foreground m-0 mb-3">
        {hasFilters ? 'No generations found' : 'No generations yet'}
      </h2>
      <p className="text-base text-muted-foreground m-0 mb-6 max-w-[400px]">
        {hasFilters
          ? 'Try adjusting your filters or search criteria.'
          : 'Start creating amazing AI-generated videos to see them here.'}
      </p>
      {!hasFilters && (
        <Button
          variant="primary"
          onClick={() => (window.location.href = ROUTES.AD_GENERATOR)}
        >
          Create Your First Video
        </Button>
      )}
    </div>
  );
}

// Error State Component
interface ErrorStateProps {
  error: Error;
  onRetry: () => void;
}

function ErrorState({ error, onRetry }: ErrorStateProps) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-12 text-center md:p-8">
      <svg
        className="w-20 h-20 text-red-500 mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      </svg>
      <h2 className="text-2xl font-semibold text-foreground m-0 mb-3">Failed to load generations</h2>
      <p className="text-base text-muted-foreground m-0 mb-6 max-w-[400px]">{error.message}</p>
      <Button variant="primary" onClick={onRetry}>
        Try Again
      </Button>
    </div>
  );
}
