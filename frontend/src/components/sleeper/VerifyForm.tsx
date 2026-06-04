import { useState } from 'react';

interface Props {
  onVerify: (code: string) => Promise<void> | void;
  onSwitchView: () => void;
  loading?: boolean;
}

export const VerifyForm = ({ onVerify, onSwitchView, loading }: Props) => {
  const [code, setCode] = useState('');

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    await onVerify(code);
  };

  return (
    <form onSubmit={handleSubmit} className="auth-form">
      <h2>Verify Code</h2>

      <input
        type="text"
        placeholder="Enter verification code"
        value={code}
        onChange={(e) => setCode(e.target.value)}
        required
      />

      <button type="submit" disabled={loading}>
        {loading ? 'Verifying...' : 'Verify'}
      </button>

      <p>
        <span onClick={onSwitchView} className="link">
          Back
        </span>
      </p>
    </form>
  );
};