import { useEffect, useState } from 'react';
import HCaptcha from '@hcaptcha/react-hcaptcha';

import { useSleeperAuthContext } from '@/context/useSleeperAuthContext';

interface Props {
  initialUsername?: string | null;
  onSend: (username: string, captcha: string) => Promise<void>;
  loading?: boolean;
}

export const SendForm = ({
  initialUsername,
  onSend,
  loading,
}: Props) => {
  const [username, setUsername] = useState(
    initialUsername ?? '',
  );

  const authContext = useSleeperAuthContext();

  useEffect(() => {
    setUsername(initialUsername ?? '');
  }, [initialUsername]);

  const handleSubmit = async (e: React.SubmitEvent) => {
    e.preventDefault();
    if (!authContext.captcha) {
      throw new Error("Captcha not solved");
    }
    await onSend(username, authContext.captcha!);
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Connect Sleeper</h2>

      <input
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        placeholder="Sleeper username"
        required
      />

      <HCaptcha
        sitekey={import.meta.env.VITE_HCAPTCHA_SITE_KEY}
        onVerify={(token) => authContext.setCaptcha(token)}
        onExpire={() => authContext.setCaptcha(null)}
      />

      <button disabled={loading}>
        {loading ? 'Sending...' : 'Send Code'}
      </button>
    </form>
  );
};
