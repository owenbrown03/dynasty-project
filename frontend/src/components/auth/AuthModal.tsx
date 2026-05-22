import { useEffect, useRef, useState } from 'react';
import './AuthModal.css';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLogin: () => void | Promise<void>;
}

export interface AuthFormProps {
  onSwitchView: () => void;
  onClose: () => void;
  onLogin: () => void | Promise<void>;
}

export const AuthModal = ({ isOpen, onClose, onLogin }: AuthModalProps) => {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [view, setView] = useState<'login' | 'register'>('login');

  useEffect(() => {
      console.log('Entering useEffect in AuthModal');
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (isOpen) {
      dialog.showModal();
    } else {
      dialog.close();
    }
    const handleNativeClose = () => {
      if (isOpen) onClose();
    };
    dialog.addEventListener('close', handleNativeClose);
    return () => {
      dialog.removeEventListener('close', handleNativeClose);
    };
  }, [isOpen, onClose]);

  return (
    <dialog ref={dialogRef} onClose={onClose} className="auth-modal">
      <button onClick={onClose} className="close-btn">×</button>
      
      {view === 'login' ? (
        <LoginForm 
          onSwitchView={() => setView('register')} 
          onClose={onClose}
          onLogin={onLogin}
        />
      ) : (
        <RegisterForm 
          onSwitchView={() => setView('login')} 
          onClose={onClose}
          onLogin={onLogin}
        />
      )}
    </dialog>
  );
};