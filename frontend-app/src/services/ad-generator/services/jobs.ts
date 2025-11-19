/**
 * Jobs Service
 * API calls for job status and history management
 */

import type {
  ListGenerationsResponse,
  GetGenerationResponse,
  GetCompositionResponse,
  PaginationParams,
} from '@/services/ad-generator/types';
import { listGenerations, getGeneration } from './generation';
import { getComposition } from './composition';

/**
 * Get all jobs (generations) with filters
 * This is an alias for listGenerations for semantic clarity
 */
export const listJobs = async (
  params?: PaginationParams
): Promise<ListGenerationsResponse> => {
  return listGenerations(params);
};

/**
 * Get job details (supports both generation and composition IDs)
 */
export const getJob = async (
  jobId: string
): Promise<GetGenerationResponse | GetCompositionResponse> => {
  // Try to determine job type from ID prefix
  if (jobId.startsWith('gen_')) {
    return getGeneration(jobId);
  } else if (jobId.startsWith('comp_')) {
    return getComposition(jobId);
  }

  // Default to generation
  return getGeneration(jobId);
};

/**
 * Get recent jobs (last 10 generations)
 */
export const getRecentJobs = async (): Promise<ListGenerationsResponse> => {
  return listGenerations({
    page: 1,
    limit: 10,
    sort: '-created_at',
  });
};

/**
 * Get active jobs (queued or processing)
 */
export const getActiveJobs = async (): Promise<ListGenerationsResponse> => {
  // Get all active statuses
  const statuses = ['queued', 'processing', 'composing'] as const;

  // For now, we'll fetch all and filter client-side
  // In production, the API should support multiple status filters
  const allJobs = await listGenerations({
    page: 1,
    limit: 100,
  });

  // Filter to only active jobs
  const activeGenerations = allJobs.generations.filter((gen) =>
    statuses.includes(gen.status as (typeof statuses)[number])
  );

  return {
    generations: activeGenerations,
    pagination: {
      ...allJobs.pagination,
      total: activeGenerations.length,
    },
  };
};

/**
 * Get completed jobs
 */
export const getCompletedJobs = async (
  params?: PaginationParams
): Promise<ListGenerationsResponse> => {
  return listGenerations({
    ...params,
    status: 'completed',
  });
};

/**
 * Get failed jobs
 */
export const getFailedJobs = async (
  params?: PaginationParams
): Promise<ListGenerationsResponse> => {
  return listGenerations({
    ...params,
    status: 'failed',
  });
};

/**
 * Check if user has any active jobs
 */
export const hasActiveJobs = async (): Promise<boolean> => {
  const active = await getActiveJobs();
  return active.generations.length > 0;
};
