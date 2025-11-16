/**
 * Generation Form State Management Hook
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import type { AdCreativeFormData } from '@/types/form';
import { createGeneration } from '@/api/services/generation';
import { useFormValidation } from './useFormValidation';
import { useFormPersistence } from './useFormPersistence';
import type { CreateGenerationRequest } from '@/api/types';

const INITIAL_STATE: AdCreativeFormData = {
  prompt: '',
  brandName: '',
  brandLogo: null,
  brandColors: {
    primary: '#2563eb',
    secondary: '#10b981',
  },
  includeCta: false,
  ctaText: '',
  duration: 30,
  aspectRatio: '16:9',
  style: 'professional',
  musicStyle: 'corporate',
  parallelizeGenerations: false,
};

export function useGenerationForm() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3 | 4>(1);
  const [formData, setFormData] = useState<AdCreativeFormData>(INITIAL_STATE);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    errors,
    validateCurrentStep,
    validateSingleField,
    touchField,
    clearFieldError,
    clearErrors,
  } = useFormValidation();

  /**
   * Handle form data restoration from localStorage
   */
  const handleRestore = useCallback((data: AdCreativeFormData) => {
    setFormData(data);
  }, []);

  const {
    clearStorage,
    showRestoreDialog,
    handleResume,
    handleDiscard,
  } = useFormPersistence(formData, handleRestore);

  /**
   * Update a single field
   */
  const updateField = useCallback(
    (field: keyof AdCreativeFormData, value: any) => {
      setFormData((prev) => {
        // Handle nested fields (e.g., brandColors.primary)
        if (field.includes('.')) {
          const [parent, child] = field.split('.') as [keyof AdCreativeFormData, string];
          return {
            ...prev,
            [parent]: {
              ...(prev[parent] as any),
              [child]: value,
            },
          };
        }

        return {
          ...prev,
          [field]: value,
        };
      });

      clearFieldError(field as string);
      setSubmitError(null);
    },
    [clearFieldError]
  );

  /**
   * Update multiple fields at once
   */
  const updateMultipleFields = useCallback(
    (updates: Partial<AdCreativeFormData>) => {
      setFormData((prev) => ({ ...prev, ...updates }));
      clearErrors();
      setSubmitError(null);
    },
    [clearErrors]
  );

  /**
   * Handle field blur (validate on blur)
   */
  const handleFieldBlur = useCallback(
    (field: string, value: any) => {
      touchField(field);
      validateSingleField(field, value, currentStep, formData);
    },
    [touchField, validateSingleField, currentStep, formData]
  );

  /**
   * Navigate to next step
   */
  const nextStep = useCallback(() => {
    const isValid = validateCurrentStep(currentStep, formData);

    if (!isValid) {
      // Scroll to first error
      const firstErrorElement = document.querySelector('[aria-invalid="true"]');
      if (firstErrorElement) {
        firstErrorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      return false;
    }

    if (currentStep < 4) {
      setCurrentStep((prev) => (prev + 1) as 1 | 2 | 3 | 4);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    return true;
  }, [currentStep, formData, validateCurrentStep]);

  /**
   * Navigate to previous step
   */
  const previousStep = useCallback(() => {
    if (currentStep > 1) {
      setCurrentStep((prev) => (prev - 1) as 1 | 2 | 3 | 4);
      window.scrollTo({ top: 0, behavior: 'smooth' });
      clearErrors();
    }
  }, [currentStep, clearErrors]);

  /**
   * Navigate to a specific step
   */
  const goToStep = useCallback((step: 1 | 2 | 3 | 4) => {
    setCurrentStep(step);
    window.scrollTo({ top: 0, behavior: 'smooth' });
    clearErrors();
  }, [clearErrors]);

  /**
   * Build API request from form data
   */
  const buildRequest = useCallback((): CreateGenerationRequest => {
    return {
      prompt: formData.prompt,
      parameters: {
        duration_seconds: formData.duration,
        aspect_ratio: formData.aspectRatio,
        style: formData.style,
        brand: formData.brandName
          ? {
              name: formData.brandName,
              colors: [formData.brandColors.primary, formData.brandColors.secondary],
              logo_url: formData.brandLogo?.url,
            }
          : undefined,
        include_cta: formData.includeCta,
        cta_text: formData.includeCta ? formData.ctaText : undefined,
        music_style: formData.musicStyle,
      },
      options: {
        quality: 'high',
        fast_generation: false,
        parallelize_generations: formData.parallelizeGenerations,
      },
    };
  }, [formData]);

  /**
   * Submit the form
   */
  const submitForm = useCallback(async () => {
    // Final validation
    const isValid = validateCurrentStep(4, formData);
    if (!isValid) {
      setSubmitError('Please fix all errors before submitting');
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const request = buildRequest();
      const response = await createGeneration(request);

      // Clear localStorage draft on success
      clearStorage();

      // Navigate to progress page
      navigate(`/generation/${response.generation_id}`);
    } catch (error: any) {
      console.error('Failed to create generation:', error);

      // Map error to user-friendly message
      let errorMessage = 'Failed to create video. Please try again.';

      if (error.response?.data?.error) {
        const errorCode = error.response.data.error;
        const errorMessages: Record<string, string> = {
          INVALID_PROMPT: 'Your prompt doesn\'t meet requirements. Please revise.',
          INVALID_PARAMETERS: 'Some parameters are invalid. Please check your settings.',
          RATE_LIMIT_EXCEEDED: 'You\'ve submitted too many requests. Please try again later.',
          INSUFFICIENT_CREDITS: 'You don\'t have enough credits to create this video.',
          UPLOAD_FAILED: 'Logo upload failed. Please try again.',
        };
        errorMessage = errorMessages[errorCode] || errorMessage;
      } else if (error.message) {
        errorMessage = error.message;
      }

      setSubmitError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  }, [formData, validateCurrentStep, buildRequest, clearStorage, navigate]);

  /**
   * Reset form to initial state
   */
  const resetForm = useCallback(() => {
    setFormData(INITIAL_STATE);
    setCurrentStep(1);
    clearErrors();
    setSubmitError(null);
    clearStorage();
  }, [clearErrors, clearStorage]);

  return {
    // State
    currentStep,
    formData,
    errors,
    // Form persistence dialog
    showRestoreDialog,
    handleResume,
    handleDiscard,
    isSubmitting,
    submitError,

    // Actions
    updateField,
    updateMultipleFields,
    handleFieldBlur,
    nextStep,
    previousStep,
    goToStep,
    submitForm,
    resetForm,
  };
}
