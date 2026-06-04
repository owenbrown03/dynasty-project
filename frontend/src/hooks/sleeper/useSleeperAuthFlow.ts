import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

import { api } from '@/api/v1/endpoints';

export const useSleeperAuthFlow = () => {
  const [step, setStep] = useState<'send' | 'verify'>('send');
  const [username, setUsername] = useState<string | null>(null);

  // -------------------------
  // SEND CODE
  // -------------------------
  const sendMutation = useMutation({
    mutationFn: api.sleeper_auth.sendCode,
  });

  const sendCode = async (username: string, captcha: string) => {
    await sendMutation.mutateAsync({ username, captcha });
    setUsername(username);
    setStep('verify');
  };

  // -------------------------
  // VERIFY CODE
  // -------------------------
  const verifyMutation = useMutation({
    mutationFn: api.sleeper_auth.verifyCode,
  });

  const verifyCode = async (code: string) => {
    if (!username) return;

    await verifyMutation.mutateAsync({
      username,
      code,
    });

    setStep('send');
  };

  const reset = () => {
    setStep('send');
    setUsername(null);
  };

  return {
    step,
    username,

    sendCode,
    verifyCode,
    reset,

    isSending: sendMutation.isPending,
    isVerifying: verifyMutation.isPending,
  };
};