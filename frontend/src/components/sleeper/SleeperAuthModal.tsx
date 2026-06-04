import { useEffect, useRef } from 'react';

import './SleeperAuthModal.css';
import { SendForm } from './SendForm';
import { VerifyForm } from './VerifyForm';
import { useSleeperAuth } from '@/hooks/sleeper/useSleeperAuth';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const SleeperAuthModal = ({ isOpen, onClose }: Props) => {
  const dialogRef = useRef<HTMLDialogElement>(null);

  const {
    step,
    sendCode,
    verifyCode,
    reset,
    isSending,
    isVerifying,
  } = useSleeperAuth();

  // -----------------------------
  // sync dialog open/close
  // -----------------------------
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen && !dialog.open) {
      dialog.showModal();
    }

    if (!isOpen && dialog.open) {
      dialog.close();
    }
  }, [isOpen]);

  // -----------------------------
  // reset state when opened
  // -----------------------------
  useEffect(() => {
    if (isOpen) {
      reset();
    }
  }, [isOpen]);

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <dialog
      ref={dialogRef}
      onClose={handleClose}
      className="auth-modal"
    >
      <button onClick={handleClose} className="close-btn">
        ×
      </button>

      {step === 'send' ? (
        <SendForm onSend={sendCode} loading={isSending} />
      ) : (
        <VerifyForm
          onVerify={verifyCode}
          onSwitchView={reset}
          loading={isVerifying}
        />
      )}
    </dialog>
  );
};