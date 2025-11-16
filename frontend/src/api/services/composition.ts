/**
 * Composition Service
 * API calls for video composition operations
 */

import { get, post, download } from '@/api/client';
import type {
  CreateCompositionRequest,
  CreateCompositionResponse,
  GetCompositionResponse,
  GetCompositionMetadataResponse,
  EditCompositionRequest,
  EditCompositionResponse,
} from '@/api/types';

/**
 * Create a new video composition
 */
export const createComposition = async (
  request: CreateCompositionRequest
): Promise<CreateCompositionResponse> => {
  return post<CreateCompositionResponse, CreateCompositionRequest>(
    '/v1/compositions',
    request
  );
};

/**
 * Get composition status and progress
 */
export const getComposition = async (
  compositionId: string
): Promise<GetCompositionResponse> => {
  return get<GetCompositionResponse>(`/v1/compositions/${compositionId}`);
};

/**
 * Get composition metadata
 */
export const getCompositionMetadata = async (
  compositionId: string
): Promise<GetCompositionMetadataResponse> => {
  return get<GetCompositionMetadataResponse>(
    `/v1/compositions/${compositionId}/metadata`
  );
};

/**
 * Download final composed video
 */
export const downloadComposition = async (
  compositionId: string,
  filename?: string
): Promise<Blob> => {
  const finalFilename =
    filename || `video_composition_${compositionId}.mp4`;
  return download(`/v1/compositions/${compositionId}/download`, finalFilename);
};

/**
 * AI-assisted composition edit
 */
export const editComposition = async (
  compositionId: string,
  request: EditCompositionRequest
): Promise<EditCompositionResponse> => {
  return post<EditCompositionResponse, EditCompositionRequest>(
    `/v1/compositions/${compositionId}/edit`,
    request
  );
};

/**
 * Poll composition status until complete or failed
 * Returns a promise that resolves when composition is done
 */
export const pollCompositionStatus = async (
  compositionId: string,
  onProgress?: (response: GetCompositionResponse) => void,
  intervalMs: number = 2000
): Promise<GetCompositionResponse> => {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const response = await getComposition(compositionId);

        // Call progress callback if provided
        if (onProgress) {
          onProgress(response);
        }

        // Check if composition is complete
        if (response.status === 'completed') {
          resolve(response);
          return;
        }

        // Check if composition failed
        if (response.status === 'failed') {
          reject(new Error(`Composition failed: ${compositionId}`));
          return;
        }

        // Continue polling
        setTimeout(poll, intervalMs);
      } catch (error) {
        reject(error);
      }
    };

    poll();
  });
};
