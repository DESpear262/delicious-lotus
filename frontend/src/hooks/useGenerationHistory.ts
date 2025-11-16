/**
 * Generation History Hook
 * Manages state and API calls for the generation history page
 */

import { useState, useEffect, useCallback } from 'react';
import { listGenerations, deleteGeneration } from '@/api/services/generation';
import type {
  GenerationListItem,
  PaginationMeta,
  GenerationStatus,
} from '@/api/types';

export interface HistoryFilters {
  status?: GenerationStatus;
  search?: string;
  dateFrom?: string;
  dateTo?: string;
  pipelineType?: 'ad_creative' | 'music_video';
}

export interface HistorySortOptions {
  sortBy: 'date' | 'duration' | 'status';
  sortOrder: 'asc' | 'desc';
}

export interface UseGenerationHistoryResult {
  generations: GenerationListItem[];
  pagination: PaginationMeta | null;
  isLoading: boolean;
  error: Error | null;
  filters: HistoryFilters;
  sort: HistorySortOptions;
  page: number;
  limit: number;
  setFilters: (filters: HistoryFilters) => void;
  setSort: (sort: HistorySortOptions) => void;
  setPage: (page: number) => void;
  setLimit: (limit: number) => void;
  refresh: () => Promise<void>;
  deleteGeneration: (generationId: string) => Promise<void>;
}

const DEFAULT_LIMIT = 20;

export const useGenerationHistory = (): UseGenerationHistoryResult => {
  const [generations, setGenerations] = useState<GenerationListItem[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const [filters, setFilters] = useState<HistoryFilters>({});
  const [sort, setSort] = useState<HistorySortOptions>({
    sortBy: 'date',
    sortOrder: 'desc',
  });
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(DEFAULT_LIMIT);

  const fetchGenerations = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Build sort parameter
      const sortParam = sort.sortOrder === 'desc'
        ? `-${sort.sortBy}`
        : sort.sortBy;

      const response = await listGenerations({
        page,
        limit,
        status: filters.status,
        sort: sortParam,
      });

      // Apply client-side filtering for search and date range
      let filteredGenerations = response.generations;

      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        filteredGenerations = filteredGenerations.filter((gen) =>
          gen.prompt.toLowerCase().includes(searchLower) ||
          gen.generation_id.toLowerCase().includes(searchLower)
        );
      }

      if (filters.dateFrom) {
        filteredGenerations = filteredGenerations.filter((gen) =>
          new Date(gen.created_at) >= new Date(filters.dateFrom!)
        );
      }

      if (filters.dateTo) {
        filteredGenerations = filteredGenerations.filter((gen) =>
          new Date(gen.created_at) <= new Date(filters.dateTo!)
        );
      }

      setGenerations(filteredGenerations);
      setPagination(response.pagination);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch generations'));
      setGenerations([]);
      setPagination(null);
    } finally {
      setIsLoading(false);
    }
  }, [page, limit, filters, sort]);

  const handleDeleteGeneration = useCallback(async (generationId: string) => {
    try {
      await deleteGeneration(generationId);
      // Refresh the list after deletion
      await fetchGenerations();
    } catch (err) {
      throw err instanceof Error ? err : new Error('Failed to delete generation');
    }
  }, [fetchGenerations]);

  const refresh = useCallback(async () => {
    await fetchGenerations();
  }, [fetchGenerations]);

  // Fetch generations when dependencies change
  useEffect(() => {
    fetchGenerations();
  }, [fetchGenerations]);

  // Reset to page 1 when filters or limit change
  useEffect(() => {
    if (page !== 1) {
      setPage(1);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, limit]);

  return {
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
    deleteGeneration: handleDeleteGeneration,
  };
};
