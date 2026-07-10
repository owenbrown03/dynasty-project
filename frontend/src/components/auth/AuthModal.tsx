import './AuthModal.css';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';
import { useAuthContext } from '@/context/AuthContext';
import { useAuth } from '@/hooks/useAuth';

export const AuthModal = () => {
  const authContext = useAuthContext();
  const auth = useAuth();

  if (!authContext.isOpen) return null;

  return (
    <div className="auth-modal">
      <div className="modal-content">
        <button
          className="button-secondary close-btn"
          onClick={authContext.close}
        >
          ×
        </button>

        {authContext.view === 'login' ? (
          <LoginForm
            onLogin={auth.login}
            onSwitchView={authContext.switchView}
            loading={auth.isLoggingIn}
          />
        ) : (
          <RegisterForm
            onRegister={auth.register}
            onSwitchView={authContext.switchView}
            loading={auth.isRegistering}
          />
        )}
      </div>
    </div>
  );
};
