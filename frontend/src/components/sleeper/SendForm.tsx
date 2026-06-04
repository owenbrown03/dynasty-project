import { useState } from 'react';
import HCaptcha from '@hcaptcha/react-hcaptcha';

interface Props {
  onSend: (username: string, captcha: string) => Promise<void> | void;
  loading?: boolean;
}

export const SendForm = ({ onSend, loading }: Props) => {
  const [username, setUsername] = useState('');
  const [captcha, setCaptcha] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!captcha) return;

    await onSend(username, captcha);
  };

  return (
    <form onSubmit={handleSubmit} className="auth-form">
      <h2>Connect Sleeper</h2>

      <input
        type="text"
        placeholder="Sleeper Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        required
      />

      <HCaptcha
        sitekey="ecc67a72-2e44-4722-a788-9e7070282f72"
        onVerify={(token) => setCaptcha(token)}
      />

      <button type="submit" disabled={!captcha || loading}>
        {loading ? 'Sending...' : 'Send Code'}
      </button>
    </form>
  );
};