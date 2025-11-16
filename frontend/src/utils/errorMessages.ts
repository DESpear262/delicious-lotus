/**
 * Error Messages Utility
 * Comprehensive error code to user-friendly message mapping
 */

/**
 * HTTP Status Code to Message Mapping
 */
export const HTTP_STATUS_MESSAGES: Record<number, string> = {
  // Client Errors (4xx)
  400: 'The request was invalid. Please check your input and try again.',
  401: 'You need to be logged in to perform this action.',
  403: 'You do not have permission to access this resource.',
  404: 'The requested resource could not be found.',
  405: 'This action is not allowed.',
  408: 'The request timed out. Please try again.',
  409: 'This action conflicts with the current state. Please refresh and try again.',
  410: 'This resource is no longer available.',
  413: 'The file you are trying to upload is too large.',
  415: 'This file type is not supported.',
  422: 'The data you provided could not be processed. Please check your input.',
  429: 'Too many requests. Please wait a moment and try again.',
  451: 'This content is unavailable for legal reasons.',

  // Server Errors (5xx)
  500: 'An internal server error occurred. Please try again later.',
  501: 'This feature is not yet implemented.',
  502: 'Bad gateway. The server is temporarily unavailable.',
  503: 'The service is temporarily unavailable. Please try again later.',
  504: 'Gateway timeout. The server took too long to respond.',
  507: 'Insufficient storage. Please contact support.',
  509: 'Bandwidth limit exceeded. Please try again later.',
};

/**
 * Application Error Codes to Messages
 */
export const ERROR_CODE_MESSAGES: Record<string, string> = {
  // Authentication & Authorization
  INVALID_CREDENTIALS: 'Invalid username or password.',
  EXPIRED_SESSION: 'Your session has expired. Please log in again.',
  INVALID_TOKEN: 'Your authentication token is invalid. Please log in again.',
  UNAUTHORIZED: 'You are not authorized to perform this action.',
  FORBIDDEN: 'Access to this resource is forbidden.',

  // Validation Errors
  INVALID_PROMPT:
    'Your prompt is invalid. Please check the length and content.',
  INVALID_PARAMETERS:
    'One or more generation parameters are invalid. Please review your settings.',
  INVALID_FORMAT: 'The data format is invalid. Please check your input.',
  MISSING_REQUIRED_FIELD: 'Required fields are missing. Please fill out all required information.',
  FIELD_TOO_LONG: 'One or more fields exceed the maximum length.',
  FIELD_TOO_SHORT: 'One or more fields are too short.',
  INVALID_EMAIL: 'Please enter a valid email address.',
  INVALID_URL: 'Please enter a valid URL.',
  INVALID_DATE: 'Please enter a valid date.',
  INVALID_FILE_TYPE: 'This file type is not supported. Please upload a valid file.',
  FILE_TOO_LARGE: 'The file is too large. Please upload a smaller file.',
  FILE_TOO_SMALL: 'The file is too small. Please upload a larger file.',

  // Resource Errors
  GENERATION_NOT_FOUND:
    'The requested generation could not be found. It may have been deleted.',
  COMPOSITION_NOT_FOUND:
    'The requested composition could not be found. It may have been deleted.',
  ASSET_NOT_FOUND: 'The requested asset could not be found. It may have been deleted.',
  USER_NOT_FOUND: 'The user could not be found.',
  RESOURCE_NOT_FOUND: 'The requested resource could not be found.',
  RESOURCE_ALREADY_EXISTS: 'A resource with this identifier already exists.',

  // Rate Limiting & Quotas
  RATE_LIMIT_EXCEEDED:
    'You have made too many requests. Please wait a moment and try again.',
  QUOTA_EXCEEDED: 'You have exceeded your quota. Please upgrade your plan or contact support.',
  INSUFFICIENT_CREDITS:
    'You do not have enough credits to complete this action.',
  DAILY_LIMIT_REACHED: 'You have reached your daily limit. Please try again tomorrow.',

  // Processing Errors
  PROCESSING_FAILED:
    'Processing failed. Please try again or contact support.',
  GENERATION_FAILED:
    'Video generation failed. Please try generating again.',
  UPLOAD_FAILED: 'File upload failed. Please try again.',
  DOWNLOAD_FAILED: 'File download failed. Please try again.',
  CONVERSION_FAILED: 'File conversion failed. Please try a different file.',
  ENCODING_FAILED: 'Video encoding failed. Please try again.',
  RENDERING_FAILED: 'Video rendering failed. Please try again.',

  // External Service Errors
  REPLICATE_API_ERROR:
    'There was an error with the AI generation service. Please try again later.',
  STORAGE_ERROR:
    'There was an error accessing storage. Please try again later.',
  DATABASE_ERROR:
    'A database error occurred. Please try again or contact support.',
  QUEUE_ERROR:
    'There was an error with the job queue. Please try again later.',
  WEBHOOK_ERROR: 'There was an error processing the webhook.',
  EXTERNAL_API_ERROR: 'An external service error occurred. Please try again later.',

  // Network Errors
  NETWORK_ERROR:
    'Unable to connect to the server. Please check your internet connection.',
  TIMEOUT_ERROR: 'The request took too long to complete. Please try again.',
  CONNECTION_REFUSED: 'Connection refused. Please check your network settings.',
  DNS_ERROR: 'DNS resolution failed. Please check your internet connection.',
  SSL_ERROR: 'SSL certificate error. Please contact support.',

  // State Errors
  INVALID_STATE: 'The resource is in an invalid state for this operation.',
  CONFLICT: 'This action conflicts with the current state. Please refresh and try again.',
  PRECONDITION_FAILED: 'A precondition for this operation was not met.',
  ALREADY_PROCESSING: 'This resource is already being processed.',
  NOT_READY: 'The resource is not ready for this operation.',

  // Generic
  UNKNOWN_ERROR:
    'An unexpected error occurred. Please try again or contact support.',
  INTERNAL_ERROR: 'An internal error occurred. Please contact support.',
  BAD_REQUEST: 'The request was invalid. Please check your input.',
  SERVICE_UNAVAILABLE: 'The service is temporarily unavailable. Please try again later.',
  MAINTENANCE_MODE: 'The service is currently under maintenance. Please try again later.',
};

