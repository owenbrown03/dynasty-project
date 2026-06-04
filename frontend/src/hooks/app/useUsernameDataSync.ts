import { useMutation } from '@tanstack/react-query';
import { api } from '@/api/v1/endpoints';

export const useUsernameDataSync = () => {
  const mutation = useMutation({
    mutationFn: async (username: string) => {
      const res = await api.username.sync({ username });
      return res.data;
    },
  });

  const performUsernameDataSync = async (username: string) => {
    if (!username) return;

    return await mutation.mutateAsync(username);
  };

  return {
    performUsernameDataSync,

    // state
    isSyncingUsernameData: mutation.isPending,
    isError: mutation.isError,
    error: mutation.error,
  };
};