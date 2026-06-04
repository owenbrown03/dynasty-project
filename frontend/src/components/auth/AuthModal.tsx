import { useEffect, useRef, useState } from 'react';

import './AuthModal.css';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AuthModal = ({ isOpen, onClose }: AuthModalProps) => {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [view, setView] = useState<'login' | 'register'>('login');

  useEffect(() => {
    if (isOpen) {
      setView('login');
    }
  }, [isOpen]);

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

  const handleClose = () => {
    onClose();
  };

  return (
    <dialog ref={dialogRef} className="auth-modal" onClose={handleClose}>
      <button onClick={handleClose} className="close-btn">
        ×
      </button>

      {view === 'login' ? (
        <LoginForm
          onSwitchView={() => setView('register')}
          onClose={handleClose}
        />
      ) : (
        <RegisterForm
          onSwitchView={() => setView('login')}
          onClose={handleClose}
        />
      )}
    </dialog>
  );
};