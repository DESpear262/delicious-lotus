/**
 * History Page Component
 * Displays paginated list of user's generation jobs with filtering and search
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { GenerationCard } from '@/components/History/GenerationCard';
import { FilterSidebar } from '@/components/History/FilterSidebar';
import { Pagination } from '@/components/Pagination';
import { useGenerationHistory } from '@/hooks/useGenerationHistory';
import { download } from '@/api/client';
import styles from './History.module.css';

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
      navigate(`/generation/${generationId}`);
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
    <div className={styles.historyPage}>
      <div className={styles.sidebar}>
        <FilterSidebar
          filters={filters}
          onFiltersChange={setFilters}
          resultCount={pagination?.total}
        />
      </div>

      <div className={styles.main}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.headerTop}>
            <h1 className={styles.title}>Generation History</h1>
            <Button
              variant="ghost"
              size="sm"
              onClick={refresh}
              disabled={isLoading}
              leftIcon={
                <svg
                  className={styles.refreshIcon}
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
          <div className={styles.controls}>
            <div className={styles.searchWrapper}>
              <Input
                type="text"
                placeholder="Search by prompt or generation ID..."
                value={searchInput}
                onChange={handleSearchChange}
                fullWidth
                leftIcon={
                  <svg
                    className={styles.searchIcon}
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
                      className={styles.clearSearch}
                      aria-label="Clear search"
                    >
                      <svg
                        className={styles.clearIcon}
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

            <div className={styles.sortWrapper}>
              <label htmlFor="sort" className={styles.sortLabel}>
                Sort by:
              </label>
              <select
                id="sort"
                value={sortValue}
                onChange={handleSortChange}
                className={styles.sortSelect}
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
        <div className={styles.content}>
          {isLoading && (!generations || generations.length === 0) ? (
            <LoadingSkeleton />
          ) : error ? (
            <ErrorState error={error} onRetry={refresh} />
          ) : !generations || generations.length === 0 ? (
            <EmptyState hasFilters={!!debouncedSearch || Object.keys(filters).length > 0} />
          ) : (
            <>
              <div className={styles.generationList}>
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
    <div className={styles.loadingSkeleton}>
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className={styles.skeletonCard}>
          <div className={styles.skeletonThumbnail} />
          <div className={styles.skeletonDetails}>
            <div className={styles.skeletonTitle} />
            <div className={styles.skeletonMetadata} />
            <div className={styles.skeletonActions} />
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
    <div className={styles.emptyState}>
      <svg
        className={styles.emptyIcon}
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
      <h2 className={styles.emptyTitle}>
        {hasFilters ? 'No generations found' : 'No generations yet'}
      </h2>
      <p className={styles.emptyDescription}>
        {hasFilters
          ? 'Try adjusting your filters or search criteria.'
          : 'Start creating amazing AI-generated videos to see them here.'}
      </p>
      {!hasFilters && (
        <Button
          variant="primary"
          onClick={() => (window.location.href = '/')}
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
    <div className={styles.errorState}>
      <svg
        className={styles.errorIcon}
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
      <h2 className={styles.errorTitle}>Failed to load generations</h2>
      <p className={styles.errorDescription}>{error.message}</p>
      <Button variant="primary" onClick={onRetry}>
        Try Again
      </Button>
    </div>
  );
}
