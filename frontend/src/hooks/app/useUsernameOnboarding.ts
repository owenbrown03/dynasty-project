import { useState } from 'react';

import { useAuth } from '@/hooks/auth/useAuth';
import { useSleeperAuth } from '@/hooks/sleeper/useSleeperAuth';
import { useUsernameDataSync } from '@/hooks/app/useUsernameDataSync';
import { notify } from '@/utils/notify';

type Status =
  | 'idle'
  | 'syncing'
  | 'auth-required'
  | 'sleeper-linking'
  | 'complete'
  | 'error';

export const useUsernameOnboarding = () => {
  const auth = useAuth();
  const sleeper = useSleeperAuth();
  const { performUsernameDataSync } = useUsernameDataSync();

  const [status, setStatus] = useState<Status>('idle');
  const [username, setUsername] = useState<string | null>(null);

  const submitUsername = async (input: string) => {
    const trimmed = input.trim();
    if (!trimmed) return;

    setStatus('syncing');

    const toastId = notify.loading('Syncing profile...');

    try {
      // 1. sync external data
      await performUsernameDataSync(trimmed);

      setUsername(trimmed);

      // 2. if not logged in → require auth
      if (!auth.isLoggedIn) {
        setStatus('auth-required');
        auth.openAuth();
        notify.dismiss(toastId);
        return;
      }

      // 3. if logged in but sleeper not linked → open sleeper flow
      if (!sleeper.username) {
        setStatus('sleeper-linking');
        sleeper.openAuth();
        notify.dismiss(toastId);
        return;
      }

      // 4. fully complete
      setStatus('complete');
      notify.success('Profile ready!');
    } catch (err) {
      setStatus('error');
      notify.error('Failed to sync profile');
    } finally {
      notify.dismiss(toastId);
    }
  };

  return {
    status,
    username,
    submitUsername,
  };
};