/**
 * TransitionPicker Component
 * Dropdown menu for selecting clip transitions
 */

import React, { useState, useRef, useEffect } from 'react';
import type { TransitionType } from '@/utils/timeline';
import styles from './TransitionPicker.module.css';

export interface TransitionPickerProps {
  /** Currently selected transition */
  currentTransition: TransitionType;
  /** Callback when transition is selected */
  onSelect: (transition: TransitionType) => void;
  /** Position of the picker */
  position?: 'in' | 'out';
  /** Additional CSS classes */
  className?: string;
}

const TRANSITION_OPTIONS: Array<{
  type: TransitionType;
  label: string;
  icon: string;
  description: string;
}> = [
  {
    type: 'cut',
    label: 'Cut',
    icon: '✂️',
    description: 'Instant transition',
  },
  {
    type: 'fade',
    label: 'Fade',
    icon: '🌓',
    description: 'Fade to/from black',
  },
  {
    type: 'dissolve',
    label: 'Dissolve',
    icon: '⚡',
    description: 'Cross-dissolve blend',
  },
  {
    type: 'wipe',
    label: 'Wipe',
    icon: '➡️',
    description: 'Directional wipe',
  },
];

/**
 * TransitionPicker Component
 * Shows transition icon and opens dropdown menu on click
 */
export const TransitionPicker: React.FC<TransitionPickerProps> = ({
  currentTransition,
  onSelect,
  position = 'out',
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentOption = TRANSITION_OPTIONS.find(opt => opt.type === currentTransition);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  const handleSelect = (transition: TransitionType) => {
    onSelect(transition);
    setIsOpen(false);
  };

  return (
    <div ref={dropdownRef} className={`${styles.transitionPicker} ${className}`}>
      {/* Transition button */}
      <button
        className={styles.transitionPicker__button}
        onClick={() => setIsOpen(!isOpen)}
        title={`${position === 'in' ? 'Transition In' : 'Transition Out'}: ${currentOption?.label}`}
        type="button"
      >
        <span className={styles.transitionPicker__icon}>
          {currentOption?.icon || '✂️'}
        </span>
      </button>

      {/* Dropdown menu */}
      {isOpen && (
        <div className={styles.transitionPicker__dropdown}>
          <div className={styles.transitionPicker__header}>
            Select Transition {position === 'in' ? 'In' : 'Out'}
          </div>
          <div className={styles.transitionPicker__options}>
            {TRANSITION_OPTIONS.map(option => (
              <button
                key={option.type}
                className={`${styles.transitionPicker__option} ${
                  option.type === currentTransition ? styles['transitionPicker__option--active'] : ''
                }`}
                onClick={() => handleSelect(option.type)}
                type="button"
              >
                <span className={styles.transitionPicker__optionIcon}>
                  {option.icon}
                </span>
                <div className={styles.transitionPicker__optionContent}>
                  <div className={styles.transitionPicker__optionLabel}>
                    {option.label}
                  </div>
                  <div className={styles.transitionPicker__optionDescription}>
                    {option.description}
                  </div>
                </div>
                {option.type === currentTransition && (
                  <span className={styles.transitionPicker__checkmark}>✓</span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

TransitionPicker.displayName = 'TransitionPicker';
