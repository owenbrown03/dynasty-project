import { useMutation, useQueryClient } from '@tanstack/react-query';

import { api } from '@/api/v1/endpoints';
import { notify } from '@/utils/notify';
import { useAuthContext } from '@/context/useAuthContext'
import { useBootstrap } from './useBootstrap';

const KEY = ['bootstrap'] as const;

export function useAuth() {
  const queryClient = useQueryClient();
  const authContext = useAuthContext();
  const bootstrapQuery = useBootstrap();

  const loginMutation = useMutation({
    mutationFn: api.auth.login,

    onSuccess: async () => {
      authContext.close();
      await queryClient.invalidateQueries({
        queryKey: KEY,
      });

      notify.success('Successfully logged in!');
    },

    onError: () => {
      notify.error('Login failed.');
    },
  });


  const registerMutation = useMutation({
    mutationFn: api.auth.register,

    onSuccess: () => {
      notify.success('Successfully registered!');
    },

    onError: () => {
      notify.error('Register failed.');
    },
  });


  const logoutMutation = useMutation({
    mutationFn: api.auth.logout,

    onSuccess: () => {
      queryClient.setQueryData(KEY, null);

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

  return {
    siteUser: bootstrapQuery.data?.site_user ?? null,
    sleeper: bootstrapQuery.data?.sleeper ?? null,
    isLoggedIn: bootstrapQuery.data?.authenticated ?? false,

    isLoading: bootstrapQuery.isLoading,

    login,
    register,
    logout,

    isLoggingIn: loginMutation.isPending,
    isRegistering: registerMutation.isPending,
    isLoggingOut: logoutMutation.isPending,
  };
}
