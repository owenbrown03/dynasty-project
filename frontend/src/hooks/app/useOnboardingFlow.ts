import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

import { api } from '@/api/v1/endpoints';
import { useAuth } from '@/hooks/auth/useAuth';

export const useOnboardingFlow = () => {
  const auth = useAuth();

  const [isSleeperModalOpen, setSleeperOpen] = useState(false);

  const sendCode = useMutation({
    mutationFn: api.sleeper_auth.sendCode,
  });

  const verifyCode = useMutation({
    mutationFn: api.sleeper_auth.verifyCode,
  });

  const linkSleeper = async (username: string, captcha: string) => {
    await sendCode.mutateAsync({ username, captcha });

    setSleeperOpen(true);
  };

  const verifySleeper = async (code: string, username: string, captcha: string) => {
    await verifyCode.mutateAsync({ username, code, captcha });

    setSleeperOpen(false);
  };

  return {
    // auth
    ...auth,

    // sleeper
    isSleeperModalOpen: isSleeperModalOpen,
    openSleeper: () => setSleeperOpen(true),
    closeSleeper: () => setSleeperOpen(false),

    linkSleeper,
    verifySleeper,

    isSending: sendCode.isPending,
    isVerifying: verifyCode.isPending,
  };
};