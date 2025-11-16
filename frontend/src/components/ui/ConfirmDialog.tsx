import React from 'react';
import { Card, CardHeader, CardBody } from './Card';
import { Button } from './Button';
import styles from './ConfirmDialog.module.css';

export interface ConfirmDialogProps {
  /** Whether the dialog is visible */
  isOpen: boolean;
  /** Dialog title */
  title: string;
  /** Dialog message */
  message: string;
  /** Label for the confirm/primary button */
  confirmLabel: string;
  /** Label for the cancel/secondary button */
  cancelLabel: string;
  /** Variant for the confirm button */
  confirmVariant?: 'primary' | 'secondary' | 'danger';
  /** Variant for the cancel button */
  cancelVariant?: 'outline' | 'ghost';
  /** Callback when confirm button is clicked */
  onConfirm: () => void;
  /** Callback when cancel button is clicked */
  onCancel: () => void;
}

/**
 * ConfirmDialog Component
 * 
 * A modal confirmation dialog with customizable buttons.
 * Used to replace browser confirm dialogs with styled alternatives.
 */
export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  title,
  message,
  confirmLabel,
  cancelLabel,
  confirmVariant = 'primary',
  cancelVariant = 'outline',
  onConfirm,
  onCancel,
}) => {
  if (!isOpen) return null;

  return (
    <div
      className={styles.overlay}
      onClick={onCancel}
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-message"
    >
      <Card
        variant="elevated"
        className={styles.dialog}
        onClick={(e) => e.stopPropagation()}
      >
        <CardHeader title={title} />
        <CardBody>
          <p id="confirm-dialog-message" className={styles.message}>
            {message}
          </p>
          <div className={styles.actions}>
            <Button
              onClick={onCancel}
              variant={cancelVariant}
              fullWidth
            >
              {cancelLabel}
            </Button>
            <Button
              onClick={onConfirm}
              variant={confirmVariant}
              fullWidth
            >
              {confirmLabel}
            </Button>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

ConfirmDialog.displayName = 'ConfirmDialog';