/**
 * Validation Error Field Messages
 */
export const VALIDATION_FIELD_MESSAGES: Record<string, string> = {
  prompt: 'Please enter a valid prompt.',
  duration: 'Please enter a valid duration.',
  aspectRatio: 'Please select a valid aspect ratio.',
  style: 'Please select a valid style.',
  brand: 'Please enter brand information.',
  colors: 'Please select valid brand colors.',
  logo: 'Please upload a valid logo.',
  email: 'Please enter a valid email address.',
  password: 'Please enter a valid password.',
  confirmPassword: 'Passwords do not match.',
  name: 'Please enter a valid name.',
  title: 'Please enter a valid title.',
  description: 'Please enter a valid description.',
  url: 'Please enter a valid URL.',
  file: 'Please select a valid file.',
};

/**
 * Get user-friendly message for HTTP status code
 */
export const getHttpStatusMessage = (statusCode: number): string => {
  return (
    HTTP_STATUS_MESSAGES[statusCode] ||
    ERROR_CODE_MESSAGES.UNKNOWN_ERROR
  );
};

/**
 * Get user-friendly message for error code
 */
export const getErrorCodeMessage = (code: string): string => {
  return ERROR_CODE_MESSAGES[code] || ERROR_CODE_MESSAGES.UNKNOWN_ERROR;
};

/**
 * Get user-friendly message for validation field
 */
export const getValidationFieldMessage = (field: string): string => {
  return (
    VALIDATION_FIELD_MESSAGES[field] ||
    `Please check the ${field} field.`
  );
};

/**
 * Parse validation errors from API response
 */
export interface ValidationError {
  field: string;
  message: string;
}

export const parseValidationErrors = (
  details?: Record<string, unknown>
): ValidationError[] => {
  if (!details) {
    return [];
  }

  const errors: ValidationError[] = [];

  // Handle different validation error formats
  if (details.errors && Array.isArray(details.errors)) {
    // Format: { errors: [{ field: 'email', message: 'Invalid email' }] }
    return details.errors.map((error: { field: string; message: string }) => ({
      field: error.field,
      message: error.message || getValidationFieldMessage(error.field),
    }));
  }

  if (details.fields && typeof details.fields === 'object') {
    // Format: { fields: { email: 'Invalid email', password: 'Too short' } }
    Object.entries(details.fields).forEach(([field, message]) => {
      errors.push({
        field,
        message: typeof message === 'string' ? message : getValidationFieldMessage(field),
      });
    });
  }

  // Format: { email: 'Invalid email', password: 'Too short' }
  Object.entries(details).forEach(([field, message]) => {
    if (field !== 'errors' && field !== 'fields') {
      errors.push({
        field,
        message: typeof message === 'string' ? message : getValidationFieldMessage(field),
      });
    }
  });

  return errors;
};

/**
 * Format validation errors as a single message
 */
export const formatValidationErrors = (errors: ValidationError[]): string => {
  if (errors.length === 0) {
    return '';
  }

  if (errors.length === 1) {
    return errors[0].message;
  }

  return `Multiple errors:\n${errors.map((e) => `• ${e.message}`).join('\n')}`;
};

/**
 * Get retry recommendation text based on error code
 */
export const getRetryRecommendation = (code: string): string | null => {
  const retryableCodes = [
    'TIMEOUT_ERROR',
    'NETWORK_ERROR',
    'SERVICE_UNAVAILABLE',
    'QUEUE_ERROR',
    'PROCESSING_FAILED',
    'GENERATION_FAILED',
    'UPLOAD_FAILED',
    'DOWNLOAD_FAILED',
  ];

  if (retryableCodes.includes(code)) {
    return 'Please try again in a few moments.';
  }

  return null;
};

/**
 * Check if error is a validation error
 */
export const isValidationError = (statusCode: number, code?: string): boolean => {
  return (
    statusCode === 400 ||
    statusCode === 422 ||
    code === 'INVALID_PARAMETERS' ||
    code === 'INVALID_FORMAT' ||
    code === 'MISSING_REQUIRED_FIELD'
  );
};

/**
 * Check if error should show contact support message
 */
export const shouldShowSupportMessage = (
  statusCode: number,
  code?: string
): boolean => {
  const supportCodes = [
    'DATABASE_ERROR',
    'STORAGE_ERROR',
    'INTERNAL_ERROR',
    'UNKNOWN_ERROR',
  ];

  return (
    statusCode >= 500 ||
    (code !== undefined && supportCodes.includes(code))
  );
};
