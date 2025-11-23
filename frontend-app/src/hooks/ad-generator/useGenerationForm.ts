/**
 * Generation Form State Management Hook
 */

import { useState, useCallback, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import type { AdCreativeFormData } from '@/types/ad-generator/form';
import { createGeneration, generateVideoClipPrompts } from '@/services/ad-generator/services/generation';
import { useFormValidation } from './useFormValidation';
import { useProjectStore } from '@/contexts/StoreContext';
import type {
  CreateGenerationRequest,
  CreateGenerationResponse,
  VideoPromptRequest,
  VideoPromptResponse,
} from '@/services/ad-generator/types';

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
  const [searchParams] = useSearchParams();
  const projectIdParam = searchParams.get('projectId');

  const [currentStep, setCurrentStep] = useState<1 | 2 | 3 | 4>(1);
  const [formData, setFormData] = useState<AdCreativeFormData>(INITIAL_STATE);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<CreateGenerationResponse | null>(null);
  const [promptResult, setPromptResult] = useState<VideoPromptResponse | null>(null);
  const [promptError, setPromptError] = useState<string | null>(null);
  const [isGeneratingPrompts, setIsGeneratingPrompts] = useState(false);

  // Project Store Integration
  const currentProjectId = useProjectStore((state) => state.currentProjectId);
  const compositionConfig = useProjectStore((state) => state.compositionConfig);
  const addProject = useProjectStore((state) => state.addProject);
  const loadProject = useProjectStore((state) => state.loadProject);
  const setCurrentProject = useProjectStore((state) => state.setCurrentProject);
  const updateCompositionConfig = useProjectStore((state) => state.updateCompositionConfig);
  const saveProject = useProjectStore((state) => state.saveProject);

  const {
    errors,
    validateCurrentStep,
    validateSingleField,
    touchField,
    clearFieldError,
    clearErrors,
  } = useFormValidation();

  /**
   * Initialize or Load Project
   */
  useEffect(() => {
    const initProject = async () => {
      if (projectIdParam) {
        // Case 1: URL has projectId
        if (currentProjectId !== projectIdParam) {
           try {
             await loadProject(projectIdParam);
           } catch (err) {
             console.error("Failed to load project from URL", err);
             // Fallback: maybe redirect to home or show error?
           }
        }
      } else if (!currentProjectId) {
        // Case 2: No URL param and no current project in store
        // Create a new temporary/persisted project
        try {
          const newId = await addProject(
            { 
               name: `Ad Campaign ${new Date().toLocaleTimeString()}`, 
               description: 'Auto-generated ad campaign',
               type: 'ad-creative'
            },
            { aspectRatio: '16:9' }
          );
          // Update URL to reflect new project
          navigate(`?projectId=${newId}`, { replace: true });
        } catch (err) {
           console.error("Failed to auto-create project", err);
        }
      }
    };

    initProject();
  }, [projectIdParam, currentProjectId, loadProject, addProject, navigate]);

  /**
   * Sync Store State to Form
   */
  useEffect(() => {
      if (currentProjectId && compositionConfig?.adWizard) {
        const { formData: savedData, currentStep: savedStep, promptResult: savedPrompts } = compositionConfig.adWizard;
        
        // Only update if different to avoid loops (basic check)
        if (savedData && JSON.stringify(savedData) !== JSON.stringify(formData)) {
             setFormData(savedData);
        }
        if (savedStep && savedStep !== currentStep) {
            setCurrentStep(savedStep);
        }
        if (savedPrompts) {
            setPromptResult(savedPrompts);
        }
      }
  }, [currentProjectId, compositionConfig]); // Careful with dependencies here to avoid loops if we were updating store on every render

  /**
   * Persist state to Project Store
   */
  const persistState = useCallback((data: AdCreativeFormData, step: 1 | 2 | 3 | 4, prompts?: VideoPromptResponse | null) => {
    if (!currentProjectId) return;

    updateCompositionConfig({
      adWizard: {
        formData: data,
        currentStep: step,
        promptResult: prompts ?? promptResult 
      }
    });
    saveProject().catch(err => console.error("Auto-save failed", err));
  }, [currentProjectId, updateCompositionConfig, promptResult, saveProject]);



  /**
   * Update a single field
   */
  const updateField = useCallback(
    (field: string | keyof AdCreativeFormData, value: any) => {
      let newFormData = { ...formData };
      
      // Handle nested fields (e.g., brandColors.primary)
      if (field.includes('.')) {
        const [parent, child] = field.split('.') as [keyof AdCreativeFormData, string];
        newFormData = {
          ...newFormData,
          [parent]: {
            ...(newFormData[parent] as any),
            [child]: value,
          },
        };
      } else {
        newFormData = {
          ...newFormData,
          [field]: value,
        };
      }

      setFormData(newFormData);
      persistState(newFormData, currentStep);
      clearFieldError(field as string);
      setSubmitError(null);
    },
    [formData, currentStep, persistState, clearFieldError]
  );

  /**
   * Update multiple fields at once
   */
  const updateMultipleFields = useCallback(
    (updates: Partial<AdCreativeFormData>) => {
      const newFormData = { ...formData, ...updates };
      setFormData(newFormData);
      persistState(newFormData, currentStep);
      clearErrors();
      setSubmitError(null);
    },
    [formData, currentStep, persistState, clearErrors]
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
      const next = (currentStep + 1) as 1 | 2 | 3 | 4;
      setCurrentStep(next);
      persistState(formData, next);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    return true;
  }, [currentStep, formData, validateCurrentStep, persistState]);

  /**
   * Navigate to previous step
   */
  const previousStep = useCallback(() => {
    if (currentStep > 1) {
      const prev = (currentStep - 1) as 1 | 2 | 3 | 4;
      setCurrentStep(prev);
      persistState(formData, prev);
      window.scrollTo({ top: 0, behavior: 'smooth' });
      clearErrors();
    }
  }, [currentStep, formData, persistState, clearErrors]);

  /**
   * Navigate to a specific step
   */
  const goToStep = useCallback((step: 1 | 2 | 3 | 4) => {
    setCurrentStep(step);
    persistState(formData, step);
    window.scrollTo({ top: 0, behavior: 'smooth' });
    clearErrors();
  }, [formData, persistState, clearErrors]);

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
            colors: {
              primary: [formData.brandColors.primary],
              secondary: formData.brandColors.secondary
                ? [formData.brandColors.secondary]
                : undefined,
            },
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
    setAnalysisResult(null);
    setPromptResult(null);

    try {
      const request = buildRequest();
      const response = await createGeneration(request);

      // Save analysis result to project state? Maybe later.
      
      // Surface analysis output to the UI
      setAnalysisResult(response);
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
  }, [formData, validateCurrentStep, buildRequest]);

  /**
   * Generate clip-level prompts via backend OpenAI helper
   */
  const generatePrompts = useCallback(async () => {
    setPromptError(null);
    setPromptResult(null);
    setIsGeneratingPrompts(true);

    try {
      // Derive a sensible number of clips from duration (default 5s each, clamp 3-10 clips)
      const estimatedClips = Math.max(3, Math.min(10, Math.round(formData.duration / 5)));
      const clipLength = Math.max(
        3,
        Math.min(10, Math.round(formData.duration / Math.max(estimatedClips, 1)))
      );

      const request: VideoPromptRequest = {
        prompt: formData.prompt,
        num_clips: estimatedClips,
        clip_length: clipLength,
      };

      const response = await generateVideoClipPrompts(request);
      setPromptResult(response);
      
      // Persist results to project
      persistState(formData, currentStep, response);
      
      // Also save to sessionStorage for legacy support/backup
      sessionStorage.setItem('promptResult', JSON.stringify(response));
      
      navigate('/ad-generator/prompt-results');
    } catch (error: any) {
      console.error('Failed to generate clip prompts:', error);
      const message = error?.message || 'Failed to generate clip prompts. Please try again.';
      setPromptError(message);
    } finally {
      setIsGeneratingPrompts(false);
    }
  }, [formData, currentStep, navigate, persistState]);

  /**
   * Reset form to initial state
   */
  const resetForm = useCallback(() => {
    setFormData(INITIAL_STATE);
    setCurrentStep(1);
    clearErrors();
    setSubmitError(null);
    // Clear project config? Maybe just reset adWizard part
    if (currentProjectId) {
        updateCompositionConfig({ adWizard: undefined });
    }
  }, [clearErrors, currentProjectId, updateCompositionConfig]);

  return {
    // State
    currentStep,
    formData,
    errors,
    analysisResult,
    promptResult,
    promptError,
    isGeneratingPrompts,
    // Legacy dialog support (can be removed if no longer needed)
    showRestoreDialog: false, 
    handleResume: () => {},
    handleDiscard: () => {},
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
    generatePrompts,
    resetForm,
  };
}
