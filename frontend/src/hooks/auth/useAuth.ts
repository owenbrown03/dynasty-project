import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';

import { api } from '@/api/v1/endpoints';
import { notify } from '@/utils/notify';
import { useAuthContext } from '@/context/AuthContext'
import { useSleeperConnection } from '../sleeper/useConnection';
import type { MeRequest } from '@/types';

const KEY = ['me'] as const;

export function useAuth() {
  const queryClient = useQueryClient();
  const authContext = useAuthContext();
  const { reconcileConnection } = useSleeperConnection();

  const query = useQuery<MeRequest>({
    queryKey: KEY,
    queryFn: api.auth.me,
    retry: (failureCount, error: any) => {
        if (error?.response?.status === 401) {
          return false;
        }
        return failureCount < 3;
      },
    staleTime: 0,
  });

  const loginMutation = useMutation({
    mutationFn: api.auth.login,
    onSuccess: async () => {
      authContext.close();
      queryClient.invalidateQueries({ queryKey: KEY });
      reconcileConnection();
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
      queryClient.invalidateQueries({ queryKey: KEY });
      queryClient.setQueryData(['sleeper-connection'], null);
      queryClient.invalidateQueries({ queryKey: ['sleeper-connection'] });
      notify.success('Successfully logged out.');
    },
    onError: () => {
      notify.error('Log out failed');
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
    login,
    register,
    logout,

    isLoggedIn: !!query.data?.authenticated,

    isLoggingIn: loginMutation.isPending,
    isRegistering: registerMutation.isPending,
    isLoggingOut: logoutMutation.isPending,
  };
}