/**
 * Form Persistence Hook
 * Handles auto-save to localStorage with expiration
 */

import { useEffect, useCallback, useRef, useState } from 'react';
import type { AdCreativeFormData, FormDraft } from '@/types/form';

const STORAGE_KEY = 'ad-creative-form-draft';
const EXPIRY_HOURS = 24;
const DEBOUNCE_MS = 500;
const FORM_VERSION = '1.0';

export function useFormPersistence(
  formData: AdCreativeFormData,
  onRestore?: (data: AdCreativeFormData) => void
) {
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isInitialMount = useRef(true);
  const [showRestoreDialog, setShowRestoreDialog] = useState(false);

  /**
   * Save form data to localStorage
   */
  const saveToStorage = useCallback((data: AdCreativeFormData) => {
    try {
      const draft: FormDraft = {
        data,
        timestamp: Date.now(),
        version: FORM_VERSION,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(draft));
    } catch (error) {
      console.error('Failed to save form draft:', error);
    }
  }, []);

  /**
   * Load form data from localStorage
   */
  const loadFromStorage = useCallback((): AdCreativeFormData | null => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (!saved) {
        return null;
      }

      const draft: FormDraft = JSON.parse(saved);

      // Check version compatibility
      if (draft.version !== FORM_VERSION) {
        localStorage.removeItem(STORAGE_KEY);
        return null;
      }

      // Check expiration
      const ageHours = (Date.now() - draft.timestamp) / (1000 * 60 * 60);
      if (ageHours >= EXPIRY_HOURS) {
        localStorage.removeItem(STORAGE_KEY);
        return null;
      }

      return draft.data;
    } catch (error) {
      console.error('Failed to load form draft:', error);
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
  }, []);

  /**
   * Clear saved draft
   */
  const clearStorage = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      console.error('Failed to clear form draft:', error);
    }
  }, []);

  /**
   * Check if there's a saved draft
   */
  const hasSavedDraft = useCallback((): boolean => {
    const draft = loadFromStorage();
    return draft !== null;
  }, [loadFromStorage]);

  /**
   * Restore saved draft (prompts user)
   */
  const restoreDraft = useCallback(() => {
    const draft = loadFromStorage();
    if (draft && onRestore) {
      onRestore(draft);
      return true;
    }
    return false;
  }, [loadFromStorage, onRestore]);

  /**
   * Debounced auto-save effect
   */
  useEffect(() => {
    // Skip saving on initial mount
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }

    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Set new debounced save timer
    debounceTimerRef.current = setTimeout(() => {
      saveToStorage(formData);
    }, DEBOUNCE_MS);

    // Cleanup
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [formData, saveToStorage]);

  /**
   * Load draft on mount - show dialog instead of browser confirm
   */
  useEffect(() => {
    if (hasSavedDraft() && onRestore) {
      setShowRestoreDialog(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount

  /**
   * Handle resume (restore draft)
   */
  const handleResume = useCallback(() => {
    setShowRestoreDialog(false);
    if (restoreDraft()) {
      // Draft restored successfully
    }
  }, [restoreDraft]);

  /**
   * Handle discard (clear draft)
   */
  const handleDiscard = useCallback(() => {
    setShowRestoreDialog(false);
    clearStorage();
  }, [clearStorage]);

  return {
    saveToStorage,
    loadFromStorage,
    clearStorage,
    hasSavedDraft,
    restoreDraft,
    showRestoreDialog,
    handleResume,
    handleDiscard,
  };
}
