import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';

import { api } from '@/api/v1/endpoints';
import { notify } from '@/utils/notify';
import { useSleeperAuthContext } from '@/context/useSleeperAuthContext';

const KEY = ['sleeper-connection'] as const;

export const useSleeperAuth = () => {
  const [connectId, setConnectId] =
    useState<string | null>(null);

  const queryClient = useQueryClient();

  const {
    setUsername,
    setStep,
    close,
  } = useSleeperAuthContext();

  const sendMutation = useMutation({
    mutationFn: api.sleeper_auth.sendCode,

    onSuccess: (response) => {
      setConnectId(response.data.connect_id);

      setStep('verify');

      notify.success(
        'Verification code sent.'
      );
    },
  });

  const verifyMutation = useMutation({
    mutationFn: api.sleeper_auth.verifyCode,

    onSuccess: async () => {
      notify.success(
        'Sleeper account connected!'
      );

      await queryClient.invalidateQueries({
        queryKey: KEY,
      });

      close();
    },
  });

  const send = async (
    usernameInput: string,
    captcha: string,
  ) => {
    const trimmed = usernameInput.trim();

    if (!trimmed) {
      throw new Error(
        'Username missing from auth flow'
      );
    }

    setUsername(trimmed);

    await sendMutation.mutateAsync({
      username: trimmed,
      captcha,
    });
  };

  const verify = async (
    code: string,
    captcha?: string,
  ) => {
    if (!connectId) {
      throw new Error(
        'connectId missing from auth flow'
      );
    }

    await verifyMutation.mutateAsync({
      connect_id: connectId,
      code,
      captcha,
    });
  };

  return {
    send,
    verify,
    isSending: sendMutation.isPending,
    isVerifying: verifyMutation.isPending,
  };
};
