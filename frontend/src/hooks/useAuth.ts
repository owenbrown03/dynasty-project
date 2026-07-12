import { useMutation, useQueryClient } from '@tanstack/react-query';

import { BOOTSTRAP_QUERY_KEY } from '@/api/query-keys';
import { api } from '@/api/v1/endpoints';
import type { EmailVerificationRequestResponse } from '@/types';
import { notify } from '@/utils/notify';
import { useAuthContext } from '@/context/useAuthContext'
import { useBootstrap } from './useBootstrap';

async function handleVerificationDelivery(
  response: {
    data: EmailVerificationRequestResponse;
  },
) {
  if (response.data.delivery === 'smtp') {
    notify.success('Verification email sent.');
    return;
  }

  if (response.data.verification_url) {
    try {
      await navigator.clipboard.writeText(
        response.data.verification_url,
      );
      notify.success(
        'SMTP is not configured here. Verification link copied to clipboard.',
      );
      return;
    } catch {
      notify.success(
        `SMTP is not configured here. Open this verification link: ${response.data.verification_url}`,
      );
      return;
    }
  }

  notify.success(
    'Verification link generated. Check backend logs in local development.',
  );
}

export function useAuth() {
  const queryClient = useQueryClient();
  const authContext = useAuthContext();
  const bootstrapQuery = useBootstrap();

  const loginMutation = useMutation({
    mutationFn: api.auth.login,

    onSuccess: async () => {
      authContext.close();
      await queryClient.invalidateQueries({
        queryKey: BOOTSTRAP_QUERY_KEY,
      });

      notify.success('Successfully logged in!');
    },

    onError: () => {
      notify.error('Login failed.');
    },
  });


  const registerMutation = useMutation({
    mutationFn: api.auth.register,

    onSuccess: async () => {
      authContext.close();
      await queryClient.invalidateQueries({
        queryKey: BOOTSTRAP_QUERY_KEY,
      });

      const resendResponse = await api.auth.resendVerificationEmail();
      await handleVerificationDelivery(
        resendResponse,
      );
    },

    onError: () => {
      notify.error('Register failed.');
    },
  });


  const resendVerificationMutation = useMutation({
    mutationFn: api.auth.resendVerificationEmail,

    onSuccess: async (response) => {
      await queryClient.invalidateQueries({
        queryKey: BOOTSTRAP_QUERY_KEY,
      });

      await handleVerificationDelivery(
        response,
      );
    },

    onError: () => {
      notify.error('Unable to send verification email.');
    },
  });


  const verifyEmailMutation = useMutation({
    mutationFn: api.auth.verifyEmail,

    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: BOOTSTRAP_QUERY_KEY,
      });

      notify.success('Email verified.');
    },

    onError: () => {
      notify.error('Email verification failed.');
    },
  });


  const logoutMutation = useMutation({
    mutationFn: api.auth.logout,

    onSuccess: () => {
      queryClient.setQueryData(
        BOOTSTRAP_QUERY_KEY,
        null,
      );

      notify.success('Successfully logged out.');
    },

    onError: () => {
      notify.error('Log out failed.');
    },
  });


  const login = async (email: string, password: string): Promise<void> => {
    await loginMutation.mutateAsync({ email, password });
  };

  const register = async (email: string, password: string): Promise<void> => {
    await registerMutation.mutateAsync({ email, password });
  };

  const logout = async (): Promise<void> => {
    await logoutMutation.mutateAsync();
  };

  const resendVerificationEmail = async (): Promise<void> => {
    await resendVerificationMutation.mutateAsync();
  };

  const verifyEmail = async (token: string): Promise<void> => {
    await verifyEmailMutation.mutateAsync({ token });
  };

  return {
    siteUser: bootstrapQuery.data?.site_user ?? null,
    sleeper: bootstrapQuery.data?.sleeper ?? null,
    isLoggedIn: bootstrapQuery.data?.authenticated ?? false,
    isEmailVerified: (
      bootstrapQuery.data?.site_user?.email_verified
      ?? false
    ),

    isLoading: bootstrapQuery.isLoading,

    login,
    register,
    logout,
    resendVerificationEmail,
    verifyEmail,

    isLoggingIn: loginMutation.isPending,
    isRegistering: registerMutation.isPending,
    isLoggingOut: logoutMutation.isPending,
    isResendingVerificationEmail: resendVerificationMutation.isPending,
    isVerifyingEmail: verifyEmailMutation.isPending,
  };
}
