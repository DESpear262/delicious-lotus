/**
 * API Client Configuration
 * Configured Axios instance with interceptors and error handling
 */

import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from 'axios';
import { parseApiError, logError } from '@/utils/errors';
import {
  withRetry,
  apiCircuitBreaker,
  type RetryOptions,
} from '@/utils/retry';

/**
 * Generate a simple UUID v4
 */
const generateUUID = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

/**
 * API Client configuration
 */
interface ApiClientConfig {
  baseURL?: string;
  timeout?: number;
  uploadTimeout?: number;
  withCredentials?: boolean;
}

/**
 * Default configuration
 */
const DEFAULT_CONFIG: ApiClientConfig = {
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000, // 30 seconds for regular API calls
  uploadTimeout: 300000, // 5 minutes for file uploads
  withCredentials: true, // Include cookies for session-based auth
};

/**
 * Create and configure axios instance
 */
const createApiClient = (config: ApiClientConfig = {}): AxiosInstance => {
  const finalConfig = { ...DEFAULT_CONFIG, ...config };

  const client = axios.create({
    baseURL: finalConfig.baseURL,
    timeout: finalConfig.timeout,
    withCredentials: finalConfig.withCredentials,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor
  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      // Add request ID for tracing
      if (!config.headers['X-Request-ID']) {
        config.headers['X-Request-ID'] = generateUUID();
      }

      // Add client version
      config.headers['X-Client-Version'] = '1.0.0';

      // Check circuit breaker
      if (apiCircuitBreaker.isOpen()) {
        const error = new Error(
          'Circuit breaker is open. Too many recent failures.'
        );
        error.name = 'CircuitBreakerError';
        throw error;
      }

      // Log request in development
      if (import.meta.env.DEV) {
        console.log('[API Request]', {
          method: config.method?.toUpperCase(),
          url: config.url,
          requestId: config.headers['X-Request-ID'],
        });
      }

      return config;
    },
    (error) => {
      logError(error, 'Request Interceptor');
      return Promise.reject(error);
    }
  );

  // Response interceptor
  client.interceptors.response.use(
    (response: AxiosResponse) => {
      // Record success for circuit breaker
      apiCircuitBreaker.recordSuccess();

      // Log response in development
      if (import.meta.env.DEV) {
        console.log('[API Response]', {
          status: response.status,
          url: response.config.url,
          requestId: response.config.headers['X-Request-ID'],
        });
      }

      return response;
    },
    (error) => {
      // Record failure for circuit breaker
      apiCircuitBreaker.recordFailure();

      // Parse and enhance error
      const apiError = parseApiError(error);

      // Log error
      logError(apiError, 'API Response Error');

      return Promise.reject(apiError);
    }
  );

  return client;
};

/**
 * Main API client instance
 */
export const apiClient = createApiClient();

/**
 * Upload client instance with extended timeout
 */
export const uploadClient = createApiClient({
  timeout: DEFAULT_CONFIG.uploadTimeout,
});

/**
 * Make API request with retry logic
 */
export const makeRequest = async <T>(
  requestFn: () => Promise<AxiosResponse<T>>,
  retryOptions?: RetryOptions
): Promise<T> => {
  const response = await withRetry(requestFn, {
    maxRetries: 3,
    baseDelay: 1000,
    onRetry: (attempt, error) => {
      console.warn(`[Retry] Attempt ${attempt}:`, error.message);
    },
    ...retryOptions,
  });

  return response.data;
};

/**
 * Type-safe GET request
 */
export const get = async <T>(
  url: string,
  config?: AxiosRequestConfig,
  retryOptions?: RetryOptions
): Promise<T> => {
  return makeRequest(() => apiClient.get<T>(url, config), retryOptions);
};

/**
 * Type-safe POST request
 */
export const post = async <T, D = unknown>(
  url: string,
  data?: D,
  config?: AxiosRequestConfig,
  retryOptions?: RetryOptions
): Promise<T> => {
  return makeRequest(() => apiClient.post<T>(url, data, config), retryOptions);
};

/**
 * Type-safe PUT request
 */
export const put = async <T, D = unknown>(
  url: string,
  data?: D,
  config?: AxiosRequestConfig,
  retryOptions?: RetryOptions
): Promise<T> => {
  return makeRequest(() => apiClient.put<T>(url, data, config), retryOptions);
};

/**
 * Type-safe DELETE request
 */
export const del = async <T>(
  url: string,
  config?: AxiosRequestConfig,
  retryOptions?: RetryOptions
): Promise<T> => {
  return makeRequest(
    () => apiClient.delete<T>(url, config),
    retryOptions
  );
};

/**
 * Type-safe file upload
 */
export const upload = async <T>(
  url: string,
  formData: FormData,
  onProgress?: (progress: number) => void,
  config?: AxiosRequestConfig
): Promise<T> => {
  const response = await uploadClient.post<T>(url, formData, {
    ...config,
    headers: {
      'Content-Type': 'multipart/form-data',
      ...config?.headers,
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percentage = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        onProgress(percentage);
      }
    },
  });

  return response.data;
};

/**
 * Download file
 */
export const download = async (
  url: string,
  filename?: string,
  config?: AxiosRequestConfig
): Promise<Blob> => {
  const response = await apiClient.get(url, {
    ...config,
    responseType: 'blob',
  });

  // If filename provided, trigger download
  if (filename) {
    const blob = response.data as Blob;
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  return response.data;
};

/**
 * Health check endpoint
 */
export const checkHealth = async (): Promise<boolean> => {
  try {
    await apiClient.get('/health', { timeout: 5000 });
    return true;
  } catch {
    return false;
  }
};

export default apiClient;
