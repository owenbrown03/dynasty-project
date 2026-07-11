import './SleeperAuthModal.css';
import { SendForm } from './SendForm';
import { VerifyForm } from './VerifyForm';
import { useSleeperAuth } from '@/hooks/sleeper/useAuth';
import { useSleeperAuthContext } from '@/context/useSleeperAuthContext';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';

export const SleeperAuthModal = () => {
  const auth = useSleeperAuth();
  const authContext = useSleeperAuthContext();
  const connection = useSleeperConnection();

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

        {authContext.step === 'send' ? (
          <SendForm
            initialUsername={connection.username}
            onSend={auth.send}
            loading={auth.isSending}
          />
        ) : (
          <VerifyForm
            onVerify={auth.verify}
            onBack={authContext.reset}
            loading={auth.isVerifying}
          />
        )}
      </div>
    </div>
  );
};
