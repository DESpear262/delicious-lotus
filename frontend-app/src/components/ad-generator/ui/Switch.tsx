import React from 'react';
import styles from './Switch.module.css';

export interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  description?: string;
  disabled?: boolean;
  id?: string;
}

export const Switch: React.FC<SwitchProps> = ({
  checked,
  onChange,
  label,
  description,
  disabled = false,
  id,
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!disabled) {
      onChange(e.target.checked);
    }
  };

  return (
    <div className={styles.container}>
      <label className={styles.switchLabel} htmlFor={id}>
        <input
          type="checkbox"
          id={id}
          className={styles.switchInput}
          checked={checked}
          onChange={handleChange}
          disabled={disabled}
        />
        <span className={styles.switchSlider} />
        {label && <span className={styles.switchText}>{label}</span>}
      </label>
      {description && <p className={styles.description}>{description}</p>}
    </div>
  );
};

