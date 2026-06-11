import { useState } from 'react';
import HCaptcha from '@hcaptcha/react-hcaptcha';

import { useSleeperAuthContext } from '@/context/SleeperAuthContext';

interface Props {
  onVerify: (code: string) => Promise<void>;
  onBack: () => void;
  loading?: boolean;
}

export const VerifyForm = ({ onVerify, onBack, loading }: Props) => {
  const authContext = useSleeperAuthContext();
  const [code, setCode] = useState('');
  
  const handleSubmit = async (e: React.SubmitEvent) => {
    e.preventDefault();
    await onVerify(code);
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Verify Code</h2>

      <input
        value={code}
        onChange={(e) => setCode(e.target.value)}
        placeholder="Verification code"
        required
      />

      <HCaptcha
          sitekey={import.meta.env.VITE_HCAPTCHA_SITE_KEY}
          onVerify={(token) => authContext.setCaptcha(token)}
          onExpire={() => authContext.setCaptcha(null)}
        />

      <button disabled={loading}>
        {loading ? 'Verifying...' : 'Verify'}
      </button>

      <p>
        <span onClick={onBack} className="link">
          Back
        </span>
      </p>
    </form>
  );
};