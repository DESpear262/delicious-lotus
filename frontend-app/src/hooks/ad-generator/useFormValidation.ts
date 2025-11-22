/**
 * Form Validation Hook
 */

import { useState, useCallback } from 'react';
import type { AdCreativeFormData, FormErrors } from '@/types/ad-generator/form';
import { validateStep, validateField, VALIDATION_RULES } from '@/utils/ad-generator/formValidation';

export function useFormValidation() {
  const [errors, setErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  /**
   * Validate a specific step
   */
  const validateCurrentStep = useCallback(
    (step: number, formData: AdCreativeFormData): boolean => {
      const stepErrors = validateStep(step, formData);
      setErrors(stepErrors);
      return Object.keys(stepErrors).length === 0;
    },
    []
  );

  /**
   * Validate a single field
   */
  const validateSingleField = useCallback(
    (fieldName: string, value: any, step: number, formData: AdCreativeFormData) => {
      const stepRules = VALIDATION_RULES[step];
      const rule = stepRules?.[fieldName];

      if (!rule) {
        return;
      }

      const error = validateField(fieldName, value, rule, formData);

      setErrors((prev) => {
        const next = { ...prev };
        if (error) {
          next[fieldName] = error;
        } else {
          delete next[fieldName];
        }
        return next;
      });
    },
    []
  );

  /**
   * Mark a field as touched
   */
  const touchField = useCallback((fieldName: string) => {
    setTouched((prev) => ({ ...prev, [fieldName]: true }));
  }, []);

  /**
   * Clear errors for a specific field
   */
  const clearFieldError = useCallback((fieldName: string) => {
    setErrors((prev) => {
      const next = { ...prev };
      delete next[fieldName];
      return next;
    });
  }, []);

  /**
   * Clear all errors
   */
  const clearErrors = useCallback(() => {
    setErrors({});
  }, []);

  /**
   * Reset touched fields
   */
  const resetTouched = useCallback(() => {
    setTouched({});
  }, []);

  return {
    errors,
    touched,
    validateCurrentStep,
    validateSingleField,
    touchField,
    clearFieldError,
    clearErrors,
    resetTouched,
  };
}
